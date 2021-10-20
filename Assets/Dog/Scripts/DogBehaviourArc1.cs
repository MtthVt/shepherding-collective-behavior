using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class DogBehaviourArc1 : DogBehaviour
{

  public DogBehaviourArc1(GameManager GM, DogController dc) : base(GM, dc) { }
  public override DogBehaviour.Movement GetDesiredMovement()
  {
    float timestep;
    if (GM.useFixedTimestep)
    {
      timestep = GM.fixedTimestep;
    }
    else
    {
      timestep = Time.deltaTime;
    }
    // desired heading in vector form
    Vector3 desiredThetaVector = new Vector3();
    // noise
    float eps = 0f;

    /* behaviour logic */
    var desiredV = dc.v;
    var desiredTheta = dc.theta;

    var sheep = getSheepList();

    if (sheep.Count > 0)
    {
      // compute CM of sheep
      Vector3 CM = new Vector3();
      foreach (SheepController sc in sheep)
        CM += sc.transform.position;
      if (sheep.Count > 0)
        CM /= (float)sheep.Count;

      // check if dog is closer to CM than average sheep, if true the herd is split
      /*
      float totalDistFromCM = 0;
      foreach (SheepController sc in sheep)
        totalDistFromCM += (sc.transform.position - CM).magnitude;
      float avgDistFromCM = 0;
      if (sheep.Count > 0)
        avgDistFromCM = totalDistFromCM / (float)sheep.Count;
      float dogDistFromCM = (dc.transform.position - CM).magnitude;
      if (avgDistFromCM > dogDistFromCM) // dog is between two or more herds => ignore one side
        sheep = sheep.Where(s => !IsBehindDog(s, CM, dc.transform.position)).ToList();
      */

      // draw CM
      Vector3 X = new Vector3(1, 0, 0);
      Vector3 Z = new Vector3(0, 0, 1);
      Color color = new Color(0f, 0f, 0f, 1f);
      Debug.DrawRay(CM - X, 2 * X, color);
      Debug.DrawRay(CM - Z, 2 * Z, color);

      // find distance of sheep that is nearest to the dog & distance of sheep furthest from CM
      float md_ds = Mathf.Infinity;
      SheepController sheep_c = null; // sheep furthest from CM
      //float Md_sC = 0;
      float Md_sC = 0.01f;

      float max_priority = -Mathf.Infinity;
      foreach (SheepController sc in sheep)
      {
        // distance from CM
        float d_sC = (CM - sc.transform.position).magnitude;

        // modification: prioritize sheep closer to dog

        Vector3 vectorToSheep = (sc.transform.position - dc.transform.position);
        float thetaToSheep = Mathf.Atan2(vectorToSheep.z, vectorToSheep.x) * Mathf.Rad2Deg;
        float angleDelta = ((thetaToSheep - dc.theta) + 180f) % 360f - 180f;

        float d_dog = (dc.transform.position - sc.transform.position).magnitude;
        //float priority = d_sC - Mathf.Sqrt(d_dog);
        //float priority = d_sC - d_dog;

        // prioritize the sheep currently in front of the dog

        // linear priority scaling based on angle, 1 in front ... 0.5 directly behind
        //float priority = d_sC * (1f - Mathf.Abs(angleDelta/180f) * 0.5f);
        // quadratic priority scaling based on angle, 1 in front ... 0 directly behind
        float priority = d_sC * Mathf.Pow(1f - Mathf.Abs(angleDelta / 180f) * 1f, 2);

        if (priority > max_priority)
        {
          max_priority = priority;
          Md_sC = d_sC;
          sheep_c = sc;
        }

        //if (d_sC > Md_sC)
        //if (d_sC > Md_sC && d_sC / Md_sC > 1.5) // try to reduce target swapping
        //{
        //  Md_sC = d_sC;
        //  sheep_c = sc;
        //}

        // distance from dog
        float d_ds = (sc.transform.position - dc.transform.position).magnitude;
        md_ds = Mathf.Min(md_ds, d_ds);
      }

      float ro = 0; // mean nnd
      if (GM.StrombomSheep)
        ro = GM.SheepParametersStrombom.r_a;
      else
        ro = GM.SheepParametersGinelli.r_0;

#if false // aproximate interaction distance through nearest neigbour distance
      foreach (SheepController sheep in sheepList) {
        float nn = Mathf.Infinity;
        foreach (SheepController sc in sheepList) {
          if (sc.id == sheep.id) continue;
          nn = Mathf.Min (nn, (sheep.transform.position - sc.transform.position).magnitude);
        }
        ro += nn;
      }
      ro /= sheepList.Count;
#endif

      float r_s = GM.DogsParametersStrombom.r_s * ro; // compute true stopping distance
      float r_w = GM.DogsParametersStrombom.r_w * ro; // compute true walking distance
      float r_r = GM.DogsParametersStrombom.r_r * ro; // compute true running distance

      if (GM.DogsParametersOther.modifiedRunningDistance)
      {
        // if too close to any sheep stop and wait
        if (md_ds < r_s)
        {
          dc.dogState = Enums.DogState.idle;
          desiredV = .0f;
        }
        // if close to any sheep start walking
        else if (md_ds < 6f)
        {
          dc.dogState = Enums.DogState.walking;
          desiredV = GM.dogWalkingSpeed;
        }
        else
        {
          // default run in current direction
          dc.dogState = Enums.DogState.running;
          desiredV = GM.dogRunningSpeed;
        }
      }
      else
      {
        // if too close to any sheep stop and wait
        if (md_ds < r_s)
        {
          dc.dogState = Enums.DogState.idle;
          desiredV = .0f;
        }
        // if close to any sheep start walking
        else if (md_ds < r_w)
        {
          dc.dogState = Enums.DogState.walking;
          desiredV = GM.dogWalkingSpeed;
        }
        else if (md_ds > r_r)
        {
          // default run in current direction
          dc.dogState = Enums.DogState.running;
          desiredV = GM.dogRunningSpeed;
        }
      }

      // aproximate radius of a circle
      float f_N = ro * Mathf.Pow(sheep.Count, 2f / 3f);
      // draw aprox herd size
      Debug.DrawCircle(CM, f_N, new Color(1f, 0f, 0f, 1f));

#if true
      foreach (SheepController sc in sheep)
        Debug.DrawCircle(sc.transform.position, .5f, new Color(1f, 0f, 0f, 1f));
#endif
      bool driving = false;
      // if all agents in a single compact group, collect them
      //if (Md_sC < f_N)
      // modified: if we have multiple dogs, one is always in driving mode
      if (Md_sC < f_N || (GM.dogList.Count() > 1 && dc.id == 0))
      {
        BarnController barn = GameObject.FindObjectOfType<BarnController>();

        // compute position so that the GCM is on a line between the dog and the target
        Vector3 Pd = CM + (CM - barn.transform.position).normalized * ro * Mathf.Sqrt(sheep.Count); // Mathf.Min(ro * Mathf.Sqrt(sheep.Count), Md_sC);
        desiredThetaVector = Pd - dc.transform.position;
        if (desiredThetaVector.magnitude > r_w)
          desiredV = GM.dogRunningSpeed;

        color = new Color(0f, 1f, 0f, 1f);
        Debug.DrawRay(Pd - X - Z, 2 * X, color);
        Debug.DrawRay(Pd + X - Z, 2 * Z, color);
        Debug.DrawRay(Pd + X + Z, -2 * X, color);
        Debug.DrawRay(Pd - X + Z, -2 * Z, color);

        driving = true;
      }
      else
      {
        // compute position so that the sheep most distant from the GCM is on a line between the dog and the GCM
        Vector3 Pc = sheep_c.transform.position + (sheep_c.transform.position - CM).normalized * ro;
        // move in an arc around the herd??
        desiredThetaVector = Pc - dc.transform.position;

        color = new Color(1f, .5f, 0f, 1f);
        Debug.DrawRay(Pc - X - Z, 2 * X, color);
        Debug.DrawRay(Pc + X - Z, 2 * Z, color);
        Debug.DrawRay(Pc + X + Z, -2 * X, color);
        Debug.DrawRay(Pc - X + Z, -2 * Z, color);

      }

      if (GM.DogsParametersOther.dogRepulsion && GM.dogList.Count() > 1)
      {
        float repulsionDistance = (dc.id + 3) * 5 / 3f;
        List<DogController> otherDogs = new List<DogController>(GM.dogList).Where(d => d != dc).ToList();
        Vector3 repulsionVector = new Vector3(0f, 0f, 0f);
        foreach (DogController d in otherDogs)
        {
          if ((dc.transform.position - d.transform.position).magnitude < repulsionDistance)
          {
            repulsionVector += (dc.transform.position - d.transform.position);
          }
        }
        desiredThetaVector += repulsionVector;
        Debug.DrawCircle(dc.transform.position, repulsionDistance, new Color(0f, 1f, 1f, 1f));
        Debug.DrawLine(dc.transform.position, dc.transform.position + repulsionVector);
      }

      // arc movement
      // direct line to sheep furthest from CM
      color = Color.cyan;
      if (driving)
      {
        Debug.DrawRay(dc.transform.position, desiredThetaVector, new Color(0f, 1f, 0f, 1f));
      }
      else
      {
        Debug.DrawRay(dc.transform.position, desiredThetaVector, new Color(1f, .5f, 0f, 1f));
      }
      // arc around CM
      Debug.DrawCircle(CM, (dc.transform.position - CM).magnitude, Color.blue, false);

      //Vector3 cmVector = dc.transform.position + (dc.transform.position - CM);
      Vector3 cmVector = CM - dc.transform.position;
      Debug.DrawRay(dc.transform.position, cmVector, Color.red);
      float cmTheta = (Mathf.Atan2(cmVector.z, cmVector.x) + eps) * Mathf.Rad2Deg;
      desiredTheta = (Mathf.Atan2(desiredThetaVector.z, desiredThetaVector.x) + eps) * Mathf.Rad2Deg;

      float delta = cmTheta - desiredTheta;
      delta = (delta + 180f) % 360f - 180f;

      if (Mathf.Abs(delta) < 90) // only use arc if furthest sheep is closer to CM than dog
      {
        float arcAngle = 85f; // maintain distance from CM
        // TODO include (ratio with repulsion) distance in equation?
        if (driving && desiredThetaVector.magnitude > cmVector.magnitude)
        {
          // driving position is on other side of the herd, go around
        }
        else
        {
          arcAngle = Mathf.Min(3 * Mathf.Abs(delta), arcAngle); // get closer if angle between furthest sheep and CM is small
        }

        // calculate new desired angle
        float arcTheta = 0;
        if (delta < 0) arcTheta = (cmTheta + arcAngle + 180f) % 360f - 180f;
        else arcTheta = (cmTheta - arcAngle + 180f) % 360f - 180f;
        float arcThetaRad = arcTheta * Mathf.Deg2Rad;

        Vector3 arcVector = (new Vector3(Mathf.Cos(arcThetaRad), 0, Mathf.Sin(arcThetaRad)) * 10);

        // correct angle to avoid fence
        float angleCorrectionStep = 10; // degrees
        angleCorrectionStep = (((desiredTheta - arcTheta + 180f) % 360f) - 180f) > 0 ? angleCorrectionStep : -angleCorrectionStep;

        RaycastHit hit;
        for (int i = 0; i < (180f / Mathf.Abs(angleCorrectionStep)); i++)
        {
          if (Physics.Raycast(dc.transform.position, arcVector, out hit, 10f))
          {
            //Debug.DrawRay(dc.transform.position, arcVector * hit.distance, Color.yellow);
            // close to fence, adjust angle
            arcTheta = arcTheta + angleCorrectionStep;
            arcThetaRad = arcTheta * Mathf.Deg2Rad;
            arcVector = (new Vector3(Mathf.Cos(arcThetaRad), 0, Mathf.Sin(arcThetaRad)) * 10);
          }
          else
          {
            Debug.DrawRay(dc.transform.position, arcVector, Color.white);
            desiredThetaVector = arcVector;
            break;
          }
        }

        // make dog always run when collecting sheep
        /*if (!driving)
        {
          dc.dogState = Enums.DogState.running;
          desiredV = GM.dogRunningSpeed;
        }*/

      }
    }
    else // no visible sheep
    {
      //dc.dogState = Enums.DogState.idle;
      //desiredV = .0f;
      // turn around after losing vision of sheep instead of standing still
      dc.dogState = Enums.DogState.walking;
      desiredV = GM.dogWalkingSpeed;
      desiredTheta = (desiredTheta - GM.dogMaxTurn * timestep + 180f) % 360f - 180f;
      return new Movement(desiredV, desiredTheta);
    }

    if (GM.DogsParametersStrombom.occlusion)
    {
      float blindAngle = GM.DogsParametersStrombom.blindAngle;
      if (GM.DogsParametersOther.dynamicBlindAngle)
      {
        blindAngle = blindAngle + (GM.DogsParametersOther.runningBlindAngle - blindAngle) * (dc.v / GM.dogRunningSpeed);
      }
      float blindAngle1 = ((dc.theta + blindAngle / 2 + 360f) % 360f - 180f) * Mathf.Deg2Rad;
      Vector3 blindVector1 = new Vector3(Mathf.Cos(blindAngle1), 0, Mathf.Sin(blindAngle1));
      Debug.DrawRay(dc.transform.position, blindVector1 * 100f, new Color(0.8f, 0.8f, 0.8f, 0.2f));
      float blindAngle2 = ((dc.theta - blindAngle / 2 + 360f) % 360f - 180f) * Mathf.Deg2Rad;
      Vector3 blindVector2 = new Vector3(Mathf.Cos(blindAngle2), 0, Mathf.Sin(blindAngle2));
      Debug.DrawRay(dc.transform.position, blindVector2 * 100f, new Color(0.8f, 0.8f, 0.8f, 0.2f));
    }

    // extract desired heading
    desiredTheta = (Mathf.Atan2(desiredThetaVector.z, desiredThetaVector.x) + eps) * Mathf.Rad2Deg;
    /* end of behaviour logic */

    Movement desiredMovement = new Movement(desiredV, desiredTheta);
    return desiredMovement;
  }

  private bool IsBehindDog(SheepController sc, Vector3 cm, Vector3 dog)
  {
    float d_dog = (sc.transform.position - dog).magnitude;
    float d_cm = (sc.transform.position - cm).magnitude;
    float d_dog_cm = (dog - cm).magnitude;
    return Mathf.Pow(d_dog, 2) + Mathf.Pow(d_dog_cm, 2) < Mathf.Pow(d_cm, 2);
  }
}