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
	public int  totalScore;
	public bool gameStarted;
	public bool round1Complete;
	public bool round2Complete;
	public bool resultsComplete;

	private bool idleStarted		  = false;
	private bool round1Started        = false;
	private bool round1ScoreCollected = false;
	private bool round2Started        = false;
	private bool round2ScoreCollected = false;
	private bool resultsStarted       = false;

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
		// Set to Fullscreen Mode & hide mouse
		DisplayServer.WindowSetMode(DisplayServer.WindowMode.Fullscreen);
		Input.MouseMode = Input.MouseModeEnum.Hidden;

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
		// ------------------------------------------------------------------
		//  ********************* IDLE SCREEN PRE-GAME *********************
		// ------------------------------------------------------------------
		if(!gameStarted && !round1Complete && !round2Complete && !resultsComplete) {
			if(idleNode == null) {
				GD.Print("Idle Node is null in Game Controller's _Process function.");
			}

			if(!idleStarted) {
				printHeader("IDLE");
				GD.Print("Waiting for game to start...");
				idleNode.Show();
				idleStarted = true;
			}

			// Check for a serial message that a button has been pushed
			if(!gameStarted) { gameStarted = idleScript.isGameStarted(); }
			if (gameStarted) { GD.Print("Game started! End of Idle script, moving on to Round One..."); }
		}

		// --------------------------------------------------------
		//  ********************** ROUND ONE *********************
		// --------------------------------------------------------
		if(gameStarted && !round1Complete && !round2Complete && !resultsComplete) {
			if(round1Node == null) { GD.Print("Round One Node is null in Game Controller's _Process function."); }

			if(!round1Complete) {
				idleNode.Hide();
				round1Node.Show();

				if(!round1Started) {
					printHeader("ROUND ONE");
					round1Script.startRoundOne(true);
					round1Started = round1Script.getRound1Start();
					GD.Print("Round One started in Game Controller's _Process function.");
				}

				round1Complete = round1Script.isRound1Over();

				//GD.Print("Waiting for round one to be over in Game Controller's _Process function...");
				if(round1Complete && !round1ScoreCollected) {
					round1ScoreCollected = true;
   					totalScore = round1Script.round1Score();
					GD.Print("Round One completed. Score: " + totalScore);
				}
			}
		}

		// -------------------------------------------------------
		//  ********************* ROUND TWO *********************
		// -------------------------------------------------------
		if(gameStarted && round1Complete && !round2Complete && !resultsComplete) {
			if(round2Node == null) { GD.Print("Round Two Node is null in Game Controller's _Process function."); }

			if(!round2Complete) {
				round1Node.Hide();
				round2Node.Show();

				if(!round2Started) {
					printHeader("ROUND TWO");
					round2Script.startRoundTwo(true);
					round2Started = round2Script.getRound2Start();
					GD.Print("Round Two started in Game Controller's _Process function.");
				}

				round2Complete = round2Script.isRound2Over();

				//GD.Print("Waiting for round one to be over in Game Controller's _Process function...");
				if(round2Complete && !round2ScoreCollected) {
					round2ScoreCollected = true;
   					totalScore += round2Script.round2Score();
					GD.Print("Round Two completed. Score from Round Two: " + round2Script.round2Score());
					GD.Print("Total score: " + totalScore);
				}
			}
		}

		// -----------------------------------------------------
		//  ********************* RESULTS *********************
		// -----------------------------------------------------
		if(gameStarted && round1Complete && round2Complete && !resultsComplete) {
			if(resultsNode == null) { GD.Print("Results Node is null in Game Controller's _Process function."); }

			round2Node.Hide();
			resultsNode.Show();

   		 	if(!resultsStarted) {
				printHeader("RESULTS");
				resultsStarted = true;
				resultsScript.resetResults();        // reset before setting score
				resultsScript.setTotalScore(totalScore);
				GD.Print("Results started in GameController's _Process function. Total score: " + totalScore);
			}

			resultsComplete = resultsScript.getResultsFinished();
		}

		// ---------------------------------------------------
		//  ********************* RESET *********************
		// ---------------------------------------------------
		if(gameStarted && round1Complete && round2Complete && resultsComplete) {
			restartGame();
		}
	}

	public void restartGame() {
		printHeader("GAME RESTART");
		gameStarted = false;
		totalScore  = 0;
		GD.Print("Game restarting in GameController's restartGame(). Game started: " + gameStarted + ". Total score: " + totalScore + ".");

		idleStarted = false;
		GD.Print("Reset! Idle started: " + idleStarted);

		round1Complete       = false;
		round1ScoreCollected = false;
		round1Started        = false;
		round1Script.resetRound1Score();
		GD.Print("Reset! Round One score: " + round1Script.round1Score());

		round2Complete       = false;
		round2ScoreCollected = false;
		round2Started        = false;
		round2Script.resetRound2Score();
		GD.Print("Reset! Round One score: " + round2Script.round2Score());

		resultsComplete = false;
		resultsStarted  = false;
		resultsScript.resetResults();
		GD.Print("Reset! Results script total score: " + resultsScript.getTotalScore());

		idleNode.Hide();
		round1Node.Hide();
		round2Node.Hide();
		resultsNode.Hide();
	}

	private void printHeader(string txtToPrint) {
		GD.Print("--------------------------------------");
		GD.Print("***** " + txtToPrint + " *****");
		GD.Print("--------------------------------------");
	}
}
