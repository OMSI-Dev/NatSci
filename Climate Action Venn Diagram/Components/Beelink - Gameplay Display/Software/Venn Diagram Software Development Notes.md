# NOTES
## Goals
 Each piece will have a special hex code, which will be hardcoded by software to a specific interest, group, or topic (of 18 total options)
 
 The software will have visually reactive gameplay according to which pieces are placed in the slots. This will be communicated via Serial. 
 
 The software will be in Godot. 

## Firmware
**Known Tags: Interest, Topic, and Group**
```
Hex 1-12 for interests
Hex 13-24 for topics
Hex 25-36 for groups
```
*There are technically 6 options for both the interest and group category. There are specifically 12 options for the group category. The hex codes are all expanded to 12 options each for overhead.*

uint8_t knownTagsInterest[12] =
{
0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C};

const uint8_t knownTagsTopic[12] =
{
0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18};

const uint8_t knownTagsGroup[12] =
{
0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24};

**Removed Slots Serial Print Format**
1:0
2:0
3:0

**Registered Slots Serial Print Format**
1:0x01 < Interest : 1
2:0x0D < Topic : 1
3:0x019 < Group : 1

_______________
# Startup Sequence (Pre-configured before 2026-09-03)
## Phase 1: Autoloaded Scripts (Before Main Scene)
*This is the current repo's state as of 2026-09-03, before any software dev by autumn*

*These run first because they're configured in project.godot:22-23:*
**1. SerialCom._Ready() (SerialCom.cs:22)**

Detects available serial ports
Connects to the last port in the list (assumed to be Arduino)
Opens serial connection
Then sits in _Process() constantly reading serial data

**2. SheetManager._Ready() (SheetManager.cs:36)**

Creates an HTTPRequest node
Calls FetchSheet() to download CSV from Google Sheets
Downloads the spreadsheet asynchronously
Parses it when complete
Makes data available via GetCell(), GetColumn(), etc.

## Phase 2: Main Scene Loads (Main.tscn)
**3. GameController._Ready() (GameController.cs:7)**

Does nothing (empty implementation)

**4. QRGenerator._Ready() (QRGenerator.cs:18)**

Gets references to child nodes (QRTexture, QRCodeHelper, HTTPRequest)
Starts TWO HTTP requests (but both to nationalOrgs - this is a bug)
Subscribes to RequestCompleted event
Calls UpdateQRCode() immediately (but lists are empty, so nothing happens)
Phase 3: Async Responses

**5. QRGenerator.OnRequestCompleted() (QRGenerator.cs:45)**

When HTTP request finishes
Handles redirects if needed
Calls ParseCsv() with the downloaded data
Tries to call UpdateQRCode() but crashes because urls doesn't exist

**6. QRGenerator.UpdateQRCode() (QRGenerator.cs:165)**

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



