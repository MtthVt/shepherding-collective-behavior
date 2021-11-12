using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class DogBehaviourSimpleDoge : DogBehaviour {

  public DogBehaviourSimpleDoge (GameManager GM, DogController dc) : base (GM, dc) { }
  public override Movement GetDesiredMovement () {

    /* behaviour logic */
    var desiredV = dc.v;
    var desiredTheta = dc.theta;

    var sheep = getSheepList ();

    // if no sheep in vision continue walking and rotate
    if (sheep.Count == 0) {
      desiredV = GM.dogWalkingSpeed;
      desiredTheta = ((dc.theta + 180 + 10) % 360) - 180;
      return new Movement (desiredV, desiredTheta);
    }

    Color dogColor = new Color ();

    float rdd = 0;
    if (GM.StrombomSheep) { rdd = GM.SheepParametersStrombom.r_sS; } else { rdd = GM.SheepParametersGinelli.r_sS; }

    Vector3 repulsionVector = new Vector3 (0f, 0f, 0f);

    BarnController barn = GameObject.FindObjectOfType<BarnController> ();
    SheepController chasedSheep = null;

    List<DogController> otherDogs = new List<DogController> (GM.dogList).Where (d => d != dc).ToList ();
    DogController dog = otherDogs.ElementAt (0);
    float mojaRazdalja = (barn.transform.position - dc.transform.position).magnitude;
    float razdalja = (barn.transform.position - dog.transform.position).magnitude;

    if ((dc.transform.position - dog.transform.position).magnitude < rdd) {
      repulsionVector = (dc.transform.position - dog.transform.position);
      repulsionVector /= repulsionVector.magnitude;
      repulsionVector.x = repulsionVector.magnitude * rdd;
      repulsionVector.z = 0;

      if (Vector3.Dot (dog.transform.position - dc.transform.position, repulsionVector) > 0) {
        repulsionVector = -repulsionVector * 3 / 4;
      }
    }

    if (mojaRazdalja > razdalja && repulsionVector.magnitude == 0) // dog focusing on closest sheep
    {
      sheep.Sort (new ByDistanceFrom (dc.transform.position));
      chasedSheep = sheep[0];
      dogColor = new Color (1f, 1f, 1f);

      // obkrozi obmocje izogibanja pasom
      Debug.DrawCircle (dc.transform.position, rdd, new Color (0f, 1f, 1f, 1f));
      // narisi vektor odboja
      Debug.DrawLine (dc.transform.position, dc.transform.position + repulsionVector);

    } else // dogs focusing on sheep furthest from barn
    {

      sheep.Sort (new ByDistanceFrom (dc.transform.position));
      sheep = sheep.GetRange (0, Mathf.Min (7, sheep.Count));
      sheep.Sort (new ByDistanceFrom (barn.transform.position));

      chasedSheep = sheep[sheep.Count - 1];
      dogColor = new Color (1f, 1f, 0f);
    }

    Vector3 Pc = chasedSheep.transform.position + (chasedSheep.transform.position - barn.transform.position).normalized * (rdd - 4);
    Pc += repulsionVector;

    // obkrozi zasledovano ovco
    Debug.DrawCircle (chasedSheep.transform.position, 1f, dogColor);
    // obkrozi zeljen polozaj psa
    Debug.DrawCircle (Pc, 1f, dogColor);

    Vector3 desiredPos = Pc - dc.transform.position;
    desiredTheta = (Mathf.Atan2 (desiredPos.z, desiredPos.x)) * Mathf.Rad2Deg;

    // razdalja do cilja
    float closeEnoughToWalk = 2.0f;
    float onDesiredPosition = 0.5f;
    float distanceToDesired = (Pc - dc.transform.position).magnitude;

    if (distanceToDesired < onDesiredPosition) desiredV = 0.0f;
    else if (distanceToDesired < closeEnoughToWalk) desiredV = GM.dogWalkingSpeed;
    else desiredV = GM.dogRunningSpeed;

    Movement desiredMovement = new Movement (desiredV, desiredTheta);
    return desiredMovement;
  }
}