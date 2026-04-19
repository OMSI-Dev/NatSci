/*
* Keeping Carbon Stored - GAME CONTROLLER
* Nat Sci Hall - OMSI
* Calico Rose
* Purpose: Control the current game. Recieve data when time to start a new game. Track when rounds are over and
* when to start the next round. Track the total score and when to show the results screen.
*/

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

	public override void _Ready()
	{
		totalScore      = 0;
		gameStarted     = false;
		round1Complete  = false;
		round2Complete  = false;
		resultsComplete = false;

		serCom        = GetNode<SerialCom>("/root/SerialCom");
		idleNode      = GetNode<Node2D>("Idle");
		idleScript    = GetNode<Idle>("Idle");
		round1Node    = GetNode<Node2D>("Round1");
		round1Script  = GetNode<Round1>("Round1");
		round2Node    = GetNode<Node2D>("Round2");
		round2Script  = GetNode<Round2>("Round2");
		resultsNode   = GetNode<Node2D>("Results");
		resultsScript = GetNode<Results>("Results");

		// Load all nodes and initially hide.
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

	public override void _Process(double delta)
	{
		// ********************* IDLE SCREEN PRE-GAME *********************
		if(!gameStarted && !round1Complete && !round2Complete && !resultsComplete) {
			if(idleNode == null) {
				GD.Print("Idle Node is null in Game Controller's _Process function.");
			}

			// Check for a serial message that a button has been pushed
			if(!gameStarted) {
				idleNode.Show();
				gameStarted = idleScript.isGameStarted();
				if(!gameStarted) {
					GD.Print("Waiting for someone to start the game...");
				} else if (gameStarted) {
					GD.Print("Game started! End of Idle script, moving on to Round 1...");
				}
			}
		}

		// ********************** ROUND ONE *********************
		if(gameStarted && !round1Complete && !round2Complete && !resultsComplete) {
			if(round1Node == null) { GD.Print("Round 1 Node is null in Game Controller's _Process function."); }

			if(!round1Complete) {
				idleNode.Hide();
				round1Node.Show();

				if(!round1Script.getRound1Start()) {
					round1Script.startRoundOne(true);
					GD.Print("Round One set to start in Game Controller's _Process function.");;
				}

				GD.Print("Waiting for round one to be over in Game Controller's _Process function...");
				round1Complete = round1Script.isRound1Over();
			}
			GD.Print("Round one completed in Game Controller's _Process function.");
			totalScore = round1Script.round1Score();
		}

		// ********************* ROUND TWO *********************
		if(gameStarted && round1Complete && !round2Complete && !resultsComplete) {
			if(round2Node == null) { GD.Print("Round 2 Node is null in Game Controller's _Process function."); }

			if(!round2Complete) {
				round1Node.Hide();
				round2Node.Show();

				if(!round2Script.getRound2Start()) {
					round2Script.startRoundTwo(true);
					GD.Print("Round Two set to start in Game Controller's _Process function.");;
				}

				round2Complete = round2Script.isRound2Over();
			}
			GD.Print("Round two completed in Game Controller's _Process function.");
			totalScore += round2Script.round2Score();
		}

		// ********************* RESULTS *********************
		if(gameStarted && round1Complete && round2Complete && !resultsComplete) {
			if(resultsNode == null) {
				GD.Print("Results Node is null in Game Controller's _Process function.");
			}
			//GD.Print("In Results if statement in Game Controller's _Process function.");

			if(!resultsComplete){
				round2Node.Hide();
				resultsNode.Show();
			}

			if(resultsScript.getTotalScore() == 0) {
				resultsScript.setTotalScore(totalScore);
			}

		resultsComplete = true;
		}

		// ********************* RESET *********************
		if(gameStarted && round1Complete && round2Complete && resultsComplete) {
			restartGame();
		}
	}

	public void restartGame() {
		gameStarted = false;
		totalScore  = 0;
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
