/*
* Keeping Carbon Stored - ROUND TWO
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Send data to round two tiles to turn on. Recieve data form tiles and collect score while round one is being played.
* When all tiles have been pressed, it ends round two.
*/

using Godot;
using System;
using System.Collections.Generic;

public partial class Round2 : Node2D
{
	private VideoStreamPlayer _r2VideoPlayer;

	[Export] public VideoStream introVideo;
	[Export] public VideoStream gameplayVideo;

	string serialData     = "";
	List<string> dataList = new List<string>();
	List<string> r2Tiles  = new List<string>();
	List<bool> r2States   = new List<bool>();

	private int score        = 0;
	private bool round2Over  = false;
	private bool round2Start = false;
	private bool tilesSet    = false;

	SerialCom serialCom;
	TileInfo tileInfo;

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		serialCom = GetNode<SerialCom>("/root/SerialCom");
		tileInfo  = GetNode<TileInfo>("/root/TileInfo");

		r2Tiles  = tileInfo.getRound2Tiles();
		r2States = tileInfo.getRound2States();
		// Verify that the autoload is in the global root folder.
		//if (HasNode("/root"))
			//GD.Print("Root exists");
		//var auto = GetNodeOrNull<Node>("/root/SerialCom");
		//GD.Print(auto == null ? "Autoload NOT found" : "Autoload FOUND");

		_r2VideoPlayer = GetNode<VideoStreamPlayer>("RoundTwoVideoPlayer");

		_r2VideoPlayer.Finished += OnVideoFinished;
		_r2VideoPlayer.Stream    = introVideo;
		_r2VideoPlayer.Play();
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
		if(round2Start) {
			if(!tilesSet) { return; }

			//GD.Print("Round Two started...");
			/* // ***** Test Code *****
			if(Input.IsActionJustPressed("two")) {
				GD.Print("Space bar was pressed.");
				int i = r1Tiles.IndexOf("A2");
				GD.Print("Index of A2 is " + i);
				GD.Print("A2 was pressed. The state was " + r1States[i]);
				if(r1States[i] == false) {
					r1States[i] = true;
					//Send black.
					serialCom.sendData("A2000000000");
				} else {
					//Send red.
					serialCom.sendData("A2255000000");
					r1States[i] = false;
				}
				GD.Print("The new state of A2 is " + r1States[i]);
			} */

			serialData = serialCom.getRawData();

			if(serialData.Length > 0) {
				//GD.Print("Data from inside Round2: " + serialData);
				dataList = new List<string>(serialCom.getSplit());
			}

			if(dataList.Count > 1) {
				// Reset tile and time values each time new data is recieved (ie a new button is pressed)
				string tile = "";
				string time = "";
				tile = dataList[0] + dataList[1];
				GD.Print(tile + " was pressed in Round 2.");

				time = dataList[2] + dataList[3] + dataList[4] + dataList[5];
				GD.Print("Time was " + time);
				int toAdd;
				try {
					toAdd = int.Parse(time);
					GD.Print("Time was: " + toAdd);
					score += toAdd;
					GD.Print("Round Two Current Score: " + score);

					// Update tiles that have been pushed and check for any still active.
					bool anyTilesLeft = allTilesComplete(tile);
					if(!anyTilesLeft) { roundTwoFinished(); }
				}
				catch (FormatException e)
				{
					GD.Print(e.Message);
				}
			}
		}
		// If round2Start = false:
	}

	private void OnVideoFinished()
	{
		// Switch to the gameplay video
		_r2VideoPlayer.Stream = gameplayVideo;
		_r2VideoPlayer.Play();
		startRound2Tiles();
	}

	private void roundTwoFinished() {
		round2Start = false;
		round2Over  = true;
		_r2VideoPlayer.Stream = introVideo;
	}

	public void startRoundTwo(bool strt) {
		round2Start = strt;
	}

	public bool getRound2Start() {
		return round2Start;
	}

	public bool isRound2Over() {
		return round2Over;
	}

	public void resetRound2Score() {
		score = 0;
	}

	public int round2Score() {
		return score;
	}

	private void startRound2Tiles() {
		// Send the data to the round 1 tiles to turn on. All tiles turn on at once.
		string toSend;
		int i = 0;

		foreach(var tile in r2Tiles) {
			toSend = tile + "000255000";
			serialCom.sendData(toSend);
			// Set current state of the tile we just sent data to is true / on.
			r2States[i] = true;
			i++;
		}
		GD.Print(i + " tiles have been turned on in Round 2's startRound2Tiles() function. Score reset to 0.");
		tilesSet = true;
		score    = 0;
		r2States.Clear();
		r2States = tileInfo.getRound2States();
	}

	private bool allTilesComplete(string tile) {
		// If tile name was found in the list of tiles for round 2, set bool with the corresponding index to false.
		int index       = r2Tiles.IndexOf(tile);
		r2States[index] = false;

		// All values false, all tiles have been pressed.
		if (!r2States.Contains(true)) { return true; }

		// If tiles still remain turned on, return false.
		return false;
	}
}
