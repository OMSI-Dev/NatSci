Startup Sequence
Phase 1: Autoloaded Scripts (Before Main Scene)
These run first because they're configured in project.godot:22-23:

1. SerialCom._Ready() (SerialCom.cs:22)

Detects available serial ports
Connects to the last port in the list (assumed to be Arduino)
Opens serial connection
Then sits in _Process() constantly reading serial data

2. SheetManager._Ready() (SheetManager.cs:36)

Creates an HTTPRequest node
Calls FetchSheet() to download CSV from Google Sheets
Downloads the spreadsheet asynchronously
Parses it when complete
Makes data available via GetCell(), GetColumn(), etc.
Phase 2: Main Scene Loads (Main.tscn)
3. GameController._Ready() (GameController.cs:7)

Does nothing (empty implementation)
4. QRGenerator._Ready() (QRGenerator.cs:18)

Gets references to child nodes (QRTexture, QRCodeHelper, HTTPRequest)
Starts TWO HTTP requests (but both to nationalOrgs - this is a bug)
Subscribes to RequestCompleted event
Calls UpdateQRCode() immediately (but lists are empty, so nothing happens)
Phase 3: Async Responses
5. QRGenerator.OnRequestCompleted() (QRGenerator.cs:45)

When HTTP request finishes
Handles redirects if needed
Calls ParseCsv() with the downloaded data
Tries to call UpdateQRCode() but crashes because urls doesn't exist
6. QRGenerator.UpdateQRCode() (QRGenerator.cs:165)

Gets current URL from the (non-existent) urls list
Calls qrHelper.Call("generate_qr", url, 8) via GDScript
Converts returned Image to ImageTexture
Displays in QRTexture node
Phase 4: Runtime (Event-Driven)
SerialCom._Process() - Every frame

Reads incoming serial data
Splits it character by character into dataSplit array
Data is available but not used by anything
QRGenerator._Input() - When keys pressed (QRGenerator.cs:120)

Left/Right arrows cycle through URLs
Calls UpdateQRCode() for each navigation
Currently crashes because urls doesn't exist
