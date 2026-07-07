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

	private bool gameStarted = false;
	private bool idleSent = false;
	private bool startIdle = false;
	private float timeToStart = 5.0f;

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
		if (idleVideo == null)
		{
			GD.Print("Idle video failed to load in Idle script.");
			return;
		}

		if (!IsVisibleInTree()) { return; }

		if (!idleVideo.IsPlaying())
		{
			idleVideo.Show();
			idleVideo.Play();
			timeToStart = 5.0f;
			GD.Print("The game can be started in " + timeToStart + " seconds...");
		}

		// Let at least five seconds pass before being able to get out of Idle Mode.
		if (timeToStart > 0 && !gameStarted)
		{
			timeToStart -= (float)delta;
		}
		if (timeToStart <= 0 && !startIdle)
		{
			GD.Print("Timer is up to be able to start the game.");
			startIdle = true;
		}

		if (!gameStarted && startIdle)
		{
			if (!idleSent)
			{
				serialCom.sendData("II000000000");
				GD.Print("Sent 'II00000000' through serial communication.");
				idleSent = true;
			}
			//string[] newData = serialCom.getSplit();
			string newData = serialCom.getRawData();
			if (newData != null && newData.Length != 0)
			{
				if (newData != "")
				{
					//GD.Print("New data recieved: " + string.Join(", ", newData));
					GD.Print("New data recieved: " + newData);
					GD.Print("Recieved Serial data while in Idle script. startGame is true.");
					gameStarted = true;
					idleVideo.Stop();
					idleSent = false;
					startIdle = false;
				}
			}
		}
	}

	public bool isGameStarted()
	{
		gameStarted = true;
		return gameStarted;
	}
}
