using Godot;
using System;

public partial class Results : Node2D
{
	private int totalScore;
	
	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		totalScore = 0;
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
	}
	
	public void setTotalScore(int score) {
		totalScore = score;
		GD.Print("Total Score: " + totalScore);
	}
	
	public int getTotalScore() {
		return totalScore;
	}
}
