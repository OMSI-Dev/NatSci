# Venn Diagram Godot Framework — Dev Spec (v2)

**Audience:** a coding agent (Claude, working in VS Code) picking this up cold, with no other
context than this document, the reference files below, and read access to the actual Godot
project source (`SerialCom.cs`, `SheetManager.cs`, `GameController.cs`, `QRGenerator.cs`,
`project.godot`).

**Goal:** finish the currently-empty `GameController.cs` so it tracks which physical tag is
currently in each of the three RFID slots (Interest / Topic / Group) via the existing
`SerialCom.cs` connection, and — once all three are present — looks up the matching row in the
truth table and produces an "outcome" (a National org + one randomly-chosen Local org), then
fixes `QRGenerator.cs` so it can actually display that outcome.

**Language: C#.** All code sketches below are illustrative C#, not GDScript — this project's
scripts (`SerialCom.cs`, `SheetManager.cs`, `GameController.cs`, `QRGenerator.cs`) are all C#.

## Reference files (read these first, in this order)

1. **`System_Structure.md`** — firmware architecture and the **Serial protocol** section, which
   defines the exact line format `GameController` must parse. Also read **"Known discrepancies &
   quirks"** — several affect correctness here (see callouts below).
2. **`Venn_Diagram_Software_Development_Notes.md`** — describes the actual current state of the
   Godot project (autoload order, existing bugs) as of 2026-09-03. **Read this before touching any
   existing script** — it tells you what's already wired up vs. still broken.
3. **`Hex_Codes.csv`** — maps every physical tag's hex code to its `Category` (`Interests` /
   `Topics` / `Group`), `Subcategory` (Interest only), and `Item` (the human-readable name — this
   is the value that must match the truth table's `Topic` / `Group` / `Interest Item` columns).
4. **`truth_table_topic_group_interest_item.csv`** — one row per valid
   `Topic × Group × Interest Item` combination, with a `Prompt` and full National/Local×3 org data
   (name, English description, Spanish description, link) per row. This is the lookup target.

Treat all four as living documents: if `Hex_Codes.csv` or the truth table changes shape, the
loader code should still work as long as column names are unchanged — don't hardcode row counts
or hex ranges into logic, only into validation/warnings.

**Data source note:** the project already has `SheetManager.cs`, which fetches a CSV from Google
Sheets over HTTP. **That is unrelated to this feature** — confirmed not to be the source for hex
codes or the truth table. `Hex_Codes.csv` and the truth table should ship as **local files bundled
with the project** (e.g. `res://data/hex_codes.csv`, `res://data/truth_table.csv`), loaded
directly from disk, not fetched. Don't wire `SheetManager` into this feature.

## Serial protocol recap (do not re-derive — copied from System_Structure.md for convenience)

- One event per line, edge-triggered, sent exactly once per placement/removal.
- Tag placed & matched: `<category>:0x<ID>` — e.g. `1:0x05`. Category is a **single digit**,
  hex has **no zero-padding** (`0x5`, not `0x05` — parse leniently either way).
- Tag removed: `<category>:0x0`.
- Language button: a bare line `L` (not relevant to this module — ignore/pass through).
- **Category-to-slot mapping is the firmware code's, not the docs':**
  `1 = Interest`, `2 = Topic`, `3 = Group`. (`Documentation/Firmware/RFID Group Tags by Hex.md`
  has this wrong — do not trust it. The dev-notes doc's example — `1:0x01 < Interest`,
  `2:0x0D < Topic`, `3:0x019 < Group` — agrees with this mapping, good corroboration.)
- If a read fails or matches no known tag, **no line is sent at all** — there's no "unknown tag"
  event to handle, but a slot can silently stay empty even though a tag is physically present.
  Not fixable on the Godot side.
- In `debugMode`, extra human-readable lines are interleaved on the same serial stream. **The
  parser must silently ignore any line that isn't `L` or `<digit>:0x<hex>`** rather than erroring.
- Only `groupCheck()` (category 3) guards against sending a confirm when the match failed; topic
  and interest (categories 1 and 2) do not have this guard in firmware. Be defensive for all three
  regardless.

## Existing codebase: what's already there and what's broken

This is not a greenfield build. Read the actual current source for each file before editing it —
the summary below (from the dev notes) may be stale by the time you start.

- **`SerialCom.cs`** (autoload, runs first per `project.godot:22-23`) — already detects serial
  ports, connects to "the last port in the list" (assumed Arduino), opens the connection, and
  reads continuously in `_Process()`. **As of the notes, it splits incoming data character-by-
  character into a `dataSplit` array and does nothing further with it** — no line assembly, no
  event dispatch. This is the piece that needs building: buffer characters until a line terminator,
  then hand complete lines off to whatever consumes them (likely `GameController`, via a C# event
  or signal — check how other autoloads in this project communicate with each other, e.g. is there
  an existing event bus, or does `project.godot` autoload order imply direct static/singleton
  access?). **Do not assume a serial addon needs to be researched or chosen — the connection layer
  already exists in `SerialCom.cs`.**
- **`SheetManager.cs`** (autoload, runs second) — downloads/parses a Google Sheets CSV, exposes
  `GetCell()`/`GetColumn()`. **Unrelated to this feature** (confirmed) — do not integrate it with
  hex codes or the truth table. Leave it alone unless a bug in it is actively blocking your work.
- **`GameController.cs`** — currently empty (`_Ready()` does nothing). **This is where the state
  machine from this spec belongs.**
- **`QRGenerator.cs`** — partially implemented, with known bugs per the dev notes:
  - `_Ready()` starts **two** HTTP requests, both targeting `nationalOrgs` — one of these should
    almost certainly be targeting a local-orgs endpoint/list instead. Find and fix the duplication.
  - `UpdateQRCode()` is called immediately in `_Ready()` before any data has loaded, so it's a
    no-op at that point (expected/harmless) — but it references a `urls` list that **does not
    exist**, causing a crash both there and later in `OnRequestCompleted()` and the arrow-key
    `_Input()` handler.
  - This component is confirmed to be the **intended outcome-display surface** for this feature.
    Once `GameController` produces an outcome (National org + chosen Local org, each with
    name/description/description_es/link), `QRGenerator` needs a real, populated `urls` (or
    equivalent) list/structure to replace the currently-nonexistent one, sourced from that outcome
    rather than from HTTP requests. Whether `QRGenerator` should keep any HTTP-based org-fetching
    at all, or whether the two HTTP requests in `_Ready()` should be removed entirely in favor of
    receiving the outcome from `GameController` directly, is left to you to decide after reading
    the current `QRGenerator.cs` source in full — document whichever direction you take and why.
  - Arrow-key navigation (`_Input()`, Left/Right cycling through URLs) — once a real outcome
    structure exists, decide whether this should cycle between National/Local org, or something
    else; the original intent isn't documented beyond "cycle through URLs."
- **`GameController.cs`** doing nothing currently also means there's no existing signal/event
  pattern to copy from it — check `QRGenerator.cs` and `SerialCom.cs` for whatever inter-script
  communication convention (C# events, Godot signals, direct autoload references via
  `GetNode<T>("/root/...")`, etc.) this project already uses, and follow it rather than inventing
  a new pattern.

## Architecture

### 1. Data loading (startup)

Load both CSVs once at startup (in `GameController.cs`, or a small dedicated loader class it
owns) into in-memory lookup structures. Recommended:

- `HexCodeTable`: `Dictionary<string, HexCodeEntry>` — key = normalized hex string (e.g. always
  uppercase, e.g. `"0x0D"`), value = `{ Category, Subcategory, Item }`.
- `TruthTable`: `Dictionary<string, List<TruthTableRow>>` — key = `$"{topic}|{group}|{interestItem}"`.
  Value is a **list** (should always have exactly 1 entry given the current data, but don't assume)
  of row objects with all 21 columns.

CSV location: `res://data/hex_codes.csv` and `res://data/truth_table.csv` (create the `data/`
folder if it doesn't exist) — confirm this against any existing project convention first if one
turns up while reading the codebase.

### 2. State machine

Three independent "slots," one per category. Suggested state per slot:

```csharp
public class SlotState
{
    public string HexCode;       // raw hex from serial, null if empty
    public string Category;      // "Interests" | "Topics" | "Group", null if empty
    public string Subcategory;   // Interest only; null for Topic/Group
    public string Item;          // human-readable value used for truth-table lookup
}
```

Keep three separately-named slots (Interest, Topic, Group), not a generic array indexed by the
serial `category` digit — the digit-to-slot mapping is a firmware detail (see protocol recap)
that should be translated once at the parsing boundary, not threaded through the rest of the code.

### 3. Functions to implement (in `GameController.cs` unless noted)

- **`OnSerialLineReceived(string line)`**
  Entry point, wired to whatever `SerialCom.cs` uses to hand off complete lines once its line-
  assembly is built (see above). Passes to the parser; ignores unparseable lines.

- **`ParseSerialLine(string line)`** → nullable result
  Returns `(int categoryDigit, string hex)` for lines matching `^\d:0x[0-9A-Fa-f]+$`, or
  handles/ignores the bare `L` line and anything else. Must not throw on debug-mode noise.

- **`SlotForCategoryDigit(int digit)`**
  Single source of truth for `1→Interest, 2→Topic, 3→Group`. Isolate this so it's easy to find
  and fix if firmware ever changes it.

- **`RegisterPiece(string slot, string hex)`**
  Looks up `hex` in `HexCodeTable`. If found, populates that slot's state and calls
  `CheckAllRegistered()`. If not found (unknown hex, not equal to `0x0`), log a warning and leave
  the slot unchanged.

- **`UnregisterPiece(string slot)`**
  Called on a `<category>:0x0` line. Clears that slot's state entirely and clears any previously
  generated outcome (a removal invalidates the current outcome).

- **`CheckAllRegistered()`** → bool
  True only when all three slots have non-null `Item`. If true, calls `GenerateOutcome()`.

- **`GenerateOutcome()`**
  Builds the truth-table key from the three slots' `Item` values (`Topic` from the Topic slot,
  `Group` from the Group slot, `Interest Item` from the Interest slot — the truth table's own
  `Interest Subcategory` column is *not* part of the lookup key). Looks up `TruthTable[key]`. On a
  hit, builds the outcome object below and hands it to `QRGenerator` (via whatever communication
  convention you find in the codebase). On a miss, see Edge Cases.

- **Local org random selection**
  Given a matched truth-table row, pick 1 of the 3 Local Org column-sets (`Local Org`/
  `Local Org 2`/`Local Org 3`, each with Description/Description Spanish/Link).
  **Note:** a small number of rows have fewer than 3 local orgs populated (blank trailing columns
  — visible in rows like `Use Clean Energy` × `Innovating & Designing`). Only pick among the
  **non-empty** local org slots for that row. Randomness approach (seeded vs. `Random`-per-call)
  is left to your judgment — document the rationale in the selection method's comments.

### 4. Outcome data structure

```csharp
public class Outcome
{
    public OrgInfo NationalOrg;
    public OrgInfo LocalOrg;
    public string Prompt;
    public string Topic, Group, InterestItem;   // the inputs that produced this outcome
}

public class OrgInfo
{
    public string Name, DescriptionEn, DescriptionEs, Link;
}
```

This is what `QRGenerator` needs to consume to build its (currently-missing) `urls` list/display
data. Store as a single "current outcome" value, not a queue — only one outcome is meaningful at
a time, invalidated the moment any slot empties.

### 5. Edge cases to handle explicitly

- **Any slot emptied after an outcome was generated:** clear the outcome, notify `QRGenerator`
  (or whatever display layer) so it returns to a waiting state — don't keep showing a stale
  outcome.
- **Truth table miss despite all three slots filled:** shouldn't happen with current data, but
  log clearly (include the three lookup values) rather than crashing; surface a distinct
  "no match found" state distinguishable from "still waiting."
- **Unknown hex code:** expected occasionally given the reserved/unassigned ranges below. Log and
  ignore, don't crash.
- **Same category re-registered while already filled:** overwrite the slot and re-run
  `CheckAllRegistered()`.
- **Malformed/unparseable serial line:** ignore silently (expected in debug mode).

## Known data gaps (do not silently "fix" — flag and move on)

- `Hex_Codes.csv` reserves hex ranges `0x0D–0x18` (Topic) and `0x19–0x24` (Group) per the
  firmware's 12-slot tag-ID arrays (confirmed again in the dev notes' `knownTagsTopic`/
  `knownTagsGroup` arrays), but only 6 Topic codes (`0x0D–0x12`) and 7 Group codes (`0x19–0x1E`,
  the last freshly assigned for School or Career Group) are currently defined.
  **`0x13–0x18` and `0x1F–0x24` are unassigned/reserved — TODO, not yet part of this system.**
  Treat these as ordinary "unknown hex" cases, not special errors.

## Open questions for the implementing agent to resolve and document inline

1. **Inter-script communication convention:** determine (by reading `SerialCom.cs`, `SheetManager.cs`,
   `QRGenerator.cs`, and `project.godot`) how this project's autoloads talk to each other, and use
   that same pattern for `SerialCom → GameController → QRGenerator`, rather than introducing a new
   one.
2. **`QRGenerator`'s HTTP requests:** decide whether to keep, fix, or remove the two `nationalOrgs`
   HTTP requests in `_Ready()` now that outcome data will arrive from `GameController` instead —
   document the decision.
3. **Local org randomness:** seeded/deterministic vs. plain random-per-call — document the chosen
   rationale in code.
4. **Arrow-key cycling in `QRGenerator`:** once real outcome data exists, decide what Left/Right
   should cycle between (National vs. Local org? something else?) and document it.

## Suggested build order

1. CSV loaders (`HexCodeTable`, `TruthTable`) + sanity checks (row counts, no duplicate hex keys,
   no duplicate truth-table keys).
2. Serial line parser (pure function, no I/O) — testable in isolation with hardcoded sample lines
   including debug-mode noise.
3. Line assembly in `SerialCom.cs` (buffer chars → complete lines) — currently missing.
4. State machine in `GameController.cs` (slots + register/unregister/check-all-registered) —
   testable by feeding it parsed events directly, without a real serial connection.
5. Outcome generation + local-org selection.
6. Wire `SerialCom → GameController` using the project's existing communication convention.
7. Fix `QRGenerator.cs`'s bugs (duplicate HTTP request, missing `urls`) and wire it to consume
   `GameController`'s outcome.
8. End-to-end test with real hardware last, once 1–7 are verified against fake input.
