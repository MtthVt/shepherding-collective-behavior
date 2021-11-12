using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using csDelaunay;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using System.IO;

public class GameManager : MonoBehaviour
{
  // GUI
  [Header("GUI")]

  public Text countdownText;
  public Text scoreText;

  // timer; time available to drive all sheep into the barn 
  private float gameTimer = 150.0f;

  // game settings
  // hardcoded spawn boundaries
  private float minSpawnX = -50.0f;
  private float maxSpawnX = 50.0f;
  private float maxSpawnZ = 30.0f;
  private float minSpawnZ = -55.0f;

  // skybox
  [Header("Skybox")]
  public Material[] skyboxes;

  // fences
  [Header("Fence")]
  public GameObject fence;
  [Header("Barn doors")]
  public GameObject barnDoors;
  [HideInInspector]
  public Collider[] fenceColliders;

  // sheep
  [Header("Sheep")]
  public GameObject sheepPrefab;
  private float minSheepSize = .7f;  // random size
  public int nOfSheep = 100;

  [HideInInspector]
  public int sheepCount; // sheep remaining on field
  // list of sheep
  public List<SheepController> sheepList = new List<SheepController>();

  public float sheepMaxSpeedChange = .15f / .02f; // in deg per second
  public float sheepMaxTurn = 4.5f / .02f; // in deg per second

  public float sheepWalkingSpeed = 1.5f; // Strombom original 0.15f
  public float sheepRunningSpeed = 7.5f; // Strombom original 1.5f

  [System.Serializable]
  public class SPG
  {
    public float r_0 = 1.0f; // interaction distance
    public float r_e = 1.0f; // equilibrium distance for atraction/repulsion force
    public float eta = 0.13f; // noise - original 0.13f
    public float beta = 3.0f; // cohesion factor - original 0.8f
    public float alpha = 15.0f; // allelometric parameters
    public float delta = 4.0f; // allelometric parameters
    public float tau_iw = 35f; // transition rate, idle to walking - original 35
    public float tau_wi = 8f; // transition rate, walking to idle - original 8
    public float tau_iwr; // transition rate, idle, walking to running = sheepCount
    public float tau_ri; // transition rate, running to idle = sheepCount
    public float d_R = 31.6f; // lenghtscale for transitions to running
    public float d_S = 6.3f; // lenghtscale for transitions to idle

    public float rho_s = 3f; // shephard repulsion factor
    public float r_s = 22.5f; // shephard detection distance
    public float r_sS = 22.5f / 2f; // shephard strong repulsion distance

    public float rho_f = 2f; // fences repulsion factor
    public float r_f = 3f; // fence detection distance

    //public int n = 20; // cognitive limits
    public bool occlusion = false; // bahaviour based on local info only, i.e. visible non occluded Sheep
    public float blindAngle = 0f;
  }
  public SPG SheepParametersGinelli;
  // public int ns = 8; // experimental: interact with maximally ns neighbours (cognitive limit)

  public bool StrombomSheep = true; // use Ginelli et al.'s model
  [System.Serializable]
  public class SPS
  { // distance are half of what is given in the paper as it seems they used sheeps of size 2, ours are of size 1 (diameter of circle)
    public float r_a = 1f; // agent to agent interaction distance - original 2f
    public float rho_a = 2f; // relative strentgth of repulsion from other agents
    public float rho_s = 1f; // relative strength of repulsion from the shepherd
    public float c = 1.05f; // relative strength of attraction to the n nearest neighbours
    public float h = 0.5f; // relative strength of proceeding in the previous direction
    public float e = 0.1f; // relative strength of angular noise - original 0.3f

    public float r_s = 22.5f; // shepherd detection distance - original 45f
    public float r_sS = 22.5f / 2f; // shepherd detection distance - strong repulsion (running otherwise walking)

    public float rho_f = 2f; // relative strength of repulsion from fences
    public float r_f = 3f; // fence detection distance

    public int n = 20; // > min(0.53sheepCount, 3log(sheepCount))
    public bool occlusion = false; // bahaviour based on local info only, i.e. visible non occluded Sheep
    public float blindAngle = 0f;
  }
  public SPS SheepParametersStrombom;
  [Header("Dogs")]
  // list of dogs
  public List<DogController> dogList = new List<DogController>();

  public float dogMaxSpeedChange = 62f;
  public float dogMaxTurn = 360f; // in deg per second

  public float dogMinSpeed = -3f;
  public float dogWalkingSpeed = 1.5f;
  public float dogRunningSpeed = 7.5f; // Strombom original 1.5f
  public float dogMaxSpeed = 10f;

  // public bool StrombomDogs = false; // use Strömbom et al.'s shepherd
  // public bool StrombomDogsPlus = false; // use modified Strömbom et al.'s shepherd



  [System.Serializable]
  public class DPS
  {
    public float r_s = 3;// length at which dog stops 3ro
    public float r_w = 9;// length at which dog starts walking
    public float r_r = 18;// length at which dog starts running

    public bool local = false; // use local model
    public int ns = 20; // size of local subgroups
    public bool occlusion = false; // bahaviour based on local info only, i.e. visible non occluded Sheep
    public float blindAngle = 60f; // in degrees

    

  }
  public DPS DogsParametersStrombom;

  [System.Serializable]

  public class DPO
  {
    public float runningBlindAngle = 180f;
    public bool dynamicBlindAngle = false; // increase dog's blind angle while running
    public bool randomizeDogPositions = false;

    public bool dogRepulsion = true;

    public float rho_f = .5f; // relative strength of repulsion from fences
    public float r_f = 10f; // fence detection distance
    public bool modifiedRunningDistance = false;
  }

  public DPO DogsParametersOther;

  public Enums.DogBehaviour DogBehaviour;


  [Header("Simulation")]
  public bool disableRendering = false;
  public float timeScale = 1.0f;
  public bool useFixedTimestep = false; // advance physics by fixed time delta each update step
  public float fixedTimestep = 0.02f;
  public bool showDogPaths = false;

  private static string simulationName = ""; // used for log folder name, autogenerated in Start
  private static int simulationNumber = 1;
  public int simulationCount = 1; // amount of simulations to run

  // update frequency
  private float neighboursUpdateInterval = 0 * .5f;
  private float neighboursTimer;

  // distances between each pair of sheep
  public float[,] sheepDistances;

  [HideInInspector]
  public float maxFrameTime = 0f;
  [HideInInspector]
  public float avgFrameTime = 0f;
  [HideInInspector]
  public bool simulationRunning = false;



  void Start()
  {
    if (simulationName == "") {
      simulationName = string.Format("{0}_{1}", System.DateTime.Now.ToString("s"), DogBehaviour);
    }
    if (disableRendering) {
      GameObject.Find("Overview Camera").GetComponent<Camera>().cullingMask = 0;
    }
    Time.timeScale = timeScale;
    // spawn
    SpawnSheep();

    if (showDogPaths) {
      foreach (DogController dc in dogList) {
        TrailRenderer tr = dc.gameObject.AddComponent(typeof(TrailRenderer)) as TrailRenderer;
        tr.startWidth = 0.2f;
        tr.endWidth = 0.2f;
        tr.time = 500f;
      }
    }

    // fences colliders
    fenceColliders = fence.GetComponentsInChildren<Collider>().Concat(barnDoors.GetComponentsInChildren<Collider>()).ToArray();

    // timers
    neighboursTimer = neighboursUpdateInterval;

    sheepDistances = new float[nOfSheep, nOfSheep];
    simulationRunning = true;
  }

  void SpawnSheep()
  {
    // number of sheep
    sheepCount = nOfSheep;
    SheepParametersGinelli.tau_iwr = nOfSheep;
    SheepParametersGinelli.tau_ri = nOfSheep;

    // cleanup
    int i = 0;
    sheepList.Clear();
    GameObject[] sheep = GameObject.FindGameObjectsWithTag("Sheep");
    for (i = 0; i < sheep.Length; i++)
      Destroy(sheep[i]);

    // spawn
    Vector3 position;
    SheepController newSheep;

    i = 0;
    while (i < sheepCount)
    {
      position = new Vector3(Random.Range(minSpawnX, maxSpawnX), .0f, Random.Range(minSpawnZ, maxSpawnZ));

      if (Physics.CheckSphere(position, 1.0f, 1 << 8)) // check if random position inside SheepSpawn areas
      {
        float randomFloat = Random.Range(minSheepSize, 1.0f);
        newSheep = ((GameObject)Instantiate(sheepPrefab, position, Quaternion.identity)).GetComponent<SheepController>();
        newSheep.id = i;
        newSheep.transform.localScale = new Vector3(randomFloat, randomFloat, randomFloat);
        sheepList.Add(newSheep);
        i++;
      }
    }
    // remove spawn areas
    foreach (GameObject area in GameObject.FindGameObjectsWithTag("SpawnArea"))
      GameObject.Destroy(area);

    // find dogs
    dogList = new List<DogController>(FindObjectsOfType<DogController>());

    if(DogsParametersOther.randomizeDogPositions) {
      foreach (DogController dc in dogList) {
        position = new Vector3(Random.Range(-41, 47), 0f, Random.Range(-51f, 15f));
        dc.transform.position = position;
        dc.transform.Rotate(0, Random.Range(0f, 360f), 0);
      }
    }
    
  }

  public void Quit()
  {
#if UNITY_EDITOR
    UnityEditor.EditorApplication.isPlaying = false;
#else
      Application.Quit();
#endif
  }

  void Update()
  {
    float timestep;
    if (useFixedTimestep) {
      timestep = fixedTimestep;
    } else {
      timestep = Time.deltaTime;
    }
    // pause menu
    if (Input.GetKeyDown(KeyCode.Escape))
    {
      Quit();
    }

    // update
    UpdateNeighbours();

    // cache positions of ship to reduce expensive Transform.position calls
    foreach (SheepController sc in sheepList)
      sc.position = sc.transform.position;

    // precalculate distances between sheep
    /*
    for (int i = 0; i < sheepCount - 1; i++)
    {
      for (int j = i + 1; j < sheepCount; j++)
      {
        SheepController sc = sheepList[i];
        SheepController sc2 = sheepList[j];
        sheepDistances[sc.id, sc2.id] = (sc.position - sc2.position).sqrMagnitude;
        sheepDistances[sc2.id, sc.id] = sheepDistances[sc.id, sc2.id];
      }
    }
    */

    // game timer
    gameTimer -= timestep;

    if (gameTimer > 10.0f)
      countdownText.text = ((int)Mathf.Ceil(gameTimer)).ToString();
    else
    {
      gameTimer = Mathf.Max(gameTimer, .0f);
      countdownText.text = ((float)System.Math.Round(gameTimer, 2)).ToString();
    }

    scoreText.text = sheepCount.ToString();

    if (gameTimer == 0 || sheepCount <= 0)
    {

      
      saveData();
      simulationNumber++;
      if (simulationNumber > simulationCount) Quit();
      SceneManager.LoadScene(SceneManager.GetActiveScene().name);
    }
  }

  private void saveData() {
    int n = simulationNumber;
    int totalSheep = nOfSheep;
    int sheepHerded = nOfSheep - sheepCount;
    float timeUsed = 150.0f - gameTimer;

    string parametersFile = Path.Combine(simulationName, "parameters.json");
    string resultsFile = Path.Combine(simulationName, "results.csv");

    if(n == 1) {
      Directory.CreateDirectory(simulationName);
      // save parameters
      string parameters = JsonUtility.ToJson(this, true);
      File.WriteAllText(parametersFile, parameters);
      // write csv header
      File.WriteAllText(resultsFile, "id,total_sheep,sheep_herded,time_used\n");
    }
    File.AppendAllText(resultsFile, string.Format("{0},{1},{2},{3}\n", n, totalSheep, sheepHerded, timeUsed));

#if false // save screenshot of end state after unsuccesful simulations
    // not working on linux build
    if(sheepHerded < totalSheep) {
      if(disableRendering) {
          GameObject.Find("Overview Camera").GetComponent<Camera>().cullingMask = -1;
        }
        ScreenCapture.CaptureScreenshot(Path.Combine(simulationName, string.Format("{0}.png", n)));
    }
#endif
  }

  private void UpdateNeighbours()
  {
    float timestep;
    if (useFixedTimestep) {
      timestep = fixedTimestep;
    } else {
      timestep = Time.deltaTime;
    }
    neighboursTimer -= timestep;
    if (neighboursTimer < 0)
    {
      neighboursTimer = neighboursUpdateInterval;

      if (!StrombomSheep)
      {
        // comment out to change via inspector
        SheepParametersGinelli.tau_iwr = sheepCount;
        SheepParametersGinelli.tau_ri = sheepCount;


        // todo test with occlusion, cognitive limit and both dogs and sheep in same perception then filter out and merge from T+M dogs 
        List<Vector2f> sheepL = new List<Vector2f>();
        List<Vector2f> dogsL = new List<Vector2f>();

        // recast position data for cache coherence
        foreach (SheepController sc in sheepList)
          if (!sc.dead) sheepL.Add(new Vector2f(sc.transform.position.x, sc.transform.position.z, sc.id));
        foreach (DogController dc in dogList)
          dogsL.Add(new Vector2f(dc.transform.position.x, dc.transform.position.z, dc.id)); // GM.nOfSheep * 10 + 

        // topologic neighbours - first shell of voronoi neighbours
        Rectf bounds = new Rectf(-60.0f, -65.0f, 120.0f, 110.0f);
        Voronoi voronoi = new Voronoi(sheepL, bounds);
#if false
        Debug.DrawLine(new Vector3(bounds.x, 0, bounds.y), new Vector3(bounds.x + bounds.width, 0, bounds.y));
        Debug.DrawLine(new Vector3(bounds.x + bounds.width, 0, bounds.y), new Vector3(bounds.x + bounds.width, 0, bounds.y + bounds.height));
        Debug.DrawLine(new Vector3(bounds.x + bounds.width, 0, bounds.y + bounds.height), new Vector3(bounds.x, 0, bounds.y + bounds.height));
        Debug.DrawLine(new Vector3(bounds.x, 0, bounds.y + bounds.height), new Vector3(bounds.x, 0, bounds.y));
        foreach (LineSegment ls in voronoi.VoronoiDiagram())
          Debug.DrawLine(new Vector3(ls.p0.x, 0f, ls.p0.y), new Vector3(ls.p1.x, 0f, ls.p1.y), Color.black);
#endif

        foreach (SheepController sc in sheepList)
        {
          Vector2f position = new Vector2f(sc.transform.position.x, sc.transform.position.z, sc.id);

          // get metric dogs neighbours
          List<DogController> dogNeighbours = new List<DogController>();
          var dogs = dogsL
                        .Where(point => point.DistanceSquare(position) < SheepParametersGinelli.r_s * SheepParametersGinelli.r_s)
                        .OrderBy(d => d, new ByDistanceFrom(position));
          // dogs.GetRange(0, Mathf.Min(SheepParametersGinelli.n, dogs.Count)); // cognitive limits
          foreach (Vector2f dn in dogs)
            dogNeighbours.Add(dogList[dn.id]);

          // get topologic sheep neighbours
          List<SheepController> topologicNeighbours = new List<SheepController>();
          foreach (Vector2f snt in voronoi.NeighborSitesForSite(position))
            topologicNeighbours.Add(sheepList[snt.id]);

          // get metric sheep neighbours
          List<SheepController> metricNeighbours = new List<SheepController>();
          var sheep = sheepL
                        .Where(point => point.id != sc.id && point.DistanceSquare(position) < SheepParametersGinelli.r_0 * SheepParametersGinelli.r_0)
                        .OrderBy(d => d, new ByDistanceFrom(position));
          // sheep.GetRange(0, Mathf.Min(SheepParametersGinelli.n, sheep.Count)); // cognitive limits
          foreach (Vector2f snm in sheep)
            metricNeighbours.Add(sheepList[snm.id]);

          // perform updates by swap to prevent empty lists due to asynchronous execution
          sc.dogNeighbours = dogNeighbours;
          sc.topologicNeighbours = topologicNeighbours;
          sc.metricNeighbours = metricNeighbours;

          // ignore topologic neighbours further than the closest dog
          //          float l_i = sc.l_i;
#if false
          if (dogs.Count > 0)
          {
            float ndc = (dogList[dogs[0].id].transform.position - sc.transform.position).magnitude;
            topologicNeighbours =
              topologicNeighbours.Where(snt => (snt.transform.position - sc.transform.position).magnitude < ndc).ToList(); //!(snt.sheepState == Enums.SheepState.idle && snt.previousSheepState == Enums.SheepState.running)
            sc.topologicNeighbours = topologicNeighbours;
          }
#endif
          // TODO: metricNeighbours.Where(n => !n.dead && n.sheepState == Enums.SheepState.idle).Count();
          sc.n_idle = .0f;
          sc.n_walking = .0f;
          sc.m_idle = .0f;
          sc.m_toidle = .0f;
          sc.m_running = .0f;
          sc.l_i = .0f;
          // ignore dead/barned sheep
          foreach (SheepController neighbour in sc.metricNeighbours)
          {
            if (neighbour.dead) continue;
            // state counter
            switch (neighbour.sheepState)
            {
              case Enums.SheepState.idle:
                sc.n_idle++;
                break;
              case Enums.SheepState.walking:
                sc.n_walking++;
                break;
            }
          }

          // ignore dead/barned sheep
          foreach (SheepController neighbour in sc.topologicNeighbours)
          {
            if (neighbour.dead) continue;
            // state count
            switch (neighbour.sheepState)
            {
              case Enums.SheepState.idle:
                if (neighbour.previousSheepState == Enums.SheepState.running)
                  sc.m_toidle++;
                //sc.m_toidle += 1f - Mathf.Max(0, (neighbour.transform.position - sc.transform.position).magnitude / l_i); // decrease influence of idle sheep with their distance
                sc.m_idle++;
                break;
              case Enums.SheepState.running:
                sc.m_running++;
                // sc.m_running += 1f - Mathf.Max(0, (neighbour.transform.position - sc.transform.position).magnitude / l_i); // decrease influence of running sheep with their distance
                break;
            }

            // mean distance to topologic neighbours
            sc.l_i += (sc.transform.position - neighbour.transform.position).sqrMagnitude;
          }

          // divide with number of topologic neighbours
          if (sc.topologicNeighbours.Count > 0)
            sc.l_i /= sc.topologicNeighbours.Count;
          sc.l_i = Mathf.Sqrt(sc.l_i);
        }
      }
    }
  }
}