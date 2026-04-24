/*
* Keeping Carbon Stored - RESULTS
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Show total score from game.
*/

using Godot;
using System;
using System.Collections.Generic;

public partial class Results : Node2D
{
	private int totalScore;
	private bool resultsFinished = false;
	private bool resultsStarted  = false;
	private bool txtTriggered    = false;
	private bool vidSigConnected = false;
	private Vector2 txtPos       = new Vector2(0.0f, 0.0f);

	private VideoStreamPlayer resultsVideo;
	private RichTextLabel finalScoreText;

	private float showTriggerTime = 1.5f;
	private float hideTriggerTime = 5f;

	SerialCom serialCom;
	TileInfo tileInfo;
	List<string> r1Tiles = new List<string>();
	List<string> r2Tiles = new List<string>();

	public override void _Ready()
	{
		resultsVideo   = GetNode<VideoStreamPlayer>("ResultsVideoPlayer");
		finalScoreText = GetNode<RichTextLabel>("CanvasLayer/FinalScore");
		serialCom      = GetNode<SerialCom>("/root/SerialCom");
		tileInfo       = GetNode<TileInfo>("/root/TileInfo");

		totalScore = 0;
		r1Tiles    = tileInfo.getRound1Tiles();
		r2Tiles    = tileInfo.getRound2Tiles();

		finalScoreText.Hide();
	}

	public override void _Process(double delta)
	{
		if(resultsVideo == null) {
			GD.Print("Results video failed to load in Results script.");
			return;
		}

		if(!IsVisibleInTree()) { return; }

		if(!resultsStarted && !resultsFinished) {
			resultsStarted = true;
			ConnectVideoSignal();
			resultsVideo.Show();
			resultsVideo.Play();

			resultsAnimation();

			var texture = resultsVideo.GetVideoTexture();
			if(texture != null) { txtPos = texture.GetSize(); }
		}

		// Check if video is playing and target time is reached
		if (resultsStarted && !txtTriggered && resultsVideo.IsPlaying() && resultsVideo.StreamPosition >= showTriggerTime)
		{
			if(finalScoreText == null) { GD.Print("Text node is null in Results's _Process function."); }
			ShowScoreText(true);
		}

		if(resultsStarted && txtTriggered && resultsVideo.IsPlaying() && resultsVideo.StreamPosition >= hideTriggerTime) {
			//GD.Print("Turning off text at the right spot in the video.");
			ShowScoreText(false);
		}
	}

	public bool getResultsFinished() {
		return resultsFinished;
	}

	private void OnVideoFinished() {
		GD.Print("Results video finished.");
		resultsFinished = true;
		DisconnectVideoSignal();
		resultsVideo.Stop();
		resultsVideo.Hide();
		finalScoreText.Hide();
	}

	private void ShowScoreText(bool vis) {
		txtTriggered = vis;
		if(txtTriggered) {
			//finalScoreText.GlobalPosition = new Vector2((txtPos.X / 2) - 240, txtPos.Y / 4);
			finalScoreText.GlobalPosition = new Vector2(700, 270);
			finalScoreText.Show();
		} else {
			finalScoreText.Hide();
		}
	}

	public void resetResults() {
		DisconnectVideoSignal();
		resultsStarted  = false;
		resultsFinished = false;
		vidSigConnected = false;
		totalScore      = 0;
	}

	public void setTotalScore(int score) {
		totalScore = score;
		finalScoreText.Text = totalScore.ToString();
		GD.Print("Total Score from results node: " + totalScore);
	}

	public int getTotalScore() {
		return totalScore;
	}

	private void resultsAnimation() {
		for(int i = 0; i < 3; i++) {
			foreach(var tile in r1Tiles) {
				serialCom.sendData(tile + "000255000");
			}
			foreach(var tile in r2Tiles) {
				serialCom.sendData(tile + "000255000");
			}
			foreach(var tile in r1Tiles) {
				serialCom.sendData(tile + "000000000");
			}
			foreach(var tile in r2Tiles) {
				serialCom.sendData(tile + "000000000");
			}
		}
		GD.Print("Results animation finished.");
	}

	private void ConnectVideoSignal() {
		if(!vidSigConnected) {
			resultsVideo.Finished += OnVideoFinished;
			vidSigConnected = true;
		}
	}

	private void DisconnectVideoSignal() {
		if(vidSigConnected) {
			resultsVideo.Finished -= OnVideoFinished;
			vidSigConnected = false;
		}
	}
}
