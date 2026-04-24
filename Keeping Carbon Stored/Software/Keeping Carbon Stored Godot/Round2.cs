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
	private RichTextLabel     _r2ScoreText;
	private VideoStreamPlayer _r2VideoPlayer;
	private RichTextLabel     _r2SmallScoreText;
	private RichTextLabel     _r2SmallScoreText2;

	[Export] public VideoStream introVideo;
	[Export] public VideoStream gameplayVideo;
	[Export] public float showTriggerTime      = 12.5f;
	[Export] public float hideTriggerTime      = 42.25f;
	[Export] public float showSmallTriggerTime = 47.0f;
	[Export] public float hideSmallTriggerTime = 52.5f;

	string serialData     = "";
	List<string> dataList = new List<string>();
	List<string> r2Tiles  = new List<string>();
	List<bool> r2States   = new List<bool>();

	private int score            = 0;
	private bool round2Over      = false;
	private bool round2Start     = false;
	private bool tilesSet        = false;
	private bool txtTriggered    = false;
	private bool smallTxtTrigger = false;
	private bool vidSigConnected = false;
	private Vector2 txtPos       = new Vector2(0.0f, 0.0f);

	SerialCom serialCom;
	TileInfo tileInfo;

	// -------------------------------------------------------------
	//  ********************* ROUND TWO READY *********************
	// -------------------------------------------------------------
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
		_r2SmallScoreText = GetNode<RichTextLabel>("CanvasLayer/RoundTwoSmallScore");
		_r2SmallScoreText2 = GetNode<RichTextLabel>("CanvasLayer/RoundTwoSmallScore2");

		_r2ScoreText.Hide();
		_r2SmallScoreText.Hide();
		_r2SmallScoreText2.Hide();
		_r2VideoPlayer.Hide();
	}

	// ------------------------------------------------------------
	//  ********************* ROUND TWO MAIN *********************
	// ------------------------------------------------------------
	public override void _Process(double delta)
	{
		if(round2Over) {
			return;
		}

		if(tileInfo == null)  { GD.Print("Tile Info node is null in Round Two."); }
		if(serialCom == null) { GD.Print("SerialCom node is null in Round Two."); }

		if(_r2VideoPlayer == null) {
			GD.Print("Round Two videos failed to load in Round Two script.");
			return;
		}

		if(!IsVisibleInTree()) { return; }

		if(round2Start && !round2Over) {
			if(!_r2VideoPlayer.IsPlaying()) {
				_r2VideoPlayer.Show();
				_r2VideoPlayer.Play();
			}

			if(tilesSet == false) { return; }

			// Check if video is playing and target time is reached for the big score
			if (!txtTriggered && _r2VideoPlayer.IsPlaying() && _r2VideoPlayer.StreamPosition >= showTriggerTime)
			{
				if(_r2ScoreText == null) { GD.Print("Text node is null in Round Two's _Process function."); }
				ShowScoreText(false, true);
			}

			if(txtTriggered && _r2VideoPlayer.IsPlaying() && _r2VideoPlayer.StreamPosition >= hideTriggerTime) {
				ShowScoreText(false, false);
			}

			// Check if video is playing and target time is reached for the small score
			if (!smallTxtTrigger && _r2VideoPlayer.IsPlaying() && _r2VideoPlayer.StreamPosition >= showSmallTriggerTime)
			{
				if(_r2SmallScoreText == null) { GD.Print("Text node is null in Round Two's _Process function."); }
				ShowScoreText(true, true);
			}

			if(smallTxtTrigger && _r2VideoPlayer.IsPlaying() && _r2VideoPlayer.StreamPosition >= hideSmallTriggerTime) {
				ShowScoreText(true, false);
			}

			// Demo score
			if(txtTriggered && _r2ScoreText.IsVisible()) {
				if(GD.RandRange(0, 20) % 4 == 0 && GD.RandRange(0, 200) == 10) {
				// Only pick from tiles that are still active
					List<string> activeTiles = new List<string>();
					for(int i = 0; i < r2Tiles.Count; i++) {
						if(i < r2States.Count && r2States[i] == true) { activeTiles.Add(r2Tiles[i]); }
					}

					if(activeTiles.Count > 0) {
						score++;
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
			_r2ScoreText.Text       = score.ToString();
			_r2SmallScoreText.Text  = score.ToString();
			_r2SmallScoreText2.Text = score.ToString();
		}
		// If round2Start = false: code here
	}

	// -------------------------------------------------------------
	//  ********************* START ROUND TWO *********************
	// -------------------------------------------------------------
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
			_r2SmallScoreText.Hide();
			_r2SmallScoreText2.Hide();
			_r2ScoreText.Text       = "0";
			_r2SmallScoreText.Text  = "0";
			_r2SmallScoreText2.Text = "0";
		}
	}

	// -------------------------------------------------------
	//  ********************* SET TILES *********************
	// -------------------------------------------------------
	private void startRound2Tiles() {
		// Send the data to the round 1 tiles to turn on. All tiles turn on at once.
		string toSend;
		int i = 0;
		GD.Print("Sending serial com to turn round two tiles on:");
		foreach(var tile in r2Tiles) {
			toSend = tile + "000255000";
			if(serialCom == null) {
				GD.Print("Serial communication not connected in Round Two's startRound2Tiles function.");
			}
			serialCom.sendData(toSend);
			GD.Print(toSend);

			// Set current state of the tile we just sent data to is true / on.
			r2States[i] = true;
			i++;
		}
		tilesSet = true;
		score    = 0;
		_r2ScoreText.Text       = "0";
		_r2SmallScoreText.Text  = "0";
		_r2SmallScoreText2.Text = "0";
		GD.Print(i + " tiles have been turned on in Round 2's startRound2Tiles() function. Scores set to: " + _r2ScoreText.Text + _r2SmallScoreText.Text + _r2SmallScoreText2.Text);;
		GD.Print("Round Two tile list: " + string.Join(", ", r2Tiles));
	}

	// ------------------------------------------------------------
	//  ********************* VIDEO FINISHED *********************
	// ------------------------------------------------------------
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
		GD.Print(r2States.Count + " states set in Round Two.");
		GD.Print("Tiles on: " + string.Join(", ", r2States));
	}

	// ------------------------------------------------------------
	//  ********************* TURN TILES OFF *********************
	// ------------------------------------------------------------
	private bool allTilesOff(string tile) {
		int index = r2Tiles.IndexOf(tile);
		GD.Print(tile + " index: " + index);

		if(!r2States[index]) {
			GD.Print(tile + " already off.");
			return false;
		}

		// Guard against tile not found
		if(index == -1) {
			GD.Print(tile + " not found in r2Tiles list.");
			GD.Print("Current tile list: " + string.Join(", ", r2Tiles));
			return false;
		}

		// Guard against r2States being out of sync with r1Tiles
		if(index >= r2States.Count) {
			GD.Print("Index " + index + " is out of range for r2States (count: " + r2States.Count + ")");
			return false;
		}

		r2States[index] = false;
		serialCom.sendData(tile + "000000000");
		GD.Print("Serial com data sent to " + tile + ": " + tile + "000000000");
		GD.Print(tile + " turned off in Round Two.");

		if (!r2States.Contains(true)) {
			GD.Print("All tiles turned off in Round Two.");
			return true;
		}
		return false;
	}

	// ----------------------------------------------------------------
	//  ********************* ROUND TWO FINISHED *********************
	// ----------------------------------------------------------------
	private void roundTwoFinished() {
		GD.Print("*** ROUND TWO FINISHED. ***");

		// Turn all remaining tiles off.
		GD.Print("Turning off remaining tiles in Round Two...");
		foreach(var tile in r2Tiles) {
			serialCom.sendData(tile + "000000000");
			allTilesOff(tile);
		}
		GD.Print(r2States.Count + " states set in Round Two.");
		GD.Print("Tile states: " + string.Join(", ", r2States));

		round2Start  = false;
		round2Over   = true;
		tilesSet     = false;
		txtTriggered = false;

		DisconnectVideoSignal();
		_r2VideoPlayer.Stop();
		_r2VideoPlayer.Hide();
		_r2ScoreText.Hide();
	}

	// ------------------------------------------------------------
	//  ********************* CONNECT SIGNAL *********************
	// ------------------------------------------------------------
	private void ConnectVideoSignal() {
		if(!vidSigConnected) {
			_r2VideoPlayer.Finished += OnVideoFinished;
			vidSigConnected = true;
		}
	}

	// ---------------------------------------------------------------
	//  ********************* DISCONNECT SIGNAL *********************
	// ---------------------------------------------------------------
	private void DisconnectVideoSignal() {
		if(vidSigConnected) {
			_r2VideoPlayer.Finished -= OnVideoFinished;
			vidSigConnected = false;
		}
	}

	// -------------------------------------------------------------
	//  ********************* SHOW SCORE TEXT *********************
	// -------------------------------------------------------------
	private void ShowScoreText(bool small, bool vis) {
		txtTriggered = vis;
		smallTxtTrigger = small;
		if(txtTriggered && !smallTxtTrigger) {
			_r2ScoreText.GlobalPosition = new Vector2((txtPos.X / 2) - 240, txtPos.Y / 4);
			_r2ScoreText.Show();
		} else if(!txtTriggered && !small){
			_r2ScoreText.Hide();
		} else if(txtTriggered && small) {
			_r2SmallScoreText.GlobalPosition = new Vector2(1360, 517);
			_r2SmallScoreText.Show();
			_r2SmallScoreText2.GlobalPosition = new Vector2(1450, 668);
			_r2SmallScoreText2.Show();
		} else if(!txtTriggered && small) {
			_r2SmallScoreText.Hide();
			_r2SmallScoreText2.Hide();
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
