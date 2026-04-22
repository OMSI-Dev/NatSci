/*
* Keeping Carbon Stored - ROUND TWO
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Send data to round two tiles to turn on. Recieve data form tiles and collect score while round two is being played.
* When all tiles have been pressed, it ends round two.
*/

using Godot;
using System;
using System.Collections.Generic;

public partial class Round2 : Node2D
{
	private RichTextLabel _r2ScoreText;
	private VideoStreamPlayer _r2VideoPlayer;

	[Export] public VideoStream introVideo;
	[Export] public VideoStream gameplayVideo;
	[Export] public float showTriggerTime = 12.5f;
	[Export] public float hideTriggerTime = 42.5f;

	string serialData     = "";
	List<string> dataList = new List<string>();
	List<string> r2Tiles  = new List<string>();
	List<bool> r2States   = new List<bool>();

	private int score            = 0;
	private bool round2Over      = false;
	private bool round2Start     = false;
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

		r2Tiles  = tileInfo.getRound2Tiles();
		r2States = tileInfo.getRound2States();

		// Verify that the autoload is in the global root folder.
		//if (HasNode("/root"))
			//GD.Print("Root exists");
		//var auto = GetNodeOrNull<Node>("/root/SerialCom");
		//GD.Print(auto == null ? "Autoload NOT found" : "Autoload FOUND");

		_r2VideoPlayer = GetNode<VideoStreamPlayer>("RoundTwoVideoPlayer");
		_r2ScoreText = GetNode<RichTextLabel>("CanvasLayer/RoundTwoScore");

		_r2ScoreText.Hide();
		_r2VideoPlayer.Hide();
	}

	public override void _Process(double delta)
	{
		if(round2Over) {
			//GD.Print("Round one is over. Returning from _Process function in Round One.");
			return;
		}
		if(tileInfo == null)  { GD.Print("Tile Info node is null in Round Two."); }
		if(serialCom == null) { GD.Print("SerialCom node is null in Round Two."); }

		if(_r2VideoPlayer == null) {
			GD.Print("Round Two videos failed to load.");
			return;
		}

		if(round2Start && !round2Over) {
			if(!_r2VideoPlayer.IsPlaying()) {
				_r2VideoPlayer.Show();
				_r2VideoPlayer.Play();
			}

			if(tilesSet == false) { return; }

			// Check if video is playing and target time is reached
			if (!txtTriggered && _r2VideoPlayer.IsPlaying() && _r2VideoPlayer.StreamPosition >= showTriggerTime)
			{
				if(_r2ScoreText == null) { GD.Print("Text node is null in Round Two's _Process function."); }
				ShowScoreText(true);
				//_r1ScoreText.Show();
				//_r1ScoreText.GlobalPosition = new Vector2(0, 500);
				//txtTriggered = true;
			}

			if(txtTriggered && _r2VideoPlayer.IsPlaying() && _r2VideoPlayer.StreamPosition >= hideTriggerTime) {
				//GD.Print("Turning off text at the right spot in the video.");
				ShowScoreText(false);
			}

			// add demo score
			if(txtTriggered) {
				if(GD.RandRange(0, 19) % 4 == 0 && GD.RandRange(0, 200) == 10) {
				// Only pick from tiles that are still active
					List<string> activeTiles = new List<string>();
					for(int i = 0; i < r2Tiles.Count; i++) {
						if(i < r2States.Count && r2States[i] == true) { activeTiles.Add(r2Tiles[i]); }
					}

					if(activeTiles.Count > 0) {
						score += GD.RandRange(0, 100);
						int index = (int)(GD.Randi() % activeTiles.Count);
						string selected = activeTiles[index];
		   				GD.Print("Selected tile to turn off: " + selected);
		   			 	bool done = allTilesOff(selected);
						if(done) {
							GD.Print("All tiles have been pressed.");
							roundTwoFinished();
						}
					}
				}
			}
			_r2ScoreText.Text = score.ToString();

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

	public void startRoundTwo(bool strt) {
		round2Start = strt;
		round2Over  = !strt;

		if(strt) {
			// Reset everything for a fresh start
			tilesSet     = false;
			txtTriggered = false;
			score        = 0;

			// Reset tile states
			for(int i = 0; i < r2States.Count; i++) { r2States[i] = false; }

			// Reconnect signal cleanly - unsub first to avoid double connections
			// Use functions so it won't give an error if not connected.
			DisconnectVideoSignal();
			ConnectVideoSignal();
			_r2VideoPlayer.Stream = introVideo;
			_r2ScoreText.Hide();
			_r2ScoreText.Text = "0";
		}
	}

	private void startRound2Tiles() {
		// Send the data to the round 1 tiles to turn on. All tiles turn on at once.
		string toSend;
		int i = 0;
		foreach(var tile in r2Tiles) {
			toSend = tile + "255000000";
			if(serialCom == null) {
				GD.Print("Serial communication not connected in Round Two's startRound2Tiles function.");
			}
			//serialCom.sendData(toSend);
			GD.Print(toSend);

			// Set current state of the tile we just sent data to is true / on.
			r2States[i] = true;
			i++;
		}
		GD.Print(i + " tiles have been turned on in Round 2's startRound2Tiles() function. Score reset to 0.");
		GD.Print("Round Two tile list: " + string.Join(", ", r2Tiles));
		tilesSet = true;
		score    = 0;
		_r2ScoreText.Text = "0";
	}

	private void OnVideoFinished()
	{
		_r2VideoPlayer.Hide();
		if(tilesSet) {
			// We have already played both videos and the round is over.
			roundTwoFinished();
			return;
		}
		// Switch to the gameplay video
		_r2VideoPlayer.Stream = gameplayVideo;
		_r2VideoPlayer.Play();
		_r2VideoPlayer.Show();

		var texture = _r2VideoPlayer.GetVideoTexture();
		if(texture != null) { txtPos = texture.GetSize(); }

		startRound2Tiles();
		GD.Print("r2States count: "  + r2States.Count);
		GD.Print("r2States values: " + string.Join(", ", r2States));
		GD.Print("r2Tiles count: "   + r2Tiles.Count);
	}

	private bool allTilesOff(string tile) {
		int index = r2Tiles.IndexOf(tile);
		GD.Print("Index for selected tile found: " + index);

		// Guard against tile not found
		if(index == -1) {
			GD.Print("Tile " + tile + " not found in r2Tiles list.");
			GD.Print("Current tile list: " + string.Join(", ", r2Tiles));
			return false;
		}

		// Guard against r2States being out of sync with r1Tiles
		if(index >= r2States.Count) {
			GD.Print("Index " + index + " is out of range for r2States (count: " + r2States.Count + ")");
			return false;
		}

		r2States[index] = false;
		//serialCom.sendData(tile + "000000000");
		GD.Print("Round Two tile " + tile + " has been pressed.");

		if (!r2States.Contains(true)) {
			GD.Print("All tiles turned off in Round Two.");
			return true;
		}
		return false;
	}

	private void roundTwoFinished() {
		GD.Print("Round two finished.");

		// Turn all remaining tiles off.
		foreach(var tile in r2Tiles) {
			//serialCom.sendData(tile + "000000000");
			allTilesOff(tile);
		}
		round2Start  = false;
		round2Over   = true;
		tilesSet     = false;
		txtTriggered = false;

		DisconnectVideoSignal();
		_r2VideoPlayer.Stop();
		_r2VideoPlayer.Hide();
		_r2ScoreText.Hide();
	}

	private void ConnectVideoSignal() {
		if(!vidSigConnected) {
			_r2VideoPlayer.Finished += OnVideoFinished;
			vidSigConnected = true;
		}
	}

	private void DisconnectVideoSignal() {
		if(vidSigConnected) {
			_r2VideoPlayer.Finished -= OnVideoFinished;
			vidSigConnected = false;
		}
	}

	private void ShowScoreText(bool vis) {
		txtTriggered = vis;
		if(txtTriggered) {
			_r2ScoreText.GlobalPosition = new Vector2((txtPos.X / 2) - 240, txtPos.Y / 4);
			_r2ScoreText.Show();
		} else {
			_r2ScoreText.Hide();
		}
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
}
