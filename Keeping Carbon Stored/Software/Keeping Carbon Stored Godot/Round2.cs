using Godot;
using System;
using System.Collections.Generic;

public partial class Round2 : Node2D
{
	string serialData = "";
	List<string> dataList = new List<string>();
	//List<string> round1Tiles = new List<string> {"A2", "A4", "B1", "B3", "B5", 
	//											"C2", "C4", "D1", "D3", "D5", 
	//											"E2", "E4", "F1", "F3", "F5", 
	//											"G2", "G4"};
	//string[] finishedTiles;
	List<string> r1Tiles = new List<string>();
	List<string> r2Tiles = new List<string>();
	List<bool> r1States = new List<bool>();
	List<bool> r2States = new List<bool>();
	
	private int score = 0;
	private bool round2Over = false;
	private bool round2Start = false;
	
	private int timesButtonPushed = 0;
	
	// Access global / root script.
	SerialCom serialCom;
	TileInfo tileInfo;
	
	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		serialCom = GetNode<SerialCom>("/root/SerialCom");
		tileInfo = GetNode<TileInfo>("/root/TileInfo");
		
		//r1Tiles = tileInfo.getRound1Tiles();
		r2Tiles = tileInfo.getRound2Tiles();
		//r1States = tileInfo.getRound1States();
		r2States = tileInfo.getRound2States();
		// Verify that the autoload is in the global root folder.
		//if (HasNode("/root"))
			//GD.Print("Root exists");
//
		//var auto = GetNodeOrNull<Node>("/root/SerialCom");
		//GD.Print(auto == null ? "Autoload NOT found" : "Autoload FOUND");
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{	
		if(round2Start) {
			startRound2Tiles();
			//GD.Print("Round One started...");
			/* // ***** Test Code *****
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
			} */
		
			serialData = serialCom.getRawData();
		
			if(serialData.Length > 0) {
				//GD.Print("Data from inside Round2: " + serialData);
				dataList = new List<string>(serialCom.getSplit());
			}
		
			if(dataList.Count > 1) {
				string tile = dataList[0] + dataList[1];
				//GD.Print(tile + " was pressed.");
				
				string time = dataList[2] + dataList[3] + dataList[4] + dataList[5];
				//GD.Print("Time was " + time);
				int toAdd;
				try {
					toAdd = int.Parse(time);
					//GD.Print("toAdd: " + toAdd);
					score += toAdd;
					GD.Print("Round Two Current Score: " + score);
					//timesButtonPushed++;
					//if(timesButtonPushed >= 3) {
					//	roundTwoFinished();
					//}
					
					// Update tiles that have been pushed and check for any still active.
					bool anyTilesLeft = updateRound2Tiles(tile);
					if(!anyTilesLeft) {
						roundTwoFinished();
					}
				}
				catch (FormatException e)
				{
					GD.Print(e.Message);
				}
			}
			// Once all tiles have been lit up and pressed or timed out,
			// round2Over = true and score = the total score
			// roundTwoStart = false
		}
		// If round2Start = false
	}
	
	private void roundTwoFinished() {
		round2Start = false;
		round2Over = true;
	}
	
	public void startRoundTwo(bool strt) {
		round2Start = strt;
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
	
	private void startRound2Tiles() {
		// Send the data to the round 2 tiles to turn on.
		string toSend;
		// All tiles turn on at once. Just get this working first.
		foreach(tile in r2Tiles) {
			toSend = tile + "255000000";
			SerialCom.sendData(toSend);
		}
	}
	
	private bool updateRound2Tiles(string tile) {
		// Send the data to the round 2 tiles to turn on.
		string toSend;
		// All tiles turn on at once. Just get this working first. 
		int i = 0;
		foreach(tile in r2Tiles) {
			toSend = tile + "000255000";
			SerialCom.sendData(toSend);
			// Say that the current state of the tile we just sent data to is true / on.
			r2States[i] = true;
			i++;
		}
	}
}
