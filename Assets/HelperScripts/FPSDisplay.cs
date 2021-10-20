using UnityEngine;
using System.Collections;
 
public class FPSDisplay : MonoBehaviour
{
	private GameManager GM;
	private float maxFrameTime = 0f;
	private int frameCount = 0;
	private float totalFrameTime = 0f;

	float deltaTime = 0.0f;

	void Start()
	{
		GM = FindObjectOfType<GameManager>();
	}
 
	void Update()
	{
		deltaTime += (Time.unscaledDeltaTime - deltaTime) * 0.1f;
	}
 
	void OnGUI()
	{
		if(GM.simulationRunning) {
			int w = Screen.width, h = Screen.height;
	
			GUIStyle style = new GUIStyle();
	
			Rect rect = new Rect(0, 0, w, h * 2 / 100);
			style.alignment = TextAnchor.UpperLeft;
			style.fontSize = h * 2 / 100;
			style.normal.textColor = new Color (0.0f, 0.0f, 0.5f, 1.0f);
			float msec = deltaTime * 1000.0f;
			float fps = 1.0f / deltaTime;
			string text = string.Format("{0:0.0} ms ({1:0.} fps)", msec, fps);
			GUI.Label(rect, text, style);

			frameCount++;
			totalFrameTime += msec;
			if (msec > maxFrameTime) {
				maxFrameTime = msec;
				GM.maxFrameTime = msec;
			}
			GM.avgFrameTime = totalFrameTime / frameCount;
		}
		
	}
}