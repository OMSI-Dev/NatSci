using Godot;
using System;
using System.Collections.Generic;

/*
* Game state machine. Attached to the root node of Main.tscn.
*
* Flow:
*   Collecting -> (all 3 pieces registered) -> Transition -> Results
*   Removing any piece returns to Collecting.
*
* Pieces arrive from the SerialCom autoload (Teensy RFID readers).
* Piece identity comes from the Hex Code key; the final outcome comes
* from the Truth Table (both loaded by the SheetManager autoload).
*
* The frontend should connect to the signals below to drive visuals:
*   PieceRegistered / PieceCleared  - update slot highlights
*   ResultsPhaseStarted             - play the transition animation
*   ResultsReady(outcome)           - populate and show the results screen
*   GameReset                       - return to the main gameplay screen
*   LanguageChanged(spanish)        - swap displayed language
*/

public partial class GameController : Node2D
{
	public enum GamePhase { Collecting, Transition, Results }

	[Signal] public delegate void PieceRegisteredEventHandler(int slot, string category, string subcategory, string item);
	[Signal] public delegate void PieceClearedEventHandler(int slot, string category);
	[Signal] public delegate void ResultsPhaseStartedEventHandler();
	[Signal] public delegate void ResultsReadyEventHandler(Godot.Collections.Dictionary outcome);
	[Signal] public delegate void GameResetEventHandler();
	[Signal] public delegate void LanguageChangedEventHandler(bool spanish);

	// How long the transition/loading screen shows before results appear.
	[Export] public double TransitionSeconds { get; set; } = 3.0;

	public GamePhase Phase { get; private set; } = GamePhase.Collecting;
	public bool SpanishActive { get; private set; } = false;

	// Set while in the Results phase.
	public Outcome CurrentOutcome { get; private set; }
	public OrgInfo SelectedLocalOrg { get; private set; }

	// Registered piece per reader slot (1..3).
	private readonly Dictionary<int, PieceInfo> _slots = new();

	private readonly Random _rng = new();
	private SceneTreeTimer _transitionTimer;

	public override void _Ready()
	{
		var serial = GetNodeOrNull<SerialCom>("/root/SerialCom");
		if (serial != null) {
			serial.PiecePlaced += OnPiecePlaced;
			serial.PieceRemoved += OnPieceRemoved;
			serial.LanguagePressed += OnLanguagePressed;
		} else {
			GD.PrintErr("[GameController] SerialCom autoload not found; no input will arrive.");
		}
	}

	// ------------------------------------------------------------ piece events

	private void OnPiecePlaced(int slot, int hexId)
	{
		PieceInfo piece = SheetManager.Instance?.LookupHex(hexId);
		if (piece == null) {
			GD.PrintErr($"[GameController] Unknown hex 0x{hexId:X2} on slot {slot}; ignoring.");
			return;
		}

		_slots[slot] = piece;
		GD.Print($"[GameController] Slot {slot}: {piece.Category} / {piece.Item}");
		EmitSignal(SignalName.PieceRegistered, slot, piece.Category, piece.Subcategory, piece.Item);

		if (Phase == GamePhase.Collecting && AllPiecesRegistered()) {
			StartResultsPhase();
		}
	}

	private void OnPieceRemoved(int slot)
	{
		if (!_slots.TryGetValue(slot, out PieceInfo removed)) {
			return;
		}

		_slots.Remove(slot);
		GD.Print($"[GameController] Slot {slot} cleared ({removed.Category}).");
		EmitSignal(SignalName.PieceCleared, slot, removed.Category);

		// Removing a piece during transition/results resets the game.
		if (Phase != GamePhase.Collecting) {
			ResetToCollecting();
		}
	}

	private void OnLanguagePressed()
	{
		SpanishActive = !SpanishActive;
		GD.Print($"[GameController] Language: {(SpanishActive ? "Spanish" : "English")}");
		EmitSignal(SignalName.LanguageChanged, SpanishActive);
	}

	// ----------------------------------------------------------- state machine

	// True when all three readers hold a piece and the pieces cover
	// exactly the three categories (Interest, Topic, Group).
	private bool AllPiecesRegistered()
	{
		if (_slots.Count != 3) {
			return false;
		}
		var categories = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
		foreach (PieceInfo piece in _slots.Values) {
			categories.Add(piece.Category);
		}
		return categories.Contains("Interest") && categories.Contains("Topic") && categories.Contains("Group");
	}

	private PieceInfo GetPieceByCategory(string category)
	{
		foreach (PieceInfo piece in _slots.Values) {
			if (string.Equals(piece.Category, category, StringComparison.OrdinalIgnoreCase)) {
				return piece;
			}
		}
		return null;
	}

	private async void StartResultsPhase()
	{
		Phase = GamePhase.Transition;
		GD.Print("[GameController] All pieces registered; starting results phase.");
		EmitSignal(SignalName.ResultsPhaseStarted);

		_transitionTimer = GetTree().CreateTimer(TransitionSeconds);
		await ToSignal(_transitionTimer, SceneTreeTimer.SignalName.Timeout);
		_transitionTimer = null;

		// A piece may have been removed while the transition played.
		if (Phase != GamePhase.Transition) {
			return;
		}

		ShowResults();
	}

	private void ShowResults()
	{
		PieceInfo interest = GetPieceByCategory("Interest");
		PieceInfo topic = GetPieceByCategory("Topic");
		PieceInfo group = GetPieceByCategory("Group");

		Outcome outcome = SheetManager.Instance?.FindOutcome(topic.Item, group.Item, interest.Item);
		if (outcome == null) {
			GD.PrintErr($"[GameController] No Truth Table row for " +
				$"Topic='{topic.Item}', Group='{group.Item}', Interest='{interest.Item}'.");
			ResetToCollecting();
			return;
		}

		CurrentOutcome = outcome;
		SelectedLocalOrg = outcome.LocalOrgs.Count > 0
			? outcome.LocalOrgs[_rng.Next(outcome.LocalOrgs.Count)]
			: new OrgInfo();
		Phase = GamePhase.Results;

		GD.Print($"[GameController] Outcome: national='{outcome.NationalOrg.Name}', " +
			$"local='{SelectedLocalOrg.Name}'.");

		// Generate the QR codes for the two org links, if the QR node exists.
		var qr = GetNodeOrNull<QRGenerator>("QRNode");
		qr?.SetUrls(outcome.NationalOrg.Link, SelectedLocalOrg.Link);

		EmitSignal(SignalName.ResultsReady, BuildOutcomeDict());
	}

	private void ResetToCollecting()
	{
		Phase = GamePhase.Collecting;
		CurrentOutcome = null;
		SelectedLocalOrg = null;
		GD.Print("[GameController] Reset to collecting.");
		EmitSignal(SignalName.GameReset);
	}

	private Godot.Collections.Dictionary BuildOutcomeDict()
	{
		return new Godot.Collections.Dictionary {
			{ "topic", CurrentOutcome.Topic },
			{ "group", CurrentOutcome.Group },
			{ "interest_subcategory", CurrentOutcome.InterestSubcategory },
			{ "interest_item", CurrentOutcome.InterestItem },
			{ "national_name", CurrentOutcome.NationalOrg.Name },
			{ "national_description", CurrentOutcome.NationalOrg.Description },
			{ "national_description_spanish", CurrentOutcome.NationalOrg.DescriptionSpanish },
			{ "national_link", CurrentOutcome.NationalOrg.Link },
			{ "local_name", SelectedLocalOrg.Name },
			{ "local_description", SelectedLocalOrg.Description },
			{ "local_description_spanish", SelectedLocalOrg.DescriptionSpanish },
			{ "local_link", SelectedLocalOrg.Link }
		};
	}
}
