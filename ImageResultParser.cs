using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Affdex;
using System.IO;
using System.Diagnostics;

//Parsed image data will be sent to the ImageResultsListener methods
public class ImageResultParser : ImageResultsListener {

	//emotion levels
	public float joyLevel;
	public float sadnessLevel;
	public float engagementLevel;
	public float disgustLevel;
	public string path = "Summaries/ExpressionSummary_X_voice_2.txt";

	public override void onFaceFound (float timestamp, int faceId)
	{
		File.WriteAllText(path,"joyLevel, sadnessLevel, engagementLevel, disgustLevel\n");
	}

	//called when the Affectiva SDK loses a facial detection
	public override void onFaceLost (float timestamp, int faceId)

	{
		//set emotion levels to 0 (will cause character to be Idle)
		joyLevel = 0;
		sadnessLevel = 0;
		engagementLevel = 0;
		disgustLevel = 0;
	}

	//called every second whether there is a face detected or not
	public override void onImageResults (Dictionary<int, Face> faces)
	{
		if (faces.Count > 0){
			//set emotion levels
			faces [0].Emotions.TryGetValue (Emotions.Joy, out joyLevel);
			faces [0].Emotions.TryGetValue (Emotions.Sadness, out sadnessLevel);
			faces [0].Emotions.TryGetValue (Emotions.Engagement, out engagementLevel);
			faces [0].Emotions.TryGetValue (Emotions.Disgust, out disgustLevel);
			// Create a file to write to.

			File.AppendAllText(path, joyLevel+",");
			File.AppendAllText(path, sadnessLevel+",");
			File.AppendAllText(path, disgustLevel+",");
			File.AppendAllText(path, engagementLevel+"\n");
			// Open the file to read from.
//			string readText = File.ReadAllText(path);

//			Console.WriteLine("Hello {0}", joyLevel);
//			System.Diagnostics.Debug.WriteLine(joyLevel);
		}
	}
}
