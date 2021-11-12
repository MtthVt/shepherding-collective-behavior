using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using System;

public class DogBehaviourArc2 : DogBehaviour
{

  public DogBehaviourArc2(GameManager GM, DogController dc) : base(GM, dc) { }

  // weight direct and arc vectors according to distance to closest sheep
  private float r_2s = 45;
  private float r_s = 22.5f;
  private float r_sS = 12.25f;

  private float directVectorWeight(float d)
  {
    if (d > r_2s) return 1;
    if (d > r_s) return 0.5f + ((d - r_s) / (r_2s - r_s)) * 0.5f;
    if (d > r_sS) return 0.5f;
    return (d / r_sS) * 0.5f;
  }

  private float arcVectorWeight(float d)
  {
    if (d > r_2s) return 0;
    if (d > r_s) return ((r_2s - d) / (r_2s - r_s)) * 0.5f;
    if (d > r_sS) return 0.5f;
    return 0.5f + ((r_sS - d) / r_sS) * 0.5f;
  }

  private float directVectorWeight2(float d)
  {
    if (d > r_s) return 1;
    return d / r_s;
  }

  private float arcVectorWeight2(float d)
  {
    if (d > r_s) return 0;
    return (r_s - d) / r_s;
  }


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
      float f_N = ro * Mathf.Pow(sheep.Count, 2f / 3f);
      // draw aprox herd size
      Debug.DrawCircle(CM, f_N, new Color(1f, 0f, 0f, 1f));

#if true
      foreach (SheepController sc in sheep)
        Debug.DrawCircle(sc.transform.position, .5f, new Color(1f, 0f, 0f, 1f));
#endif
      // bool driving = false;
      // if all agents in a single compact group, collect them
      //if (Md_sC < f_N)
      // modified: if we have multiple dogs, one is always in driving mode
      if (Md_sC < f_N || (GM.dogList.Count() > 1 && dc.id == 0))
      {
        BarnController barn = GameObject.FindObjectOfType<BarnController>();

        // compute position so that the GCM is on a line between the dog and the target
        Vector3 Pd = CM + (CM - barn.transform.position).normalized * ro * Mathf.Sqrt(sheep.Count); // Mathf.Min(ro * Mathf.Sqrt(sheep.Count), Md_sC);
        // Vector3 Pd = CM + (CM - barn.transform.position).normalized * ro * 5; // Mathf.Min(ro * Mathf.Sqrt(sheep.Count), Md_sC);

        desiredThetaVector = Pd - dc.transform.position;
        if (desiredThetaVector.magnitude > r_w)
          desiredV = GM.dogRunningSpeed;

        color = new Color(0f, 1f, 0f, 1f);
        Debug.DrawRay(Pd - X - Z, 2 * X, color);
        Debug.DrawRay(Pd + X - Z, 2 * Z, color);
        Debug.DrawRay(Pd + X + Z, -2 * X, color);
        Debug.DrawRay(Pd - X + Z, -2 * Z, color);

        // driving = true;
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


      Vector3 cmVector = CM - dc.transform.position;
      Debug.DrawRay(dc.transform.position, cmVector, Color.red);
      float cmTheta = (Mathf.Atan2(cmVector.z, cmVector.x) + eps) * Mathf.Rad2Deg;

      desiredTheta = (Mathf.Atan2(desiredThetaVector.z, desiredThetaVector.x) + eps) * Mathf.Rad2Deg;
      float delta = cmTheta - desiredTheta;
      delta = (delta + 180f) % 360f - 180f;
      Vector3 arcVector = new Vector3();
      foreach (SheepController sc in sheep)
      {
        Vector3 scVector = sc.position - dc.transform.position;
        //Debug.DrawRay(dc.transform.position, cmVector, Color.red);
        float scTheta = (Mathf.Atan2(scVector.z, scVector.x) + eps) * Mathf.Rad2Deg;
        if (delta < 0)
        {
          scTheta = (scTheta + 90f + 180f) % 360f - 180f;
        }
        else
        {
          scTheta = (scTheta - 90f + 180f) % 360f - 180f;
        }
        float scThetaRad = scTheta * Mathf.Deg2Rad;
        Vector3 scVector90 = new Vector3(Mathf.Cos(scThetaRad), 0, Mathf.Sin(scThetaRad));
        scVector90 = scVector90 * Mathf.Pow(md_ds, 2) / scVector.sqrMagnitude;
        arcVector += scVector90;
        Debug.DrawRay(dc.transform.position, scVector90 * 10, new Color(1f, 1f, 1f, 0.2f));
      }
      arcVector = arcVector.normalized;
      Debug.DrawRay(dc.transform.position, arcVector.normalized * 10, new Color(1f, 1f, 1f, 1f));

      Vector3 directVector = desiredThetaVector.normalized;


      // repulsion from fences
      float r_f2 = GM.DogsParametersOther.r_f * GM.DogsParametersOther.r_f;
      Vector3 fenceRepulsionVector = new Vector3();
      foreach (Collider fenceCollider in GM.fenceColliders)
      {
        Vector3 closestPoint = fenceCollider.ClosestPointOnBounds(dc.transform.position);
        if ((dc.transform.position - closestPoint).sqrMagnitude < r_f2)
        {
          Vector3 e_ij = closestPoint - dc.transform.position;
          float d_ij = e_ij.magnitude;

          float f_ij = Mathf.Min(.0f, (d_ij - GM.DogsParametersOther.r_f) / GM.DogsParametersOther.r_f);

          fenceRepulsionVector += f_ij * e_ij.normalized;
        }
      }
      Debug.DrawRay(dc.transform.position, fenceRepulsionVector, new Color(0.5f, 1.0f, 0.5f));

      // desiredThetaVector = directVector * directVectorWeight(md_ds) + arcVector * arcVectorWeight(md_ds) + fenceRepulsionVector * GM.DogsParametersOther.rho_f;
      desiredThetaVector = directVector * directVectorWeight2(md_ds) + arcVector * arcVectorWeight2(md_ds) + fenceRepulsionVector * GM.DogsParametersOther.rho_f;




      Debug.DrawRay(dc.transform.position, desiredThetaVector.normalized * 10, Color.yellow);



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



    // extract desired heading
    desiredTheta = (Mathf.Atan2(desiredThetaVector.z, desiredThetaVector.x) + eps) * Mathf.Rad2Deg;
    /* end of behaviour logic */


    if (GM.DogsParametersStrombom.occlusion) drawBlindAngle();


    Movement desiredMovement = new Movement(desiredV, desiredTheta);
    return desiredMovement;
  }

  private void drawBlindAngle()
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

  private void drawConvexHull(List<SheepController> sheep)
  {
    List<ConvexHull.Point> points = new List<ConvexHull.Point>();
    foreach (SheepController sc in sheep)
    {
      points.Add(new ConvexHull.Point(sc.position.x, sc.position.z));
    }
    List<ConvexHull.Point> hull = ConvexHull.convexHull(points);
    ConvexHull.Point prev = hull.Last();
    foreach (ConvexHull.Point p in hull)
    {
      Debug.DrawRay(new Vector3(prev.x, 0, prev.y), new Vector3(p.x - prev.x, 0, p.y - prev.y), new Color(1f, 0f, 1f, 0.4f));
      prev = p;
    }
    List<ConvexHull.Point> expandedHull = new List<ConvexHull.Point>();
    if (hull.Count > 1)
    {
      for (int i = 0; i < hull.Count(); i++)
      {
        prev = i > 0 ? hull[i - 1] : hull.Last();
        ConvexHull.Point next = i < hull.Count - 1 ? hull[i + 1] : hull[0];
        float prevAngle = (Mathf.Atan2(prev.y - hull[i].y, prev.x - hull[i].x)) * Mathf.Rad2Deg;
        float prevPlus90 = (prevAngle + 90f + 180f) % 360f - 180f;
        float nextAngle = (Mathf.Atan2(next.y - hull[i].y, next.x - hull[i].x)) * Mathf.Rad2Deg;
        float nextMinus90 = (nextAngle - 90f + 180f) % 360f - 180f;
        float delta12 = (nextMinus90 - prevPlus90 + 720f) % 360f;
        int nSteps = (int)(delta12 / 30f) + 1;
        Vector3 currentPointVector = new Vector3(hull[i].x, 0, hull[i].y);
        for (int j = 0; j <= nSteps; j++)
        {
          float angle = (prevPlus90 + j * (delta12 / nSteps)) * Mathf.Deg2Rad;
          Vector3 vec = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * 5f + currentPointVector;
          ConvexHull.Point p = new ConvexHull.Point(vec.x, vec.z);
          expandedHull.Add(p);

        }
      }
    }
    else
    {
      Vector3 currentPointVector = new Vector3(hull[0].x, 0, hull[0].y);
      for (int i = 0; i < 12; i++)
      {
        float angle = i * 30 * Mathf.Deg2Rad;
        Vector3 vec = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * 5f + currentPointVector;
        ConvexHull.Point p = new ConvexHull.Point(vec.x, vec.z);
        expandedHull.Add(p);
      }
    }

    prev = expandedHull.Last();
    foreach (ConvexHull.Point p in expandedHull)
    {
      Debug.DrawRay(new Vector3(prev.x, 0, prev.y), new Vector3(p.x - prev.x, 0, p.y - prev.y), new Color(1f, 0f, 1f, 0.7f));
      prev = p;
    }
  }
}