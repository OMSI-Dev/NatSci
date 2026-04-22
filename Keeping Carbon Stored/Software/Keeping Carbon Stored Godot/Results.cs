/*
* Keeping Carbon Stored - RESULTS
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Show total score from game.
*/

using Godot;
using System;

public partial class Results : Node2D
{
	private int totalScore;
	private bool resultsFinished = false;
	private bool resultsStarted  = false;

	private VideoStreamPlayer resultsVideo;
	private RichTextLabel finalScoreText;

	public override void _Ready()
	{
		totalScore     = 0;
		resultsVideo   = GetNode<VideoStreamPlayer>("ResultsVideoPlayer");
		finalScoreText = GetNode<RichTextLabel>("CanvasLayer/FinalScore");

		resultsVideo.Finished += OnVideoFinished;
		finalScoreText.Hide();
	}

	public override void _Process(double delta)
	{
		if(resultsVideo == null) {
			GD.Print("Results video failed to load.");
			return;
		}

		if(!resultsStarted && !resultsFinished) {
			resultsStarted = true;
			resultsVideo.Show();
			resultsVideo.Play();
		}
	}

	public bool getResultsFinished() {
		return resultsFinished;
	}

	private void OnVideoFinished() {
		GD.Print("Results video finished.");
		resultsFinished = true;
		resultsVideo.Stop();
		resultsVideo.Hide();
		finalScoreText.Hide();
	}


	public void resetResults() {
		resultsStarted  = false;
		resultsFinished = false;
		totalScore      = 0;
	}

	public void setTotalScore(int score) {
		totalScore = score;
		GD.Print("Total Score from results node: " + totalScore);
	}

	public int getTotalScore() {
		return totalScore;
	}
}
