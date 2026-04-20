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
	public SerialCom serCom;

	private bool gameStarted = false;
	private bool startIdle = false;

	private VideoStreamPlayer idleVideo;

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		serCom = GetNode<SerialCom>("/root/SerialCom");

		idleVideo = GetNode<VideoStreamPlayer>("IdleVideoPlayer");
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
		if(idleVideo == null) {
			GD.Print("Idle video failed to load.");
			return;
		}

		if(!idleVideo.IsPlaying()) { idleVideo.Play(); }

		if(!gameStarted) {
			string[] newData = serCom.getSplit();
			//GD.Print(newData);
			//GD.Print(newData[0]);
			if(newData != null) {
				if(newData[0] != "0") {
					GD.Print("Recieved Serial data while in Idle script. startGame is true.");
					gameStarted = true;
					idleVideo.Stop();
				}
			}
		}
	}

	public bool isGameStarted() {
		return gameStarted;
	}
}
