# Godot Gameplay Software — Reference Overview
Current state of the software in `Software/Godot`. 

Changes made by autumn as of 2026-09-09.

Godot 4.6 + C# (.NET 8)

# Game summary
Visitors place 3 RFID pieces (Interest, Topic, Group) on readers. A Teensy 4.0 reports them over USB serial. When all 3 are registered, the game shows a matching national + local climate org with QR codes. All data is local CSV — no network anywhere.

# Files
- `GameController.cs` — state machine AND frontend driver. Attached to the root of BOTH scenes; detects scene by presence of a `Results` child node.

- `SheetManager.cs` — autoload. Loads the two CSVs at startup. `SheetManager.Instance.LookupHex(id)` and `.FindOutcome(topic, group, interestItem)` (case-insensitive match).

- `Scripts/SerialCom.cs` — autoload. Serial reader.
- `Scripts/QRGenerator.cs` — on `Results/QRNode`. `SetUrls(nationalUrl, localUrl)` renders QRs locally via `Scripts/QRCodeHelper.gd` + the `qr_code` addon.

- `Shaders/wipe.gdshader` — horizontal screen-space wipe used by the loading transition.

- `docs/Hex Codes.csv` — 24 pieces: Hex, Category (Interest/Topic/Group), Subcategory (Interest only), Item.

- `docs/Truth Table.csv` — every Topic×Group×Interest combo. 

Columns: Topic, Group, Interest Subcategory, Interest Item, then National Org / Local Org / Local Org 2 / Local Org 3, each with Description, Description Spanish, Link. ~60 rows have an empty Local Org 3 — SheetManager skips empty orgs, so the random pick is always from populated entries.

- Autoloads (project.godot): `SerialCom`, `SheetManager`. Both scenes ALSO have a SheetManager child node — the duplicate detects `Instance` already set and no-ops. Leave it.

# Serial protocol (Teensy 4.0, 115200 baud)
- Line `"<slot>:0x<ID>"` (slot 1-3), e.g. `3:0x19`. `0x0` = slot emptied. Line `"L"` = language button.

- Auto-picks `/dev/ttyACM*` (Linux) / `usbmodem` (macOS); `PortOverride` export to force. Reconnects every 2s if unplugged. Background read thread queues lines; signals fire on main thread: `PiecePlaced(slot, hexId)`, `PieceRemoved(slot)`, `LanguagePressed`.

# Game flow
1. Main.tscn: highlights hidden by default. Registering a piece shows its highlight (Interest=PersonHighlight, Topic=CloudHighlight, Group=HouseHighlight) and plays PieceRegistered.wav.
2. All 3 categories registered → outcome computed (random local org chosen) → scene change to Results.tscn.
3. Results.tscn plays the loading transition: pill fills left-to-right (`LoadingSeconds`, 2s), then the whole Loading layer wipes out (`WipeOutSeconds`, 0.7s) revealing results. Reward.wav plays at reveal.
4. Labels populated: NationalLabel/NationalDesc/LocalLabel/LocalDesc. QRs set on QRTextureNational/QRTextureLocal.
5. Removing ANY piece, or 60s idle (`ResultsTimeoutSeconds`), returns to Main and plays Reset.wav. Timeout also clears registered pieces (so abandoned pieces don't retrigger). Language resets to English on return.

# Dev keys
- `1`/`2`/`3` toggle test pieces on slots 1-3: 0x01 (Interest Art), 0x19 (Group Sports or Rec), 0x0D (Topic Use Clean Energy). Same code path as serial.

- `L` toggles English/Spanish (swaps descriptions only; names have no Spanish variant).

# Rules
- Do NOT reorder nodes in the scenes; the code raises `Loading.ZIndex = 10` during the transition instead. Removing that z-index breaks the loading animation (it runs invisibly behind results).

- Do NOT restyle scenes in code (font/color/design are preconfigured). Exceptions already in code: descs get word-wrap; title labels shrink-to-fit ONLY on overflow. QR TextureRects get ExpandMode=IgnoreSize + KeepAspectCentered + Nearest filter.

- CSV `.import` files use `importer="keep"` — the CSVs are game data, not Godot translations. Don't let the editor re-import them as translations.

- GameController connects to SerialCom events in `_Ready` and MUST disconnect in `_ExitTree` (autoload outlives scene instances).

- All HTTP/remote-sheet code was removed (sync_spreadsheets addon deleted). Keep it that way; edits to org data go in the CSVs.
