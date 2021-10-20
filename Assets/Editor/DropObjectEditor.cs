using UnityEngine;
using UnityEditor;

public class DropObjectsEditorWindow : EditorWindow
{
    private bool m_bAlignRotations = true;

    // Add a menu item
    [MenuItem("Window/Drop Object(s)")]

    static void Awake()
    {
        // Get or create an editor window
        EditorWindow.GetWindow<DropObjectsEditorWindow>().Show();
    }

    void OnGUI()
    {
        EditorGUILayout.BeginHorizontal();

        if (GUILayout.Button("Drop/align selected object(s)"))
        {
            DropObjects();
        }

        EditorGUILayout.EndHorizontal();

        // Add checkbox for rotation alignment
        m_bAlignRotations = EditorGUILayout.ToggleLeft("Align Rotations", m_bAlignRotations);
    }

    void DropObjects()
    {
        Undo.RecordObjects(Selection.transforms, "Drop Objects");

        for (int i = 0; i < Selection.transforms.Length; i++)
        {
            GameObject go = Selection.transforms[i].gameObject;
            if (!go)
                continue;

            // Cast a ray and get all hits
            RaycastHit[] rgHits = Physics.RaycastAll(go.transform.position, -go.transform.up, Mathf.Infinity);

            // We can assume we did not hit the current game object, since a ray cast from within the collider will implicitly ignore that collision
            int iBestHit = -1;
            float flDistanceToClosestCollider = Mathf.Infinity;
            for (int iHit = 0; iHit < rgHits.Length; ++iHit)
            {
                RaycastHit CurHit = rgHits[iHit];

                // Assume we want the closest hit
                if (CurHit.distance > flDistanceToClosestCollider)
                    continue;

                // Cache off the best hit
                iBestHit = iHit;
                flDistanceToClosestCollider = CurHit.distance;
            }

            // Did we find something?
            if (iBestHit < 0)
            {
                Debug.LogWarning("Failed to find an object on which to place the game object " + go.name + ".");
                continue;
            }

            // Grab the best hit
            RaycastHit BestHit = rgHits[iBestHit];

            // Set position
            go.transform.position = new Vector3(BestHit.point.x, BestHit.point.y, BestHit.point.z);

            // Set rotation
            if (m_bAlignRotations)
            {
                go.transform.rotation *= Quaternion.FromToRotation(go.transform.up, BestHit.normal);
            }
        }
    }
}