using Godot;
using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

/*
* Game state machine + frontend driver. Attached to the root of both
* Main.tscn and Results.tscn; detects which scene it is running in.
*
* Main scene:  shows/hides the category highlights as pieces are placed
*              on the readers. When all three categories are registered,
*              the outcome is computed and the scene changes to Results.
* Results:     plays the loading transition (pill wipe-in, then a wipe-out
*              of the Loading layer), populates the org labels, and shows
*              the QR codes. Removing any piece — or an idle timeout —
*              returns to Main.
*
* Piece events come from the SerialCom autoload (Teensy RFID readers).

* Dev keys: '1'/'2'/'3' toggle test pieces 0x01/0x0D/0x19 on slots 1-3;
* 'L' toggles English/Spanish (same as the physical language button).
*
* Game state is static so it survives the Main <-> Results scene changes.
*/
public partial class GameController : Node2D
{
	// Loading-bar fill time, then the wipe-out revealing the results.
	[Export] public double LoadingSeconds { get; set; } = 2.0;
	[Export] public double WipeOutSeconds { get; set; } = 0.7;
	// Results returns to Main after this long with no piece activity.
	[Export] public double ResultsTimeoutSeconds { get; set; } = 60.0;

	private const string MainScenePath = "res://Main.tscn";
	private const string ResultsScenePath = "res://Results.tscn";
	private const string WipeShaderPath = "res://Shaders/wipe.gdshader";

	// Dev-key piece IDs: Interest "Art", Topic "Use Clean Energy",
	// Group "Sports or Rec Group".
	private const int DevHexSlot1 = 0x01;
	private const int DevHexSlot2 = 0x19;
	private const int DevHexSlot3 = 0x0D;

	// -------- state shared across scene changes
	private static readonly Dictionary<int, PieceInfo> Slots = new();
	private static Outcome CurrentOutcome;
	private static OrgInfo SelectedLocalOrg;
	private static bool SpanishActive;
	private static readonly Random Rng = new();

	// Parented to /root (not the scene) so playback survives scene changes —
	// Reset.wav starts right as we leave the Results scene.
	private static AudioStreamPlayer PieceSound;
	private static AudioStreamPlayer ResetSound;
	private static AudioStreamPlayer RewardSound;

	private SerialCom serial;
	private bool isResultsScene;
	private bool changingScene;
	private double resultsIdleTimer;

	private Label nationalLabel, nationalDesc, localLabel, localDesc;
	// Scene-configured font sizes of the org name labels, captured before
	// any shrink-to-fit override is applied.
	private int nationalTitleBaseSize, localTitleBaseSize;

	// Static UI text (English-Spanish.csv): node path -> "Godot Label" key.
	// NOTE: the CSV rows FinaleSubheader/LocalHeader are keyed by CONTENT,
	// which is crossed relative to the scene node names — the node named
	// FinaleSubheader shows the "LOCAL OREGON" tag and the node named
	// LocalHeader shows the long prompt paragraph. Mapped accordingly.
	private static readonly (string Path, string Key)[] MainUiText = {
		("Main/UI/MainHeader", "MainHeader"),
		("Main/UI/MainSubheader", "MainSubheader"),
		("Main/UI/Prompt1", "Prompt1"),
		("Main/UI/Prompt2", "Prompt2"),
		("Main/UI/Prompt3", "Prompt3"),
	};
	private static readonly (string Path, string Key)[] ResultsUiText = {
		("Loading/Loading", "LoadingLabel"),
		("Results/QRNode/UI/FinaleSubheader", "LocalHeader"),
		("Results/QRNode/UI/LocalHeader", "FinaleSubheader"),
		("Results/QRNode/UI/NationalHeader", "NationalHeader"),
		("Results/QRNode/UI/QRinfo", "QRInfo"),
		("Results/QRNode/UI/QRinfo2", "QRInfo"),
	};
	private const string FinaleHeaderPath = "Results/QRNode/UI/FinaleHeader";
	private const string FinaleHighlightColor = "#47c1bb";

	// Scene-configured font sizes of the static UI labels (per label).
	private readonly Dictionary<Control, int> uiTextBaseSizes = new();

	public override void _Ready()
	{
		isResultsScene = GetNodeOrNull("Results") != null;
		EnsureSoundPlayers();

		serial = GetNodeOrNull<SerialCom>("/root/SerialCom");
		if (serial != null) {
			serial.PiecePlaced += OnPiecePlaced;
			serial.PieceRemoved += OnPieceRemoved;
			serial.LanguagePressed += OnLanguageToggled;
		} else {
			GD.PrintErr("[GameController] SerialCom autoload not found; keyboard input only.");
		}

		if (isResultsScene) {
			SetupResults();
		} else {
			SetupMain();
		}
	}

	public override void _ExitTree()
	{
		if (serial != null) {
			serial.PiecePlaced -= OnPiecePlaced;
			serial.PieceRemoved -= OnPieceRemoved;
			serial.LanguagePressed -= OnLanguageToggled;
		}
	}

	public override void _Process(double delta)
	{
		if (!isResultsScene || changingScene) {
			return;
		}
		resultsIdleTimer -= delta;
		if (resultsIdleTimer <= 0) {
			GD.Print("[GameController] Results idle timeout; resetting.");
			// Pieces were left on the readers; forget them so the game
			// waits for fresh placements instead of instantly re-triggering.
			Slots.Clear();
			ReturnToMain();
		}
	}

	// --------------------------------------------------------------- input

	public override void _UnhandledKeyInput(InputEvent @event)
	{
		if (@event is not InputEventKey key || !key.Pressed || key.Echo) {
			return;
		}
		switch (key.Keycode) {
			case Key.Key1: ToggleDevPiece(1, DevHexSlot1); break;
			case Key.Key2: ToggleDevPiece(2, DevHexSlot2); break;
			case Key.Key3: ToggleDevPiece(3, DevHexSlot3); break;
			case Key.L: OnLanguageToggled(); break;
		}
	}

	private void ToggleDevPiece(int slot, int hexId)
	{
		if (Slots.ContainsKey(slot)) {
			OnPieceRemoved(slot);
		} else {
			OnPiecePlaced(slot, hexId);
		}
	}

	// -------------------------------------------------------- piece events

	private void OnPiecePlaced(int slot, int hexId)
	{
		if (changingScene) {
			return;
		}
		PieceInfo piece = SheetManager.Instance?.LookupHex(hexId);
		if (piece == null) {
			GD.PrintErr($"[GameController] Unknown hex 0x{hexId:X2} on slot {slot}; ignoring.");
			return;
		}

		Slots[slot] = piece;
		GD.Print($"[GameController] Slot {slot}: {piece.Category} / {piece.Item}");

		if (isResultsScene) {
			resultsIdleTimer = ResultsTimeoutSeconds;
			return;
		}

		SetHighlight(piece.Category, true);
		PieceSound?.Play();
		if (AllPiecesRegistered()) {
			BeginResults();
		}
	}

	private void OnPieceRemoved(int slot)
	{
		if (changingScene || !Slots.Remove(slot, out PieceInfo removed)) {
			return;
		}
		GD.Print($"[GameController] Slot {slot} cleared ({removed.Category}).");

		if (isResultsScene) {
			ReturnToMain();
			return;
		}
		// Keep the highlight if another slot still holds this category.
		SetHighlight(removed.Category, GetPieceByCategory(removed.Category) != null);
	}

	private void OnLanguageToggled()
	{
		SpanishActive = !SpanishActive;
		GD.Print($"[GameController] Language: {(SpanishActive ? "Spanish" : "English")}");
		ApplyUiText();
		if (isResultsScene) {
			resultsIdleTimer = ResultsTimeoutSeconds;
			ApplyLanguage();
		}
	}

	// ----------------------------------------------------------- main scene

	private void SetupMain()
	{
		ApplyUiText();
		// Hide all highlights, then restore any for pieces still on the
		// readers (e.g. after returning from Results with two pieces left).
		foreach (string category in new[] { "Interest", "Topic", "Group" }) {
			SetHighlight(category, GetPieceByCategory(category) != null);
		}
	}

	private void SetHighlight(string category, bool visible)
	{
		string node = category.ToLowerInvariant() switch {
			"interest" => "Main/PersonHighlight",
			"topic" => "Main/CloudHighlight",
			"group" => "Main/HouseHighlight",
			_ => null
		};
		if (node != null) {
			GetNodeOrNull<Sprite2D>(node)?.SetVisible(visible);
		}
	}

	private bool AllPiecesRegistered()
	{
		return GetPieceByCategory("Interest") != null
			&& GetPieceByCategory("Topic") != null
			&& GetPieceByCategory("Group") != null;
	}

	private static PieceInfo GetPieceByCategory(string category)
	{
		foreach (PieceInfo piece in Slots.Values) {
			if (string.Equals(piece.Category, category, StringComparison.OrdinalIgnoreCase)) {
				return piece;
			}
		}
		return null;
	}

	private void BeginResults()
	{
		PieceInfo interest = GetPieceByCategory("Interest");
		PieceInfo topic = GetPieceByCategory("Topic");
		PieceInfo group = GetPieceByCategory("Group");

		Outcome outcome = SheetManager.Instance?.FindOutcome(topic.Item, group.Item, interest.Item);
		if (outcome == null) {
			GD.PrintErr($"[GameController] No Truth Table row for Topic='{topic.Item}', " +
				$"Group='{group.Item}', Interest='{interest.Item}'.");
			return;
		}

		CurrentOutcome = outcome;
		SelectedLocalOrg = outcome.LocalOrgs.Count > 0
			? outcome.LocalOrgs[Rng.Next(outcome.LocalOrgs.Count)]
			: new OrgInfo();

		GD.Print($"[GameController] Outcome: national='{outcome.NationalOrg.Name}', " +
			$"local='{SelectedLocalOrg.Name}'.");
		ChangeScene(ResultsScenePath);
	}

	// -------------------------------------------------------- results scene

	private void SetupResults()
	{
		resultsIdleTimer = ResultsTimeoutSeconds;

		nationalLabel = GetNode<Label>("Results/NationalLabel");
		nationalDesc = GetNode<Label>("Results/NationalDesc");
		localLabel = GetNode<Label>("Results/LocalLabel");
		localDesc = GetNode<Label>("Results/LocalDesc");

		// Fit text inside the preconfigured boxes without touching font size:
		// wrap the descriptions. Org names keep the scene's font size unless
		// they overflow, in which case FitLabelText shrinks them to fit
		// (ellipsis only as a last resort at the minimum size).
		nationalDesc.AutowrapMode = TextServer.AutowrapMode.Word;
		localDesc.AutowrapMode = TextServer.AutowrapMode.Word;
		nationalLabel.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
		localLabel.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
		nationalTitleBaseSize = nationalLabel.GetThemeFontSize("font_size");
		localTitleBaseSize = localLabel.GetThemeFontSize("font_size");

		ApplyUiText();

		if (CurrentOutcome == null) {
			// Scene launched directly (F6) with no game in progress.
			GD.PrintErr("[GameController] Results scene opened with no outcome set.");
			return;
		}

		// The Results layer, QRNode, and its UI are hidden in the scene so
		// nothing flashes before the transition; show them now — the Loading
		// layer (z-raised) covers them until the wipe-out reveals them.
		GetNode<Node2D>("Results").Visible = true;
		GetNode<Node2D>("Results/QRNode").Visible = true;
		GetNode<Node2D>("Results/QRNode/UI").Visible = true;

		ApplyLanguage();

		var qr = GetNodeOrNull<QRGenerator>("Results/QRNode");
		qr?.SetUrls(CurrentOutcome.NationalOrg.Link, SelectedLocalOrg.Link);

		PlayLoadingTransition();
	}

	private void ApplyLanguage()
	{
		if (CurrentOutcome == null || nationalLabel == null) {
			return;
		}
		FitLabelText(nationalLabel, CurrentOutcome.NationalOrg.Name, nationalTitleBaseSize);
		FitLabelText(localLabel, SelectedLocalOrg.Name, localTitleBaseSize);
		nationalDesc.Text = SpanishActive
			? CurrentOutcome.NationalOrg.DescriptionSpanish
			: CurrentOutcome.NationalOrg.Description;
		localDesc.Text = SpanishActive
			? SelectedLocalOrg.DescriptionSpanish
			: SelectedLocalOrg.Description;
	}

	// Sets the label's text at its original font size, shrinking only as
	// far as needed for the text to fit the label's box.
	private static void FitLabelText(Label label, string text, int baseSize)
	{
		const int MinFontSize = 10;

		label.Text = text;
		Font font = label.GetThemeFont("font");
		int size = baseSize;
		while (size > MinFontSize
			&& font.GetStringSize(text, HorizontalAlignment.Left, -1, size).X > label.Size.X) {
			size--;
		}
		label.AddThemeFontSizeOverride("font_size", size);
	}

	// ------------------------------------------------------- static UI text

	// Applies the current language's strings (English-Spanish.csv) to the
	// static UI labels of the active scene.
	private void ApplyUiText()
	{
		if (SheetManager.Instance == null || !SheetManager.Instance.IsReady) {
			return;
		}

		foreach ((string path, string key) in isResultsScene ? ResultsUiText : MainUiText) {
			var label = GetNodeOrNull<Label>(path);
			string text = SheetManager.Instance.GetUiText(key, SpanishActive);
			if (label == null || text == null) {
				GD.PrintErr($"[GameController] UI text missing: node '{path}' / key '{key}'.");
				continue;
			}
			FitUiLabel(label, text);
		}

		if (isResultsScene) {
			ApplyFinaleHeader();
		}
	}

	// Word-wraps within the label's box at its scene-configured font size,
	// shrinking only if the wrapped text is taller than the box.
	private void FitUiLabel(Label label, string text)
	{
		const int MinFontSize = 10;

		if (!uiTextBaseSizes.TryGetValue(label, out int baseSize)) {
			baseSize = label.GetThemeFontSize("font_size");
			uiTextBaseSizes[label] = baseSize;
			label.AutowrapMode = TextServer.AutowrapMode.Word;
		}

		label.Text = text;
		Font font = label.GetThemeFont("font");
		int size = baseSize;
		while (size > MinFontSize
			&& font.GetMultilineStringSize(text, HorizontalAlignment.Left, label.Size.X, size).Y
				> label.Size.Y) {
			size--;
		}
		label.AddThemeFontSizeOverride("font_size", size);
	}

	// FinaleHeader is a RichTextLabel: the words 'YOUR' / 'TU' are shown in
	// the highlight color, the rest keeps the theme's default color.
	private void ApplyFinaleHeader()
	{
		const int MinFontSize = 10;

		var header = GetNodeOrNull<RichTextLabel>(FinaleHeaderPath);
		string text = SheetManager.Instance.GetUiText("FinaleHeader", SpanishActive);
		if (header == null || text == null) {
			GD.PrintErr("[GameController] FinaleHeader node or CSV row missing.");
			return;
		}

		if (!uiTextBaseSizes.TryGetValue(header, out int baseSize)) {
			baseSize = header.GetThemeFontSize("normal_font_size");
			uiTextBaseSizes[header] = baseSize;
		}

		// Shrink-to-fit measured on the plain text, before BBCode is added.
		Font font = header.GetThemeFont("normal_font");
		int size = baseSize;
		while (size > MinFontSize
			&& font.GetMultilineStringSize(text, HorizontalAlignment.Left, header.Size.X, size).Y
				> header.Size.Y) {
			size--;
		}
		header.AddThemeFontSizeOverride("normal_font_size", size);

		header.Text = Regex.Replace(text, @"\b(YOUR|TU)\b",
			$"[color={FinaleHighlightColor}]$1[/color]");
	}

	private void PlayLoadingTransition()
	{
		var loading = GetNode<Node2D>("Loading");
		var pill = GetNode<Sprite2D>("Loading/LoadingPill");
		loading.Visible = true;
		// The Results layer is a later sibling in the scene, so it draws on
		// top of Loading. Raise Loading above it for the transition.
		loading.ZIndex = 10;

		var shader = GD.Load<Shader>(WipeShaderPath);

		// Stage 1: fill the pill left-to-right like a loading bar, so the
		// wipe region is bounded to the pill's own extent on screen.
		var pillMat = new ShaderMaterial { Shader = shader };
		(float pillLeft, float pillRight) = ScreenUvExtent(pill);
		pillMat.SetShaderParameter("reveal", true);
		pillMat.SetShaderParameter("left", pillLeft);
		pillMat.SetShaderParameter("right", pillRight);
		pillMat.SetShaderParameter("progress", 0.0f);
		pill.Material = pillMat;

		// Stage 2: wipe the whole Loading layer out, left to right. Applied
		// to every child (background, pill, and the loading label).
		var wipeMat = new ShaderMaterial { Shader = shader };
		wipeMat.SetShaderParameter("reveal", false);
		wipeMat.SetShaderParameter("progress", 0.0f);

		Tween tween = CreateTween();
		tween.TweenMethod(Callable.From((float p) => pillMat.SetShaderParameter("progress", p)),
			0.0f, 1.0f, LoadingSeconds);
		tween.TweenCallback(Callable.From(() => {
			foreach (Node child in loading.GetChildren()) {
				if (child is CanvasItem item) {
					item.Material = wipeMat;
				}
			}
		}));
		tween.TweenMethod(Callable.From((float p) => wipeMat.SetShaderParameter("progress", p)),
			0.0f, 1.0f, WipeOutSeconds);
		tween.TweenCallback(Callable.From(() => {
			loading.Visible = false;
			RewardSound?.Play();
		}));
	}

	// A sprite's horizontal extent in SCREEN_UV coordinates (0..1).
	private (float, float) ScreenUvExtent(Sprite2D sprite)
	{
		Rect2 rect = sprite.GetRect();
		float x0 = (sprite.GlobalTransform * rect.Position).X;
		float x1 = (sprite.GlobalTransform * rect.End).X;
		float screenWidth = GetViewportRect().Size.X;
		return (Mathf.Min(x0, x1) / screenWidth, Mathf.Max(x0, x1) / screenWidth);
	}

	// -------------------------------------------------------- scene changes

	private void ReturnToMain()
	{
		CurrentOutcome = null;
		SelectedLocalOrg = null;
		// SpanishActive is intentionally kept — language persists across
		// games and only changes on 'L' / the physical language button.
		ResetSound?.Play();
		ChangeScene(MainScenePath);
	}

	private void ChangeScene(string path)
	{
		if (changingScene) {
			return;
		}
		changingScene = true;
		GetTree().ChangeSceneToFile(path);
	}

	// ---------------------------------------------------------------- sounds

	private void EnsureSoundPlayers()
	{
		if (PieceSound != null && IsInstanceValid(PieceSound)) {
			return;
		}
		PieceSound = CreateSoundPlayer("res://Assets/Sounds/PieceRegistered.wav");
		ResetSound = CreateSoundPlayer("res://Assets/Sounds/Reset.wav");
		RewardSound = CreateSoundPlayer("res://Assets/Sounds/Reward.wav");
	}

	private AudioStreamPlayer CreateSoundPlayer(string path)
	{
		var stream = GD.Load<AudioStream>(path);
		if (stream == null) {
			GD.PrintErr($"[GameController] Sound not found: {path}");
			return null;
		}
		var player = new AudioStreamPlayer { Stream = stream };
		GetTree().Root.CallDeferred(Node.MethodName.AddChild, player);
		return player;
	}
}
