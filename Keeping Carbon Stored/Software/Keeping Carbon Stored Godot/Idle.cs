/*
* Keeping Carbon Stored - IDLE SCREEN
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Play Idle screen video until button is pressed to signal the start of the game.
*/

using Godot;
using System;

public partial class Idle : Node2D
{
	SerialCom serialCom;

	private bool gameStarted  = false;
	private bool idleSent	  = false;
	private bool startIdle    = false;
	private float timeToStart = 20.0f;

	private VideoStreamPlayer idleVideo;

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		serialCom = GetNode<SerialCom>("/root/SerialCom");

		idleVideo = GetNode<VideoStreamPlayer>("IdleVideoPlayer");
		idleVideo.Hide();
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
		if(idleVideo == null) {
			GD.Print("Idle video failed to load in Idle script.");
			return;
		}

		if(!IsVisibleInTree()) { return; }

		//if(!idleVideo.IsPlaying()) {
			//idleVideo.Show();
			//idleVideo.Play();
			//timeToStart = 2.0f;
		//}

		if(!gameStarted) {
			if(!idleSent) {
				serialCom.sendData("I");
				idleSent = true;
			}
			string[] newData = serialCom.getSplit();
			if(newData != null && newData.Length > 0) {
				//if(newData[0] != "0") {
					GD.Print("New data recieved: " + string.Join(", ", newData));
					GD.Print("Recieved Serial data while in Idle script. startGame is true.");
					gameStarted = true;
					idleVideo.Stop();
					idleSent = false;
				//}
			}
			//if (timeToStart > 0) {
				//timeToStart -= (float)delta;
				//GD.Print($"Time remaining: {Mathf.Max(0, timeToStart)}");
			//}
			//if(timeToStart <= 0) {
				//GD.Print("Timer up to start the game.");
				//gameStarted = true;
			//}
		}
	}

	public bool isGameStarted() {
		return gameStarted;
	}
}
