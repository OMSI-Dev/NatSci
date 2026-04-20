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

	private VideoStreamPlayer resultsVideo;

	public override void _Ready()
	{
		totalScore   = 0;
		resultsVideo = GetNode<VideoStreamPlayer>("ResultsVideo");

		resultsVideo.Finished += OnVideoFinished;
	}

	public override void _Process(double delta)
	{
		if(!resultsVideo.IsPlaying()) {
			resultsVideo.Play();
			resultsFinished = false;
			}
	}

	public void setTotalScore(int score) {
		totalScore = score;
		GD.Print("Total Score from results node: " + totalScore);
	}

	public int getTotalScore() {
		return totalScore;
	}

	public bool getResultsFinished() {
		return resultsFinished;
	}

	private void OnVideoFinished() {
		resultsFinished = true;
	}
}
