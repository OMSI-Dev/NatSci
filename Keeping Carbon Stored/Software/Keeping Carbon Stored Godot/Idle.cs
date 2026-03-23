using Godot;
using System;

public partial class Idle : Node2D
{
	public SerialCom serCom;
	
	private bool startGame;
	
	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		startGame = false;
		
		serCom = GetNode<SerialCom>("/root/SerialCom");
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
		if(!startGame) {
			string[] newData = serCom.getSplit();
			//GD.Print(newData);
			//GD.Print(newData[0]);
			if(newData != null) {
				if(newData[0] != "0") {
					GD.Print("Recieved Serial data in Idle script. startGame is true.");
					startGame = true;
				}
			}
		}
	}
	
	public bool isGameStarted() {
		return startGame;
	}
}
