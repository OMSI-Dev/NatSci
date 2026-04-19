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

	public override void _Ready()
	{
		totalScore = 0;
	}

	public override void _Process(double delta)
	{
	}

	public void setTotalScore(int score) {
		totalScore = score;
		GD.Print("Total Score from results node: " + totalScore);
	}

	public int getTotalScore() {
		return totalScore;
	}
}
