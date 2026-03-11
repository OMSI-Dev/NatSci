using Godot;
using System;
using System.Collections.Generic;

/* * * * * * * * * * *
* Fetches data from a publicly published Google Sheet (CSV export) on startup.
* Google Sheet needs to be PUBLISHED TO WEB as a CSV.
* This script has to be autoloaded. Project > Project Settings > Autoload.
* Access from any script via: SheetManager.Instance.GetCell(row, "ColumnName").
* * * * * * * * * * */

public partial class SheetManager : Node
{
	// Replace this URL with the published CSV URL.
	private const string SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT0Yr6AIij3GnBDkB-eJlz5aTuLJIelGDH9JTGNqVwmND9SnghV9E47ZUZZzD0rWmseccNJLxzKnqd3/pub?gid=1578975206&single=true&output=csv";

	public static SheetManager Instance { get; private set; }

	// All sheet data: _data[row][col]. Row 0 is the header row.
	private List<List<string>> _data = new();

	// Enum / column lookup index.
	private Dictionary<string, int> _enums = new();

	[Signal] public delegate void DataLoadedEventHandler();
	[Signal] public delegate void DataFailedEventHandler(string error);

	public bool IsReady { get; private set; } = false;

	public override void _Ready() {
		Instance = this;
		FetchSheet();
	}

	private async void FetchSheet() {
		var http = new HttpRequest();
		AddChild(http);

		var tcs = new System.Threading.Tasks.TaskCompletionSource<Godot.Collections.Array>();
		http.RequestCompleted += (result, responseCode, headers, body) =>
			tcs.TrySetResult(new Godot.Collections.Array { result, responseCode, body });

		Error err = http.Request(SHEET_CSV_URL);
		if (err != Error.Ok) {
			GD.PrintErr($"[SheetManager] HTTP request failed to start: {err}");
			EmitSignal(SignalName.DataFailed, err.ToString());
			return;
		}

		var response = await tcs.Task;

		long responseCode = response[1].AsInt64();
		byte[] body = (byte[])response[2];

		if (responseCode != 200) {
			string errMsg = $"HTTP {responseCode}: {System.Text.Encoding.UTF8.GetString(body)}";
			GD.PrintErr($"[SheetManager] {errMsg}");
			EmitSignal(SignalName.DataFailed, errMsg);
			return;
		}

		ParseCsv(System.Text.Encoding.UTF8.GetString(body));
		http.QueueFree();
	}

	private void ParseCsv(string csv) {
		_data.Clear();
		_enums.Clear();

		var rows = SplitCsvRows(csv);
		bool firstRow = true;

		foreach (var row in rows) {
			if (row.Count == 0) {
				continue;
			}
			_data.Add(row);

			if (firstRow) {
				for (int i = 0; i < row.Count; i++) {
					_enums[row[i].Trim()] = i;
				}
				firstRow = false;
			}
		}

		IsReady = true;
		GD.Print($"[SheetManager] Loaded {_data.Count} rows, {_enums.Count} columns.");
		EmitSignal(SignalName.DataLoaded);
	}

	// CSV parser. Handles quoted fields containing commas, quotes, and newlines.
	private List<List<string>> SplitCsvRows(string csv) {
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
				} if (c == '\n') {
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

	public int RowCount => _data.Count;
	public int ColCount => _enums.Count;

	public string GetCell(int row, int col) {
		if (row < 0 || row >= _data.Count) {
			return "";
		}
		if (col < 0 || col >= _data[row].Count) {
			return "";
		}
		return _data[row][col];
	}

	public string GetCell(int row, string colName) {
		if (!_enums.TryGetValue(colName, out int col)) {
			return "";
		}
		return GetCell(row, col);
	}

	public List<string> GetRow(int row) {
		if (row < 0 || row >= _data.Count) {
			return new List<string>();
		}
		return new List<string>(_data[row]);
	}

	public List<string> GetColumn(string colName) {
		var result = new List<string>();
		if (!_enums.TryGetValue(colName, out int col)) {
			return result;
		}
		for (int r = 1; r < _data.Count; r++) {
			result.Add(GetCell(r, col));
		}
		return result;
	}

	public int FindRow(string colName, string searchValue) {
		if (!_enums.TryGetValue(colName, out int col)) {
			return -1;
		}
		for (int r = 1; r < _data.Count; r++) {
			if (GetCell(r, col) == searchValue) {
				return r;
			}
		}
		return -1;
	}

	public List<string> GetHeaders() {
		var headers = new List<string>(new string[_enums.Count]);
		foreach (var kv in _enums) {
			headers[kv.Value] = kv.Key;
		}
		return headers;
	}
}
