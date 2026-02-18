using Godot;
using System;

public partial class GameController : Node2D
{
	public int totalScore;
	public bool gameStarted;
	public bool round1Complete;
	public bool round2Complete;
	public bool resultsComplete;
	
	public SerialCom serCom;
	
	private Node2D idleNode;
	private Idle idleScript;
	
	private Node2D round1Node;
	private Round1 round1Script;
	
	private Node2D round2Node;
	private Round2 round2Script;
	
	private Node2D resultsNode;
	private Results resultsScript;
	
	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		totalScore = 0;
		gameStarted = false;
		round1Complete = false;
		round2Complete = false;
		resultsComplete = false;
		
		serCom = GetNode<SerialCom>("/root/SerialCom");
		idleNode = GetNode<Node2D>("Idle");
		//Idle idleScript = idleNode as Idle;
		idleScript = GetNode<Idle>("Idle");
		round1Node = GetNode<Node2D>("Round1");
		//Round1 round1Script = round1Node as Round1;
		round1Script = GetNode<Round1>("Round1");
		round2Node = GetNode<Node2D>("Round2");
		//Round2 round2Script = round2Node as Round2;
		round2Script = GetNode<Round2>("Round2");
		resultsNode = GetNode<Node2D>("Results");
		//Results resultsScript = resultsNode as Results;
		resultsScript = GetNode<Results>("Results");
		
		if(idleNode != null) {
			idleNode.Hide();
		} else if(idleNode == null) {
			GD.Print("Problem with idle node in _Ready.");
		}
		
		if(round1Node != null) {
			round1Node.Hide();
		} else if(round1Node == null) {
			GD.Print("Problem with round 1 node in _Ready.");
		}
		
		if(round2Node != null) {
			round2Node.Hide();
		} else if(round2Node == null) {
			GD.Print("Problem with round 2 node in _Ready.");
		}
		
		if(resultsNode != null) {
			resultsNode.Hide();
		} else if(resultsNode == null) {
			GD.Print("Problem with results node in _Ready.");
		}
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(double delta)
	{
		// ************* IDLE SCREEN PRE-GAME ******************
		if(!gameStarted && !round1Complete && !round2Complete && !resultsComplete) {
			// If round1Complete, round2Complete, and resultsScreen = false and 
			// gameStarted = false, play idle screen script
			if(idleNode == null) {
				GD.Print("Idle Node is null in Game Controller's _Process function.");
			}
			
			// function checks for a serial message that a button has been pushed
			if(!gameStarted) {
				idleNode.Show();
				gameStarted = idleScript.isGameStarted();
				if(!gameStarted) {
					GD.Print("Waiting for game to start...");
				} else if (gameStarted) {
					GD.Print("Game started! End of Idle script, moving on to Round 1...");
				}
			}
		}
		
		// ************* ROUND ONE ******************
		if(gameStarted && !round1Complete && !round2Complete && !resultsComplete) {
			// If round one isn't complete and we get a message from serial
			// that a button has been pushed, mark idleScreen = false and
			// call round 1 script 
			
			// Get bool from round 1 script saying that it's completed
			// Get int from total score from round one (same as above?)
			// roundOneComplete = true;
			
			if(round1Node == null) {
				GD.Print("Round 1 Node is null in Game Controller's _Process function.");
			}
			//GD.Print("In Round One if statement in Game Controller's _Process function.");
			
			if(!round1Complete) {
				// Do round 1
				idleNode.Hide();
				round1Node.Show();
				
				round1Complete = round1Script.isRound1Over();
				
				if(!round1Script.getRound1Start() && !round1Complete) {
					round1Script.startRoundOne(true);
					GD.Print("Round One set to start in Game Controller's _Process function.");;
				}
				
				if(!round1Complete) {
					GD.Print("Waiting for round one to be over...");
				} else if (round1Complete) {
					GD.Print("Round one completed in Game Controller's _Process function.");
					totalScore = round1Script.round1Score();
				}
			}
		}
		
		// ************* ROUND TWO ******************
		if(gameStarted && round1Complete && !round2Complete && !resultsComplete) {
			// If round one is complete but round two isn't,
			// start round 2
			
			// Get bool from round 2 script saying it's completed
			// Get int from total score from round two (same as above?)
			// roundTwoComplete = true;
			// totalScore += round1score + round2score
			if(round2Node == null) {
				GD.Print("Round 2 Node is null in Game Controller's _Process function.");
			}
			//GD.Print("In Round Two if statement in Game Controller's _Process function.");
			
			if(!round2Complete) {
				// Do round 2
				round1Node.Hide();
				round2Node.Show();
				
				if(!round2Script.getRound2Start()) {
					round2Script.startRoundTwo(true);
					GD.Print("Round Two set to start in Game Controller's _Process function.");;
				}
				
				round2Complete = round2Script.isRound2Over();
				
				if(!round2Complete) {
					GD.Print("Waiting for round two to be over...");
				} else if (round2Complete) {
					GD.Print("Round two completed in Game Controller's _Process function.");
					totalScore += round2Script.round2Score();
				}
			}
		}
	 	
		// ************* RESULTS ******************
		if(gameStarted && round1Complete && round2Complete && !resultsComplete) {
			// If round one is complete and round two is complete,
			// pass the total score to the finished / final screen
			
			if(resultsNode == null) {
				GD.Print("Results Node is null in Game Controller's _Process function.");
			}
			//GD.Print("In Results if statement in Game Controller's _Process function.");
			
			if(!resultsComplete){
				round2Node.Hide();
				resultsNode.Show();
			}
			
			// Do results screen
			if(resultsScript.getTotalScore() == 0 || resultsScript.getTotalScore() == null) {
				resultsScript.setTotalScore(totalScore);
			}
		
		// After results screen comes back as completed, mark resultsScreen completed
		resultsComplete = true;
		}
		
		// ************* RESET ******************
		// If resultsScreen completed: mark round1Completed, round2Completed, and 
		// results screen completed = false and idleScreen = true
		// reset score in all scripts and in game controller script (this one)
		if(gameStarted && round1Complete && round2Complete && resultsComplete) {
			restartGame();
		}
	}
	
	public void restartGame() {
		gameStarted = false;
		totalScore = 0;
		GD.Print("Game starting over...");
		
		round1Complete = false;
		round1Script.resetRound1Score();
		GD.Print("Reset! Round 1 score: " + round1Script.round1Score());
		
		round2Complete = false;
		round2Script.resetRound2Score();
		GD.Print("Reset! Round 2 score: " + round2Script.round2Score());
		
		resultsComplete = false;
		resultsScript.setTotalScore(0);
		GD.Print("Reset! Results script total score: " + resultsScript.getTotalScore());
	}
}
