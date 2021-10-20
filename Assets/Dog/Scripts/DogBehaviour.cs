using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public abstract class DogBehaviour
{

  protected GameManager GM { get; }
  protected DogController dc { get; }
  public class Movement
  {
    public float v { get; set; }
    public float theta { get; set; }

    public Movement(float v, float theta)
    {
      this.v = v;
      this.theta = theta;
    }
  }

  public DogBehaviour(GameManager GM, DogController dc)
  {
    this.GM = GM;
    this.dc = dc;
  }

  public abstract DogBehaviour.Movement GetDesiredMovement();

  public List<SheepController> getSheepList()
  {
    // get only live sheep
    var sheep = GM.sheepList.Where(sc => !sc.dead);
    if (GM.DogsParametersStrombom.local)
    { // localized perception
      if (GM.DogsParametersStrombom.occlusion)
        sheep = sheep.Where(sc => IsVisible(sc, GM.DogsParametersStrombom.blindAngle));

#if false // experimental: exlude visually occludded sheep
      sheepList.Sort (new ByDistanceFrom (transform.position));
      List<int> hidden = new List<int> ();
      for (int i = 0; i < sheepList.Count; i++) {
        Vector3 toSc = sheepList[i].transform.position - transform.position;
        float dcos = Mathf.Atan2 (.5f * sheepList[i].transform.localScale.x, toSc.magnitude);
        float cos = Mathf.Acos (Vector3.Dot (transform.forward, toSc.normalized));
        for (int j = i + 1; j < sheepList.Count; j++) {
          if (hidden.Exists (k => k == sheepList[j].id)) continue; // skip those already hidden

          Vector3 toSc2 = sheepList[j].transform.position - transform.position;
          float dcos2 = Mathf.Atan2 (.5f * sheepList[j].transform.localScale.x, toSc2.magnitude);
          float cos2 = Mathf.Acos (Vector3.Dot (transform.forward, toSc2.normalized));

          float visible = Mathf.Max (0, Mathf.Min (cos - dcos, cos2 + dcos2) - (cos2 - dcos2));
          visible += Mathf.Max (0, (cos2 + dcos2) - Mathf.Max (cos2 - dcos2, cos + dcos));
          if (visible / dcos2 <= 1) hidden.Add (sheepList[j].id);
        }
      }
      for (int i = 0; i < sheepList.Count; i++) {
        if (!hidden.Exists (j => j == sheepList[i].id))
          Debug.DrawRay (transform.position, sheepList[i].transform.position - transform.position, Color.white);
      }

      sheepList = sheepList.Where (sheep => !hidden.Exists (id => id == sheep.id)).ToList ();
#endif
#if true // take into account cognitive limits track max ns nearest neighbours
      sheep = sheep
        .OrderBy(d => d, new ByDistanceFrom(dc.transform.position))
        .Take(GM.DogsParametersStrombom.ns);
#endif
    }
    return sheep.ToList();
  }

  private bool IsVisible(SheepController sc, float blindAngle)
  {
#if true // experimental: test occlusion
    Vector3 Cm = dc.GetComponent<Rigidbody>().worldCenterOfMass;
    Vector3 toCm = sc.GetComponent<Rigidbody>().worldCenterOfMass - Cm;
    bool hit = Physics.Raycast(Cm + .5f * toCm.normalized, toCm.normalized, toCm.magnitude - 1f);
    if (hit) return false;
#endif
    if (GM.DogsParametersOther.dynamicBlindAngle)
    {
      blindAngle = blindAngle + (GM.DogsParametersOther.runningBlindAngle - blindAngle) * (dc.v / GM.dogRunningSpeed);
    }
    Vector3 toSc = sc.transform.position - dc.transform.position;
    float cos = Vector3.Dot(dc.transform.forward, toSc.normalized);
    return cos > Mathf.Cos((180f - blindAngle / 2f) * Mathf.Deg2Rad);
  }

}