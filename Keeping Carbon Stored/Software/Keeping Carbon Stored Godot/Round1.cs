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

	private int score            = 0;
	private bool round1Over      = false;
	private bool round1Start     = false;
	private bool tilesSet        = false;
	private bool txtTriggered    = false;
	private bool vidSigConnected = false;
	private Vector2 txtPos       = new Vector2(0.0f, 0.0f);

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
	}

	public override void _Process(double delta)
	{
		if(round1Over) {
			//GD.Print("Round one is over. Returning from _Process function in Round One.");
			return;
		}
		if(tileInfo == null)  { GD.Print("Tile Info node is null in Round One."); }
		if(serialCom == null) { GD.Print("SerialCom node is null in Round One."); }

		if(_r1VideoPlayer == null) {
			GD.Print("Round One videos failed to load.");
			return;
		}

		if(round1Start && !round1Over) {
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
				//GD.Print("Turning off text at the right spot in the video.");
				ShowScoreText(false);
			}

			// add demo score
			if(txtTriggered) {
				if(GD.RandRange(0, 19) % 4 == 0 && GD.RandRange(0, 200) == 10) {
				// Only pick from tiles that are still active
					List<string> activeTiles = new List<string>();
					for(int i = 0; i < r1Tiles.Count; i++) {
						if(i < r1States.Count && r1States[i] == true) { activeTiles.Add(r1Tiles[i]); }
					}

					if(activeTiles.Count > 0) {
						score += GD.RandRange(0, 100);
						int index = (int)(GD.Randi() % activeTiles.Count);
						string selected = activeTiles[index];
		   				GD.Print("Selected tile to turn off: " + selected);
		   			 	bool done = allTilesOff(selected);
						if(done) {
							GD.Print("All tiles have been pressed.");
							roundOneFinished();
						}
					}
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
					bool anyTilesLeft = !allTilesOff(tile);

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

	public void startRoundOne(bool strt) {
		round1Start = strt;
		round1Over  = !strt;

		if(strt) {
			// Reset everything for a fresh start
			tilesSet     = false;
			txtTriggered = false;
			score        = 0;

			// Reset tile states
			for(int i = 0; i < r1States.Count; i++) { r1States[i] = false; }

			// Reconnect signal cleanly - unsub first to avoid double connections
			// Use functions so it won't give an error if not connected.
			DisconnectVideoSignal();
			ConnectVideoSignal();
			_r1VideoPlayer.Stream = introVideo;
			_r1ScoreText.Hide();
			_r1ScoreText.Text = "0";
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
		GD.Print("Round One tile list: " + string.Join(", ", r1Tiles));
		tilesSet = true;
		score    = 0;
		_r1ScoreText.Text = "0";
	}

	private void OnVideoFinished()
	{
		_r1VideoPlayer.Hide();
		if(tilesSet) {
			// We have already played both videos and the round is over.
			roundOneFinished();
			return;
		}
		// Switch to the gameplay video
		_r1VideoPlayer.Stream = gameplayVideo;
		_r1VideoPlayer.Play();
		_r1VideoPlayer.Show();

		var texture = _r1VideoPlayer.GetVideoTexture();
		if(texture != null) { txtPos = texture.GetSize(); }

		startRound1Tiles();
		GD.Print("r1States count: "  + r1States.Count);
		GD.Print("r1States values: " + string.Join(", ", r1States));
		GD.Print("r1Tiles count: "   + r1Tiles.Count);
	}

	private bool allTilesOff(string tile) {
		int index = r1Tiles.IndexOf(tile);
		GD.Print("Index for selected tile found: " + index);

		// Guard against tile not found
		if(index == -1) {
			GD.Print("Tile " + tile + " not found in r1Tiles list.");
			GD.Print("Current tile list: " + string.Join(", ", r1Tiles));
			return false;
		}

		// Guard against r1States being out of sync with r1Tiles
		if(index >= r1States.Count) {
			GD.Print("Index " + index + " is out of range for r1States (count: " + r1States.Count + ")");
			return false;
		}

		r1States[index] = false;
		//serialCom.sendData(tile + "000000000");
		GD.Print("Round One tile " + tile + " has been pressed.");

		if (!r1States.Contains(true)) {
			GD.Print("All tiles have been turned off in Round One.");
			return true;
		}

		return false;
	}

	private void roundOneFinished() {
		GD.Print("Round one finished.");

		// Turn all tiles off.
		foreach(var tile in r1Tiles) {
			//serialCom.sendData(tile + "000000000");
			allTilesOff(tile);
		}

		round1Start  = false;
		round1Over   = true;
		tilesSet     = false;
		txtTriggered = false;

		DisconnectVideoSignal();
		_r1VideoPlayer.Stop();
		_r1VideoPlayer.Hide();
		_r1ScoreText.Hide();
	}

	private void ConnectVideoSignal() {
		if(!vidSigConnected) {
			_r1VideoPlayer.Finished += OnVideoFinished;
			vidSigConnected = true;
		}
	}

	private void DisconnectVideoSignal() {
		if(vidSigConnected) {
			_r1VideoPlayer.Finished -= OnVideoFinished;
			vidSigConnected = false;
		}
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
}
