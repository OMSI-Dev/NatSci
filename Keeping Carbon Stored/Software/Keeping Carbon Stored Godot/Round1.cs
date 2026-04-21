/*
* Keeping Carbon Stored - ROUND ONE
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Send data to round one tiles to turn on. Recieve data form tiles and collect score while round one is being played.
* When all tiles have been pressed, it ends round one.
*/

using Godot;
using System;
using System.Collections.Generic;

public partial class Round1 : Node2D
{
	private RichTextLabel _r1ScoreText;
	private VideoStreamPlayer _r1VideoPlayer;

	[Export] public VideoStream introVideo;
	[Export] public VideoStream gameplayVideo;
	[Export] public float showTriggerTime = 12.5f;
	[Export] public float hideTriggerTime = 42.5f;

	string serialData     = "";
	List<string> dataList = new List<string>();
	List<string> r1Tiles  = new List<string>();
	List<bool> r1States   = new List<bool>();

	private int score         = 0;
	private bool round1Over   = false;
	private bool round1Start  = false;
	private bool tilesSet     = false;
	private bool txtTriggered = false;
	private Vector2 txtPos = new Vector2(0.0f, 0.0f);

	SerialCom serialCom;
	TileInfo tileInfo;

	public override void _Ready()
	{
		serialCom = GetNode<SerialCom>("/root/SerialCom");
		tileInfo  = GetNode<TileInfo>("/root/TileInfo");

		r1Tiles  = tileInfo.getRound1Tiles();
		r1States = tileInfo.getRound1States();

		// Verify that the autoload is in the global root folder.
		//if (HasNode("/root"))
			//GD.Print("Root exists");
		//var auto = GetNodeOrNull<Node>("/root/SerialCom");
		//GD.Print(auto == null ? "Autoload NOT found" : "Autoload FOUND");

		_r1VideoPlayer = GetNode<VideoStreamPlayer>("RoundOneVideoPlayer");
		_r1ScoreText = GetNode<RichTextLabel>("CanvasLayer/RoundOneScore");

		_r1ScoreText.Hide();
		_r1VideoPlayer.Hide();

		_r1VideoPlayer.Finished += OnVideoFinished;
		_r1VideoPlayer.Stream    = introVideo;
		//_r1VideoPlayer.Play();
	}

	public override void _Process(double delta)
	{
		if(tileInfo == null)  { GD.Print("Tile Info node is null in Round One."); }
		if(serialCom == null) { GD.Print("SerialCom node is null in Round One."); }

		if(_r1VideoPlayer == null) {
			GD.Print("Round One videos failed to load.");
			return;
		}

		if(round1Start) {
			if(!_r1VideoPlayer.IsPlaying()) {
				_r1VideoPlayer.Show();
				_r1VideoPlayer.Play();
			}

			if(tilesSet == false) { return; }

			// Check if video is playing and target time is reached
			if (!txtTriggered && _r1VideoPlayer.IsPlaying() && _r1VideoPlayer.StreamPosition >= showTriggerTime)
			{
				if(_r1ScoreText == null) { GD.Print("Text node is null in Round One's _Process function."); }
				ShowScoreText(true);
				//_r1ScoreText.Show();
				//_r1ScoreText.GlobalPosition = new Vector2(0, 500);
				//txtTriggered = true;
			}

			if(txtTriggered && _r1VideoPlayer.IsPlaying() && _r1VideoPlayer.StreamPosition >= hideTriggerTime) {
				GD.Print("Turning off text at the right spot in the video.");
				ShowScoreText(false);
			}

			// add demo score
			if(txtTriggered) {
				if(GD.RandRange(0, 301) % 9 == 0 && GD.RandRange(0, 20) % 7 == 0 && GD.RandRange(0, 19) % 4 == 0) {
					score += GD.RandRange(0, 100);
				}
			}
			_r1ScoreText.Text = score.ToString();

			//GD.Print("Round One started in Round1's _Process function.");
			/* // ******* Test Code *******
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
			}*/

			/* serialData = serialCom.getRawData();

			if(serialData.Length > 0) {
			//	GD.Print("Data from inside Round1: " + serialData);
				dataList = new List<string>(serialCom.getSplit());
			}

			if(dataList.Count > 1) {
				string tile = "";
				string time = "";

				tile = dataList[0] + dataList[1];
				GD.Print(tile + " was pressed in Round 1.");

				time = dataList[2] + dataList[3] + dataList[4] + dataList[5];
				GD.Print("Time was " + time);
				int toAdd;
				try {
					toAdd = int.Parse(time);
					GD.Print("Score to add is: " + toAdd);
					score += toAdd;
					GD.Print("Round One Current Score: " + score);

					// Update tiles that have been pushed and check for any still active.
					bool anyTilesLeft = allTilesComplete(tile);

					if(!anyTilesLeft) { roundOneFinished(); }
				}
				catch (FormatException e)
				{
					GD.Print(e.Message);
				}
			} */
		}
		// If round1Start = false:
	}

	private void OnVideoFinished()
	{
		_r1VideoPlayer.Hide();
		if(tilesSet) {
			// We have already played both videos and the round is over.
			roundOneFinished();
		}
		// Switch to the gameplay video
		_r1VideoPlayer.Stream = gameplayVideo;
		_r1VideoPlayer.Play();
		_r1VideoPlayer.Show();
		var texture = _r1VideoPlayer.GetVideoTexture();
		if(texture != null) {
			txtPos = texture.GetSize();
		}
		startRound1Tiles();
	}

	private void roundOneFinished() {
		round1Start = false;
		round1Over  = true;
		_r1VideoPlayer.Stream = introVideo;
	}

	public void startRoundOne(bool strt) {
		round1Start = strt;
		round1Over = !strt;
	}

	public bool getRound1Start() {
		return round1Start;
	}

	public bool isRound1Over() {
		return round1Over;
	}

	public void resetRound1Score() {
		score = 0;
	}

	public int round1Score() {
		return score;
	}

	private void ShowScoreText(bool vis) {
		txtTriggered = vis;
		if(txtTriggered) {
			_r1ScoreText.GlobalPosition = new Vector2((txtPos.X / 2) - 250, txtPos.Y / 4);
			_r1ScoreText.Show();
		} else {
			_r1ScoreText.Hide();
		}
	}

	private void startRound1Tiles() {
		// Send the data to the round 1 tiles to turn on. All tiles turn on at once.
		string toSend;
		int i = 0;
		foreach(var tile in r1Tiles) {
			toSend = tile + "255000000";
			if(serialCom == null) {
				GD.Print("Serial communication not connected in Round One's startRound1Tiles function.");
			}
			//serialCom.sendData(toSend);
			GD.Print(toSend);

			// Set current state of the tile we just sent data to is true / on.
			r1States[i] = true;
			i++;
		}
		GD.Print(i + " tiles have been turned on in Round 1's startRound1Tiles() function. Score reset to 0.");
		tilesSet = true;
		score    = 0;
		r1States.Clear();
		r1States = tileInfo.getRound1States();
		_r1ScoreText.Text = "0";
	}

	private bool allTilesComplete(string tile) {
		// If tile name was found in the list of tiles for round 1,
		// turn the bool with the corresponding index to false.
		int index = r1Tiles.IndexOf(tile);
		r1States[index] = false;
		//serialCom.sendData(tile + "000000000");

		GD.Print("Round One tile " + tile + "has been pressed.");

		// All values false, all tiles have been pressed.
		if (!r1States.Contains(true)) { return true; }

		// If tiles still remain turned on, return false.
		return false;
	}
}
