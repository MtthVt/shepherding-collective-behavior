using UnityEngine;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

class Debug : UnityEngine.Debug
{
  public static void DrawCircle(Vector3 c, float r, Color clr, bool dashed = false, int prec = 36)
  {
    for (int i=0; i < prec; i++)
    {
      float phi = 2f * Mathf.PI * i / prec;
      Vector3 s0 = new Vector3(Mathf.Cos(phi), 0f, Mathf.Sin(phi));
      float phi1 = 2f * Mathf.PI * (i + 1) / prec;
      Vector3 s1 = new Vector3(Mathf.Cos(phi1), 0f, Mathf.Sin(phi1));

      DrawLine(c + r * s0, c + r * s1, clr);

      if (dashed) i++;
    }
  }
}
