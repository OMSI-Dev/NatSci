using Godot;
using System;
using System.Collections.Generic;

/* * * * * * * * * * *
* Loads the local game data CSVs on startup (no network access):
*   - docs/Hex Codes.csv    : maps RFID tag hex IDs -> game piece info
*   - docs/Truth Table.csv  : maps (Topic, Group, Interest Item) -> org outcome
*
* This script is autoloaded (Project > Project Settings > Autoload).
* Access from any script via:
*   SheetManager.Instance.LookupHex(hexId)
*   SheetManager.Instance.FindOutcome(topic, group, interestItem)
* * * * * * * * * * */

// A game piece as described by a row of the Hex Code key.
public class PieceInfo
{
	public int Hex;
	public string Category;     // "Interest" | "Topic" | "Group"
	public string Subcategory;  // only set for Interest pieces
	public string Item;
}

// One organization from the Truth Table.
public class OrgInfo
{
	public string Name = "";
	public string Description = "";
	public string DescriptionSpanish = "";
	public string Link = "";
}

// The full outcome for a matched Truth Table row.
public class Outcome
{
	public string Topic;
	public string Group;
	public string InterestSubcategory;
	public string InterestItem;
	public OrgInfo NationalOrg;
	// Up to 3 options; pick one at random. Some rows only have 2 local orgs.
	public List<OrgInfo> LocalOrgs = new();
}

public partial class SheetManager : Node
{
	private const string HexKeyPath = "res://docs/Hex Codes.csv";
	private const string TruthTablePath = "res://docs/Truth Table.csv";

	public static SheetManager Instance { get; private set; }

	[Signal] public delegate void DataLoadedEventHandler();
	[Signal] public delegate void DataFailedEventHandler(string error);

	public bool IsReady { get; private set; } = false;

	private readonly Dictionary<int, PieceInfo> _hexKey = new();
	private readonly List<Outcome> _truthTable = new();

	public override void _Ready() {
		// Guard against a second instance (e.g. the script also attached in a scene).
		if (Instance != null && Instance != this) {
			GD.Print("[SheetManager] Duplicate instance ignored; using autoload.");
			return;
		}
		Instance = this;

		try {
			LoadHexKey();
			LoadTruthTable();
		}
		catch (Exception e) {
			GD.PrintErr($"[SheetManager] Failed to load data: {e.Message}");
			EmitSignal(SignalName.DataFailed, e.Message);
			return;
		}

		IsReady = true;
		GD.Print($"[SheetManager] Loaded {_hexKey.Count} hex codes, {_truthTable.Count} truth table rows.");
		EmitSignal(SignalName.DataLoaded);
	}

	// ------------------------------------------------------------------ API

	// Returns the game piece for a tag ID, or null if the ID is unknown.
	public PieceInfo LookupHex(int hexId) {
		return _hexKey.TryGetValue(hexId, out PieceInfo info) ? info : null;
	}

	// Finds the Truth Table row matching the three registered pieces.
	// Matching is case-insensitive (the sheets are inconsistent about
	// casing, e.g. "Faith-based Group" vs "Faith-Based Group").
	public Outcome FindOutcome(string topic, string group, string interestItem) {
		foreach (Outcome o in _truthTable) {
			if (Matches(o.Topic, topic) && Matches(o.Group, group) && Matches(o.InterestItem, interestItem)) {
				return o;
			}
		}
		return null;
	}

	private static bool Matches(string a, string b) {
		return string.Equals(a?.Trim(), b?.Trim(), StringComparison.OrdinalIgnoreCase);
	}

	// -------------------------------------------------------------- loading

	private string ReadFileText(string resPath) {
		using var file = FileAccess.Open(resPath, FileAccess.ModeFlags.Read);
		if (file == null) {
			throw new Exception($"Cannot open '{resPath}': {FileAccess.GetOpenError()}");
		}
		return file.GetAsText();
	}

	private void LoadHexKey() {
		var rows = SplitCsvRows(ReadFileText(HexKeyPath));
		var cols = HeaderIndex(rows, HexKeyPath);

		for (int r = 1; r < rows.Count; r++) {
			string hexText = Cell(rows[r], cols, "Hex").Trim();
			if (hexText.Length == 0) {
				continue;
			}
			if (hexText.StartsWith("0x", StringComparison.OrdinalIgnoreCase)) {
				hexText = hexText.Substring(2);
			}

			var piece = new PieceInfo {
				Hex = Convert.ToInt32(hexText, 16),
				Category = Cell(rows[r], cols, "Category").Trim(),
				Subcategory = Cell(rows[r], cols, "Subcategory").Trim(),
				Item = Cell(rows[r], cols, "Item").Trim()
			};
			_hexKey[piece.Hex] = piece;
		}
	}

	private void LoadTruthTable() {
		var rows = SplitCsvRows(ReadFileText(TruthTablePath));
		var cols = HeaderIndex(rows, TruthTablePath);

		for (int r = 1; r < rows.Count; r++) {
			var row = rows[r];
			if (Cell(row, cols, "Topic").Trim().Length == 0) {
				continue;
			}

			var outcome = new Outcome {
				Topic = Cell(row, cols, "Topic").Trim(),
				Group = Cell(row, cols, "Group").Trim(),
				InterestSubcategory = Cell(row, cols, "Interest Subcategory").Trim(),
				InterestItem = Cell(row, cols, "Interest Item").Trim(),
				NationalOrg = ReadOrg(row, cols, "National Org")
			};
			// Not every row has all 3 local orgs filled in; skip empty ones
			// so the random pick never lands on a blank entry.
			foreach (string prefix in new[] { "Local Org", "Local Org 2", "Local Org 3" }) {
				OrgInfo org = ReadOrg(row, cols, prefix);
				if (org.Name.Length > 0) {
					outcome.LocalOrgs.Add(org);
				}
			}
			_truthTable.Add(outcome);
		}
	}

	private OrgInfo ReadOrg(List<string> row, Dictionary<string, int> cols, string prefix) {
		return new OrgInfo {
			Name = Cell(row, cols, prefix).Trim(),
			Description = Cell(row, cols, $"{prefix} Description").Trim(),
			DescriptionSpanish = Cell(row, cols, $"{prefix} Description Spanish").Trim(),
			Link = Cell(row, cols, $"{prefix} Link").Trim()
		};
	}

	private Dictionary<string, int> HeaderIndex(List<List<string>> rows, string path) {
		if (rows.Count < 2) {
			throw new Exception($"'{path}' has no data rows.");
		}
		var cols = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
		for (int i = 0; i < rows[0].Count; i++) {
			cols[rows[0][i].Trim()] = i;
		}
		return cols;
	}

	private string Cell(List<string> row, Dictionary<string, int> cols, string colName) {
		if (!cols.TryGetValue(colName, out int col) || col >= row.Count) {
			return "";
		}
		return row[col];
	}

	// CSV parser. Handles quoted fields containing commas, quotes, and newlines.
	private static List<List<string>> SplitCsvRows(string csv) {
		var rows = new List<List<string>>();
		var row = new List<string>();
		var field = new System.Text.StringBuilder();
		bool inQuotes = false;

		for (int i = 0; i < csv.Length; i++) {
			char c = csv[i];

			if (inQuotes) {
				if (c == '"') {
					if (i + 1 < csv.Length && csv[i + 1] == '"') {
						field.Append('"');
						i++;
					} else {
						inQuotes = false;
					}
				} else {
					field.Append(c);
				}
			} else {
				if (c == '"') {
					inQuotes = true;
				} else if (c == ',') {
					row.Add(field.ToString());
					field.Clear();
				} else if (c == '\n') {
					row.Add(field.ToString());
					field.Clear();
					rows.Add(row);
					row = new List<string>();
				} else if (c != '\r') {
					field.Append(c);
				}
			}
		}

		if (field.Length > 0 || row.Count > 0) {
			row.Add(field.ToString());
			rows.Add(row);
		}

		return rows;
	}
}
