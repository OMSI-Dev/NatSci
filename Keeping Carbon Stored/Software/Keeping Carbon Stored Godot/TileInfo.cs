/*
* This script should be autoloaded into the scene.
* It needs to be used by everything throughout the game.
* Set this in Project Settings, Global tab and add this script
* to the global path. Then it can be called as a vairable just
* like any object.
*/

using Godot;
using System;
using System.Collections.Generic;

public partial class TileInfo : Node
{
	List<string> round1Tiles = new List<string> {"A2", "A4", "B1", "B3", "B5", 
												"C2", "C4", "D1", "D3", "D5", 
												"E2", "E4", "F1", "F3", "F5", 
												"G2", "G4"};
	List<bool> round1States = new List<bool>();
	
	List<string> round2Tiles = new List<string> {"A1", "A3", "A5", "B2", "B4", 
												"C1", "C3", "C5", "D2", "D4", 
												"E1", "E3", "E5", "F2", "F4", 
												"G1", "G3", "G5"};					
	List<bool> round2States = new List<bool>();

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		// All tiles initially turned off.
		foreach (var t in round1Tiles)
		{	
			round1States.Add(false);
		}
		foreach (var t in round2Tiles)
		{	
			round2States.Add(false);
		}
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
	}
	
	public List<string> getRound1Tiles() {
		return round1Tiles;
	}
	
	public List<bool> getRound1States() {
		return round1States;
	}
	
	public List<string> getRound2Tiles() {
		return round2Tiles;
	}
	
	public List<bool> getRound2States() {
		return round2States;
	}
	
	public void updateRound1States(List<bool> newR1States) {
		round1States = newR1States;
	}
	
	public void updateRound2States(List<bool> newR2States) {
		round2States = newR2States;
	}
}
