using UnityEngine;
using System.Collections.Generic;
using System.Linq;


public class DogController : MonoBehaviour
{
  public int id;

  // state
  [HideInInspector]
  public Enums.DogState dogState;
  public Enums.DogState previousDogState;

  // Game settings
  [HideInInspector]
  public int controls;

  // GameManager
  private GameManager GM;

  // Dogs animator controller
  public Animator anim;

  // Movement parameters
  private float desiredV = .0f;
  public float v { get; private set; }

  public float theta { get; private set; }
  private float desiredTheta = .0f;

  // animation bools
  private bool turningLeft = false;
  private bool turningRight = false;

  private DogBehaviour dogBehaviour;

  // Use this for initialization
  void Start()
  {
    // GameManager
    GM = FindObjectOfType<GameManager>();

    // init speed
    desiredV = 5.0f;
    v = desiredV;

    // heading is current heading
    desiredTheta = Mathf.Atan2(transform.forward.z, transform.forward.y) * Mathf.Rad2Deg;
    theta = desiredTheta;
    transform.forward = new Vector3(Mathf.Cos(theta * Mathf.Deg2Rad), .0f, Mathf.Sin(theta * Mathf.Deg2Rad)).normalized;

    // init chosen behaviour script
    if (GM.DogBehaviour == Enums.DogBehaviour.strombom) {
      dogBehaviour = new DogBehaviourStrombom(GM, this);
    } else if (GM.DogBehaviour == Enums.DogBehaviour.simple_doge) {
      dogBehaviour = new DogBehaviourSimpleDoge(GM, this);
    } else if (GM.DogBehaviour == Enums.DogBehaviour.arc_v1) {
      dogBehaviour = new DogBehaviourArc1(GM, this);
    } else if (GM.DogBehaviour == Enums.DogBehaviour.arc_v2) {
      dogBehaviour = new DogBehaviourArc2(GM, this);
    }
  }

  // Update is called once per frame
  void Update()
  {
    if (dogBehaviour != null) {
      DogBehaviour.Movement desiredMovement = dogBehaviour.GetDesiredMovement();
      desiredV = desiredMovement.v;
      desiredTheta = desiredMovement.theta;
    } else {
      Controls();
    }

    if (GM.useFixedTimestep) {
      DogMovement();
    }
  }

  void FixedUpdate()
  {
    if (!GM.useFixedTimestep) {
      DogMovement();
    }
  }

  void Controls()
  {
    float timestep;
    if (GM.useFixedTimestep) {
      timestep = GM.fixedTimestep;
    } else {
      timestep = Time.deltaTime;
    }
    if (Input.GetKey(KeyCode.W))
    {
      desiredV += GM.dogMaxSpeedChange * timestep;
    }
    else if (Input.GetKey(KeyCode.S))
    {
      desiredV -= GM.dogMaxSpeedChange * timestep;
    }
    else
    {
      desiredV = Mathf.MoveTowards(desiredV, 0, GM.dogMaxSpeedChange / 10f);
    }

    if (Input.GetKey(KeyCode.A))
    {
      desiredTheta += GM.dogMaxTurn * timestep;
    }
    else if (Input.GetKey(KeyCode.D))
    {
      desiredTheta -= GM.dogMaxTurn * timestep;
    }
    else
    {
      desiredTheta = theta + Mathf.MoveTowardsAngle((desiredTheta - theta), 0, GM.dogMaxTurn / 10f);
      // ensure angle remains in [-180,180)
      desiredTheta = (desiredTheta + 180f) % 360f - 180f;
    }
  }

  void DogMovement()
  {
    float timestep;
    if (GM.useFixedTimestep) {
      timestep = GM.fixedTimestep;
    } else {
      timestep = Time.deltaTime;
    }
    // compute angular change based on max angular velocity and desiredTheta
    theta = Mathf.MoveTowardsAngle(theta, desiredTheta, GM.dogMaxTurn * timestep);
    // ensure angle remains in [-180,180)
    theta = (theta + 180f) % 360f - 180f;
    // compute longitudinal velocity change based on max longitudinal acceleration and desiredV
    v = Mathf.MoveTowards(v, desiredV, GM.dogMaxSpeedChange * timestep);
    // ensure speed remains in [minSpeed, maxSpeed]
    v = Mathf.Clamp(v, GM.dogMinSpeed, GM.dogMaxSpeed);

    // compute new forward direction
    Vector3 newForward = new Vector3(Mathf.Cos(theta * Mathf.Deg2Rad), .0f, Mathf.Sin(theta * Mathf.Deg2Rad)).normalized;
    // update position
    Vector3 newPosition = transform.position + (timestep * v * newForward);
    // force ground, to revert coliders making sheep fly
    newPosition.y = 0f;

    transform.position = newPosition;
    transform.forward = newForward;

    // draw dogRepulsion radius
    if (GM.StrombomSheep)
    {
      Debug.DrawCircle(transform.position, GM.SheepParametersStrombom.r_s, new Color(1f, 1f, 0f, .5f), true);
      Debug.DrawCircle(transform.position, GM.SheepParametersStrombom.r_sS, new Color(1f, 1f, 0f, 1f));
    }
    else
    {
      Debug.DrawCircle(transform.position, GM.SheepParametersGinelli.r_s, new Color(1f, 1f, 0f, .5f), true);
      Debug.DrawCircle(transform.position, GM.SheepParametersGinelli.r_sS, new Color(1f, 1f, 0f, 1f));
    }

    if (v == .0f)
    {
      turningLeft = false;
      turningRight = false;
    }
    else
    {
      turningLeft = theta > 0;
      turningRight = theta < 0;
    }

    // Animation Controller
    anim.SetBool("IsRunning", v > 6);
    anim.SetBool("Reverse", v < 0);
    anim.SetBool("IsWalking", (v > 0 && v <= 6) ||
                               turningLeft ||
                               turningRight);

  }
}