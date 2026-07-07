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
using System.Reflection;

public partial class Round1 : Node2D
{
	private RichTextLabel _r1ScoreText;
	private VideoStreamPlayer _r1VideoPlayer;
	private RichTextLabel _r1SmallScoreText;
	private RichTextLabel _r1SmallScoreText2;

	private RichTextLabel _Score;
	private RichTextLabel _Puntaje;

	[Export] public VideoStream introVideo;
	[Export] public VideoStream gameplayVideo;
	[Export] public float showTriggerTime = 12.5f;
	[Export] public float hideTriggerTime = 42.25f;
	[Export] public float showSmallTriggerTime = 47.0f;
	[Export] public float hideSmallTriggerTime = 52.5f;

	string serialData = "";
	List<string> dataList = new List<string>();
	List<string> r1Tiles = new List<string>();
	List<bool> r1States = new List<bool>();

	private int score = 0;
	private bool round1Over = false;
	private bool round1Start = false;
	private bool tilesSet = false;
	private bool txtTriggered = false;
	private bool smallTxtTrigger = false;
	private bool vidSigConnected = false;
	private Vector2 txtPos = new Vector2(0.0f, 0.0f);

	SerialCom serialCom;
	TileInfo tileInfo;

	// -------------------------------------------------------------
	//  ********************* ROUND ONE READY *********************
	// -------------------------------------------------------------
	public override void _Ready()
	{
		serialCom = GetNode<SerialCom>("/root/SerialCom");
		tileInfo = GetNode<TileInfo>("/root/TileInfo");

		r1Tiles = tileInfo.getRound1Tiles();
		r1States = tileInfo.getRound1States();

		// Verify that the autoload is in the global root folder.
		//if (HasNode("/root"))
		//GD.Print("Root exists");
		//var auto = GetNodeOrNull<Node>("/root/SerialCom");
		//GD.Print(auto == null ? "Autoload NOT found" : "Autoload FOUND");

		_r1VideoPlayer = GetNode<VideoStreamPlayer>("RoundOneVideoPlayer");
		_r1ScoreText = GetNode<RichTextLabel>("CanvasLayer/RoundOneScore");
		_r1SmallScoreText = GetNode<RichTextLabel>("CanvasLayer/RoundOneSmallScore");
		_r1SmallScoreText2 = GetNode<RichTextLabel>("CanvasLayer/RoundOneSmallScore2");
		_Score = GetNode<RichTextLabel>("CanvasLayer/Score");
		_Puntaje = GetNode<RichTextLabel>("CanvasLayer/Puntaje");

		_r1ScoreText.Hide();
		_r1SmallScoreText.Hide();
		_r1SmallScoreText2.Hide();
		_r1VideoPlayer.Hide();
	}

	// ------------------------------------------------------------
	//  ********************* ROUND ONE MAIN *********************
	// ------------------------------------------------------------
	public override void _Process(double delta)
	{
		if (round1Over) { return; }

		if (tileInfo == null) { GD.Print("Tile Info node is NULL in Round One."); }
		if (serialCom == null) { GD.Print("SerialCom node is NULL in Round One."); }

		if (_r1VideoPlayer == null)
		{
			GD.Print("Round One videos FAILED TO LOAD in Round One script.");
			return;
		}

		if (!IsVisibleInTree()) { return; }

		if (round1Start && !round1Over)
		{
			if (!_r1VideoPlayer.IsPlaying())
			{
				_r1VideoPlayer.Show();
				_r1VideoPlayer.Play();
			}

			string vidSource = "res://Media/r1Gameplay1080.ogv";
			if (_r1VideoPlayer.Stream.ResourcePath != vidSource) { return; }

			// Check if video is playing and target time is reached for the big score
			if (!txtTriggered && _r1VideoPlayer.IsPlaying() && _r1VideoPlayer.StreamPosition >= showTriggerTime)
			{
				if (_r1ScoreText == null) { GD.Print("Text node is NULL in Round One's _Process function."); }
				ShowScoreText(false, true);
			}

			if (txtTriggered && _r1VideoPlayer.IsPlaying() && _r1VideoPlayer.StreamPosition >= hideTriggerTime)
			{
				ShowScoreText(false, false);
			}

			// Check if video is playing and target time is reached for the small score
			if (!smallTxtTrigger && _r1VideoPlayer.IsPlaying() && _r1VideoPlayer.StreamPosition >= showSmallTriggerTime)
			{
				if (_r1SmallScoreText == null) { GD.Print("Text node is NULL in Round One's _Process function."); }
				ShowScoreText(true, true);
			}

			if (smallTxtTrigger && _r1VideoPlayer.IsPlaying() && _r1VideoPlayer.StreamPosition >= hideSmallTriggerTime)
			{
				ShowScoreText(true, false);
			}

			// __________________________________________________
			// ***************** REAL GAMEPLAY *****************
			if (txtTriggered && _r1ScoreText.IsVisible())
			{
				if (!tilesSet)
				{
					startRound1Tiles();
					GD.Print(r1States.Count + " tiles set in Round One: " + string.Join(", ", r1States));
				}

				//string[] newData = serialCom.getSplit();
				string newData = serialCom.getRawData();
				if (newData != null || newData.Length != 0)
				{
					if (newData != "")
					{
						//GD.Print("New data recieved in Round One gameplay: " + newData);
						string selected = newData.Substring(0, 2);
						GD.Print(selected + " tile pressed while playing Round One.");
						int indx = getTileIndex(selected);
						if (indx >= 0)
						{
							if (!r1States[indx])
							{
								GD.Print(selected + " already OFF.");
							}
							else
							{
								//allTilesOff(selected);
								bool done = allTilesOff(selected);
								score++;
								if (done)
								{
									GD.Print("All non-ADA tiles have been pressed in Round One. Turning them on again...");
									restartTiles();
									done = false;
								}
							}
						}
						else
						{
							GD.Print("Tile " + selected + " is not in Round One.");
						}
					}
				}
			}

			/*// Demo score
			if(txtTriggered && _r1ScoreText.IsVisible()) {
				if(GD.RandRange(0, 20) % 4 == 0 && GD.RandRange(0, 100) < 5) {
				// Only pick from tiles that are still active
					List<string> activeTiles = new List<string>();
					for(int i = 0; i < r1Tiles.Count; i++) {
						if(i < r1States.Count && r1States[i] == true) { activeTiles.Add(r1Tiles[i]); }
					}

					if(activeTiles.Count > 0) {
						score++;
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
			} */
			_r1ScoreText.Text = score.ToString();
			_r1SmallScoreText.Text = score.ToString();
			_r1SmallScoreText2.Text = score.ToString();
		}
		// If round1Start = false: code here
	}

	// -------------------------------------------------------------
	//  ********************* START ROUND ONE *********************
	// -------------------------------------------------------------
	public void startRoundOne(bool strt)
	{
		round1Start = strt;
		round1Over = !strt;

		if (strt)
		{
			// Reset everything for a fresh start
			tilesSet = false;
			txtTriggered = false;
			score = 0;

			// Reset tile states
			for (int i = 0; i < r1States.Count; i++) { r1States[i] = false; }

			// Reconnect signal cleanly - unsub first to avoid double connections
			// Use functions so it won't give an error if not connected.
			DisconnectVideoSignal();
			ConnectVideoSignal();
			_r1VideoPlayer.Stream = introVideo;
			_r1ScoreText.Hide();
			_r1SmallScoreText.Hide();
			_r1SmallScoreText2.Hide();
			_r1ScoreText.Text = "0";
			_r1SmallScoreText.Text = "0";
			_r1SmallScoreText2.Text = "0";
		}
	}

	// -----------------------------------------------------------
	//  ********************* RESTART TILES *********************
	// -----------------------------------------------------------
	private void restartTiles()
	{
		// Send the data to the round 1 tiles to turn on. All tiles turn on at once.
		string toSend;
		int i = 0;
		GD.Print("Sending serial com to restart Round One's tiles:");
		foreach (var tile in r1Tiles)
		{
			// If tile is already on, don't resend.
			if (r1States[i]) { return; }

			toSend = tile + "255000000";
			if (serialCom == null)
			{
				GD.Print("Serial communication NOT CONNECTED in Round One's restartTiles function.");
			}
			serialCom.sendData(toSend);
			//delay(0.1)
			GD.Print(toSend);

			// Set current state of the tile we just sent data to is true / on.
			r1States[i] = true;
			i++;
		}
	}

	// -------------------------------------------------------
	//  ********************* SET TILES *********************
	// -------------------------------------------------------
	private void startRound1Tiles()
	{
		// Send the data to the round 1 tiles to turn on. All tiles turn on at once.
		string toSend;
		int i = 0;
		GD.Print("Sending serial com to Round One's tiles:");
		foreach (var tile in r1Tiles)
		{
			toSend = tile + "255000000";
			if (serialCom == null)
			{
				GD.Print("Serial communication NOT CONNECTED in Round One's startRound1Tiles function.");
			}
			serialCom.sendData(toSend);
			GD.Print(toSend);
			//create a small delay before sending next packet to prevent overflow
			//Sleep(25);

			System.Threading.Thread.Sleep(25);

			// Set current state of the tile we just sent data to is true / on.
			r1States[i] = true;
			i++;
		}
		tilesSet = true;
		score = 0;
		_r1ScoreText.Text = "0";
		_r1SmallScoreText.Text = "0";
		_r1SmallScoreText2.Text = "0";
		GD.Print(i + " tiles have been turned ON in Round 1's startRound1Tiles() function. Scores set to: " + _r1ScoreText.Text + _r1SmallScoreText.Text + _r1SmallScoreText2.Text); ;
		GD.Print("Round One tile list: " + string.Join(", ", r1Tiles));
	}

	// ------------------------------------------------------------
	//  ********************* VIDEO FINISHED *********************
	// ------------------------------------------------------------
	private void OnVideoFinished()
	{
		_r1VideoPlayer.Hide();
		if (tilesSet)
		{
			// We have already played both videos and the round is over.
			roundOneFinished();
			return;
		}
		// Switch to the gameplay video
		_r1VideoPlayer.Stream = gameplayVideo;
		_r1VideoPlayer.Play();
		_r1VideoPlayer.Show();

		var texture = _r1VideoPlayer.GetVideoTexture();
		if (texture != null) { txtPos = texture.GetSize(); }

		//startRound1Tiles();
		//GD.Print(r1States.Count + " states set in Round One.");
		//GD.Print("Tiles on: " + string.Join(", ", r1States));
	}

	// ------------------------------------------------------------
	//  ********************* GET TILE INDEX *********************
	// ------------------------------------------------------------
	private int getTileIndex(string tile)
	{
		int index = r1Tiles.IndexOf(tile);
		return index;
	}

	// ------------------------------------------------------------
	//  ********************* TURN TILES OFF *********************
	// ------------------------------------------------------------
	private bool allTilesOff(string tile)
	{
		int index = getTileIndex(tile);

		if (!r1States[index])
		{
			GD.Print(tile + " with index #" + index + " already OFF.");
			return false;
		}

		// Guard against tile not found
		if (index == -1)
		{
			GD.Print(tile + " NOT FOUND in r1Tiles list.");
			GD.Print("Current tile list: " + string.Join(", ", r1Tiles));
			return false;
		}

		// Guard against r1States being out of sync with r1Tiles
		if (index >= r1States.Count)
		{
			GD.Print("Index " + index + " is OUT OF RANGE for r1States (count: " + r1States.Count + ")");
			return false;
		}

		r1States[index] = false;
		//serialCom.sendData(tile + "000000000");
		//GD.Print("Serial com data sent to " + tile + ": " + tile + "000000000");
		GD.Print(tile + " with index #" + index + " turned OFF in Round One.");

		/*
		if (!r1States.Contains(true)) {
			GD.Print("ALL tiles turned OFF in Round One.");
			return true;
		}
		return false;
		*/
		return checkADA();
	}

	// --------------------------------------------------------------
	//  ********************* CHECK ADA TILES *********************
	// --------------------------------------------------------------
	private bool checkADA()
	{
		for (int i = 0; i < (r1States.Count - 5); i++)
		{
			GD.Print("Checking ADA states in Round One: " + string.Join(", ", r1States));
			if (r1States[i]) { return false; }
		}
		return true;
	}

	// ----------------------------------------------------------------
	//  ********************* ROUND ONE FINISHED *********************
	// ----------------------------------------------------------------
	private void roundOneFinished()
	{
		GD.Print("ROUND ONE FINISHED." + r1States.Count + " states set in Round One: " + string.Join(", ", r1States));

		round1Start = false;
		round1Over = true;
		tilesSet = false;
		txtTriggered = false;

		DisconnectVideoSignal();
		_r1VideoPlayer.Stop();
		_r1VideoPlayer.Hide();
		_r1ScoreText.Hide();
		_Score.Hide();
		_Puntaje.Hide();
	}

	// ------------------------------------------------------------
	//  ********************* CONNECT SIGNAL *********************
	// ------------------------------------------------------------
	private void ConnectVideoSignal()
	{
		if (!vidSigConnected)
		{
			_r1VideoPlayer.Finished += OnVideoFinished;
			vidSigConnected = true;
		}
	}

	// ---------------------------------------------------------------
	//  ********************* DISCONNECT SIGNAL *********************
	// ---------------------------------------------------------------
	private void DisconnectVideoSignal()
	{
		if (vidSigConnected)
		{
			_r1VideoPlayer.Finished -= OnVideoFinished;
			vidSigConnected = false;
		}
	}

	// -------------------------------------------------------------
	//  ********************* SHOW SCORE TEXT *********************
	// -------------------------------------------------------------
	private void ShowScoreText(bool small, bool vis)
	{
		txtTriggered = vis;
		smallTxtTrigger = small;

		if (txtTriggered && !smallTxtTrigger)
		{
			// Score is actively collecting input
			_r1ScoreText.GlobalPosition = new Vector2((txtPos.X / 2) - 240, (txtPos.Y / 4) - 10);
			_r1ScoreText.Show();
			_Score.Show();
			_Puntaje.Show();
		}
		else if (!txtTriggered && !small)
		{
			// Round One game is over. Turn all remaining tiles off.
			//GD.Print("Turning OFF remaining tiles in Round One...");
			TilesOff();
			_r1ScoreText.Hide();
			_Score.Hide();
			_Puntaje.Hide();
		}
		else if (txtTriggered && small)
		{
			_r1SmallScoreText.GlobalPosition = new Vector2(1071, 340);
			_r1SmallScoreText.Show();
			_r1SmallScoreText2.GlobalPosition = new Vector2(1034, 445);
			_r1SmallScoreText2.Show();
		}
		else if (!txtTriggered && small)
		{
			_r1SmallScoreText.Hide();
			_r1SmallScoreText2.Hide();
		}
	}

	public bool getRound1Start()
	{
		return round1Start;
	}

	public bool isRound1Over()
	{
		return round1Over;
	}

	public void resetRound1Score()
	{
		score = 0;
	}

	public int round1Score()
	{
		return score;
	}

	public void TilesOff()
	{
		// Turn off all of the tiles.
		foreach (var tile in r1Tiles) { serialCom.sendData(tile + "000000000"); }
	}
}
