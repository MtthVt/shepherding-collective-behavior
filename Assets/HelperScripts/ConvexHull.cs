using System;
using System.Collections;
using System.Collections.Generic;
 
public class ConvexHull {
    public class Point : IComparable<Point> {
        public float x { get; set; }
        public float y { get; set; }
 
        public Point(float x, float y) {
            this.x = x;
            this.y = y;
        }
 
        //public float X { get { return x; } set { x = value; } }
        //public float Y { get { return y; } set { y = value; } }
 
        public int CompareTo(Point other) {
            return x.CompareTo(other.x);
        }
 
        public override string ToString() {
            return string.Format("({0}, {1})", x, y);
        }
    }
    //public class ConvexHull {
        public static List<Point> convexHull(List<Point> p) {
        if (p.Count == 0) return new List<Point>();
        p.Sort();
        List<Point> h = new List<Point>();

        // lower hull
        foreach (var pt in p) {
            while (h.Count >= 2 && !Ccw(h[h.Count - 2], h[h.Count - 1], pt)) {
                h.RemoveAt(h.Count - 1);
            }
            h.Add(pt);
        }

        // upper hull
        int t = h.Count + 1;
        for (int i = p.Count - 1; i >= 0; i--) {
            Point pt = p[i];
            while (h.Count >= t && !Ccw(h[h.Count - 2], h[h.Count - 1], pt)) {
                h.RemoveAt(h.Count - 1);
            }
            h.Add(pt);
        }

        h.RemoveAt(h.Count - 1);
        return h;
    }

    private static bool Ccw(Point a, Point b, Point c) {
        return ((b.x - a.x) * (c.y - a.y)) > ((b.y - a.y) * (c.x - a.x));
    }
    //}
    
}