using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TranslateObjectRealtime : MonoBehaviour {
  
    // Inspector ON/OFF switch
    public bool enable = false;

    // Speed of rotation
    public float speed;

	// Update is called once per frame
	void Update () {
		if(enable) this.transform.Rotate(Vector3.up * Time.deltaTime * speed);
    }
}
