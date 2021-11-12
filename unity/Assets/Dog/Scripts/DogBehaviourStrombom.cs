using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using System;

public class DogBehaviourStrombom : DogBehaviour
{

  public DogBehaviourStrombom(GameManager GM, DogController dc) : base(GM, dc) { }
  public override Movement GetDesiredMovement()
  {
    // desired heading in vector form
    Vector3 desiredThetaVector = new Vector3();
    // noise
    float eps = 0f;

    /* behaviour logic */
    var desiredV = dc.v;
    var desiredTheta = dc.theta;

    var sheep = getSheepList();

    if (sheep.Count() > 0)
    {
      // compute CM of sheep
      Vector3 CM = new Vector3();
      foreach (SheepController sc in sheep)
        CM += sc.transform.position;
      if (sheep.Count() > 0)
        CM /= (float)sheep.Count();

      // draw CM
      Vector3 X = new Vector3(1, 0, 0);
      Vector3 Z = new Vector3(0, 0, 1);
      Color color = new Color(0f, 0f, 0f, 1f);
      Debug.DrawRay(CM - X, 2 * X, color);
      Debug.DrawRay(CM - Z, 2 * Z, color);

      // find distance of sheep that is nearest to the dog & distance of sheep furthest from CM
      float md_ds = Mathf.Infinity;
      SheepController sheep_c = null; // sheep furthest from CM
      float Md_sC = 0;

      foreach (SheepController sc in sheep)
      {
        // distance from CM
        float d_sC = (CM - sc.transform.position).magnitude;
        if (d_sC > Md_sC)
        {
          Md_sC = d_sC;
          sheep_c = sc;
        }

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
    foreach (SheepController sheep in sheepList)
    {
    float nn = Mathf.Infinity;
    foreach (SheepController sc in sheepList)
    {
      if (sc.id == sheep.id) continue;
      nn = Mathf.Min(nn, (sheep.transform.position - sc.transform.position).magnitude);
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
      float f_N = ro * Mathf.Pow(sheep.Count(), 2f / 3f);
      // draw aprox herd size
      Debug.DrawCircle(CM, f_N, new Color(1f, 0f, 0f, 1f));

#if true
      foreach (SheepController sc in sheep)
        Debug.DrawCircle(sc.transform.position, .5f, new Color(1f, 0f, 0f, 1f));
#endif

      // if all agents in a single compact group, collect them
      if (Md_sC < f_N)
      {
        BarnController barn = GameObject.FindObjectOfType<BarnController>();

        // compute position so that the GCM is on a line between the dog and the target
        Vector3 Pd = CM + (CM - barn.transform.position).normalized * ro * Mathf.Sqrt(sheep.Count()); // Mathf.Min(ro * Mathf.Sqrt(sheep.Count), Md_sC);
        desiredThetaVector = Pd - dc.transform.position;
        if (desiredThetaVector.magnitude > r_w)
          desiredV = GM.dogRunningSpeed;

        color = new Color(0f, 1f, 0f, 1f);
        Debug.DrawRay(Pd - X - Z, 2 * X, color);
        Debug.DrawRay(Pd + X - Z, 2 * Z, color);
        Debug.DrawRay(Pd + X + Z, -2 * X, color);
        Debug.DrawRay(Pd - X + Z, -2 * Z, color);
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
    }
    else
    {
      dc.dogState = Enums.DogState.idle;
      desiredV = .0f;
    }

    // extract desired heading
    desiredTheta = (Mathf.Atan2(desiredThetaVector.z, desiredThetaVector.x) + eps) * Mathf.Rad2Deg;
    /* end of behaviour logic */




    Movement desiredMovement = new Movement(desiredV, desiredTheta);
    return desiredMovement;
  }
}