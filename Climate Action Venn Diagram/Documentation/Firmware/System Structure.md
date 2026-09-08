# System Structure — Venn Diagram Firmware

The Venn Diagram software targets a **Teensy 4.0** that drives three RFID readers (one per Venn diagram
category) and their LED rings, and reports tag events to the media player over USB serial.

> **For agents:** this document is a verified summary of the firmware as of commit `1d5a3a7`
> (2026-09-08). Treat it as authoritative instead of re-reading the source. Only re-read a source
> file if (a) `git log -- Firmware/` shows commits after `1d5a3a7`, or (b) you need to *edit* that
> file. Line references below are to the canonical files listed in the inventory.

## Canonical location & duplicate copies

- **Canonical project:** `Firmware/` at the repo top level (tracked in git). This is the copy to edit.
- `Components/Teensy 4.0 - RFID Handler/Firmware/` is a **stale snapshot**: its `main.cpp` and
  `pins.h` predate commit `1d5a3a7` (no language button, no mode-pin boot check, no empty-slot
  serial message). Its other files are byte-identical to git HEAD. Do not edit it; ignore it.
- **Working-tree caveat:** most of `Firmware/` is currently *deleted but uncommitted* (git status
  shows `D` for `platformio.ini`, `lib/RFID_B1/*`, `src/leds.h`, `src/rfidHandler.h`, etc.). All of
  it still exists at HEAD — `git restore Firmware/` brings the buildable project back. Only
  `src/main.cpp`, `src/pins.h`, `src/serialHandler.h`, `src/tests.h` are present on disk, and they
  match HEAD.

## Build

PlatformIO, single env `teensy40` (platform `teensy`, framework `arduino`). Library deps from
`platformio.ini`: `thomasfredericks/Bounce2 @ ^2.72`, `landtree/OMSI_Timer @ ^1.0.1` (provides
`MoToTimer`), `fastled/FastLED @ ^3.10.3`. Build: `pio run`; upload: `pio run -t upload`.

**Known build blocker:** `main.cpp` does `#include "write.h"` and calls `writeTag()`, but `write.h`
does not exist anywhere in the repo (not on disk, not at HEAD). The project does not compile until
`write.h` is created or the include + write-mode branch are removed.

## File inventory

Everything except the `RFID_B1` library is a header included directly into `main.cpp` — one
translation unit, all functions/globals defined in headers, include order matters
(`pins.h` → `tests.h` → FastLED → `leds.h` → `serialHandler.h` → `rfidHandler.h` → `write.h`).

| File | Contents |
|---|---|
| `src/main.cpp` | Globals, `setup()`, `loop()`, `buttonCheck()`, and the three per-category state machines `groupCheck()` / `topicCheck()` / `interestCheck()` |
| `src/pins.h` | All pin `#define`s, `langButton` (Bounce2), `setModePins()`, `setPins()` |
| `src/tests.h` | `debugMode` / `writeMode` bools; `checkModePins()` reads the boot jumpers |
| `src/leds.h` | `NUM_LEDS 25`; CRGB arrays `house`/`person`/`cloud`; `setLED()` (init + RGB test), `confirmLED(n)`, `scanLED(n)` |
| `src/serialHandler.h` | `sendTag(uint8_t tag, uint8_t category)` → prints `category:0xTAG\n` |
| `src/rfidHandler.h` | Three `RFID_B1` instances; `startRfidSerial()`; `getGroupData()` / `getTopicData()` / `getInterestData()`; `resume*PresenceWatch()` retry wrappers |
| `src/write.h` | **Missing.** Expected to define `writeTag()` (write-mode tag programming) |
| `lib/RFID_B1/` | UART driver for the B1 RFID reader module (see API section) |
| `include/PROTOCOL_REFERENCE.md` | B1 module UART packet format reference (STX/size/CRC framing, command examples) |

## The three categories

Category number is the shared key across serial protocol, LED functions (`scanLED(n)`,
`confirmLED(n)`), and TPI pins:

| # | Category | Symbol | RFID object | UART (Teensy pins) | TPI pin | LED array / data pin | Tag IDs | Confirm color |
|---|---|---|---|---|---|---|---|---|
| 1 | Interest | Person | `interestRFID` | Serial3 (14/15) | 3 (`TPI1`) | `person` / 8 (`ledData1`) | 0x01–0x0C | DarkOrange |
| 2 | Topic | Cloud | `topicRFID` | Serial4 (16/17) | 2 (`TPI2`) | `cloud` / 9 (`ledData2`) | 0x0D–0x18 | Blue |
| 3 | Group | House | `groupRFID` | Serial5 (20/21) | 4 (`TPI3`) | `house` / 10 (`ledData3`) | 0x19–0x24 | DeepPink1 |

Tag ID = one byte at **NTAG215 page 5, byte 3** (`startPage 5`, 1 page read, match against
`knownTags*[12]` arrays in `rfidHandler.h`). `confirmLED(4)` blacks out all three rings.
Each ring is 25 WS2812 LEDs, GRB order.

## Full pin map (`src/pins.h`)

| Pin | Name | Role |
|---|---|---|
| 0 | `langPin` | Language button input (INPUT_PULLUP, pressed = LOW, Bounce2 5 ms) |
| 1 | `BTN_1_PWM` | Button LED PWM output (configured, never driven) |
| 2 | `TPI2` | Topic tag-presence input (active LOW) |
| 3 | `TPI1` | Interest tag-presence input (active LOW) |
| 4 | `TPI3` | Group tag-presence input (active LOW) |
| 5/6/7 | `NPWNDN1..3` | RFID power enables, driven HIGH at boot |
| 8/9/10 | `ledData1..3` | WS2812 data: person / cloud / house |
| 13 | — | Onboard LED, blinked during boot LED test |
| 14/15 | Serial3 | Interest RFID |
| 16/17 | Serial4 | Topic RFID |
| 20/21 | Serial5 | Group RFID |
| 22 | `debugPin` | Boot jumper → GND = `debugMode` (verbose serial logging) |
| 23 | `writePin` | Boot jumper → GND = `writeMode` (loop runs `writeTag()` instead of scanning) |

Note: the inline comments on `TPI1`/`TPI2` in `pins.h` are swapped relative to actual use;
the table above reflects the code in `main.cpp`.

## Timing constants & key globals (`main.cpp` unless noted)

| Symbol | Value | Meaning |
|---|---|---|
| `emptySlotTime` | 350 ms | TPI-low debounce before a slot is declared empty |
| `rescanTime` | 10 000 ms | Set on `rescan*Timer` after a confirm — **timers are never checked; dead code** |
| `rfidTimeout` | 5000 (rfidHandler.h) | **Unused** |
| `previous*/current*ID` | init 200–205 | Sentinel "no tag yet" values, outside valid tag range |
| `*Presence` | — | True if that reader's presence watch started OK (3 retries at boot) |
| `*Detected` | — | Latched "tag currently in slot" state |
| USB serial | 115 200 baud | `setup()` blocks on `while(!Serial)` — **firmware hangs until a USB host connects** |
| Loop pacing | `FastLED.show(); delay(50)` | ~20 Hz main loop in scan mode |

## Boot sequence (`setup()`)

1. `Serial.begin(115200)`, block until USB connected.
2. `setModePins()` → `checkModePins()`: sample pins 22/23 → `debugMode`/`writeMode` (boot-time only).
3. `setPins()`: LED/power/TPI/button pins; RFID power on.
4. `startRfidSerial()`: each reader `begin(9600)` + `dummyCommand()` connectivity check.
5. `setLED()`: register FastLED strips, run ~4 s red/blue/green test.
6. `stopPolling()` all readers (in case of soft reset), then `resume*PresenceWatch()` — puts each
   B1 in polling mode with only its TPI output active (no UART traffic per check).

## Loop state machine (identical per category; group shown)

- **Idle/scanning** (`!detected && !TPI`): `scanLED(n)` pulses the ring white (`beatsin8(16)`).
- **TPI sampling:** if presence watch is up, `TPI = !digitalRead(pin)`; while TPI high, the
  empty-slot debounce timer is continually re-armed.
- **Tag arrival** (`TPI && !detected`): set `detected`; `stopPolling()`; `get*Data()` reads page 5
  and matches against the known-tag list (match → `sendTag(id, n)` inside the getter). If the ID
  differs from `previous*ID`, latch it and `confirmLED(n)`. Then restart presence watch.
- **Tag removal** (`!TPI && detected && debounce expired`): clear `detected`, `previous*ID = 0`,
  `sendTag(0, n)` → host sees `n:0x0`.
- `buttonCheck()`: language button press → prints `L`.
- Write mode replaces all of the above with `writeTag()` (missing `write.h`) plus a 5 s
  "Press 'w' to continue..." prompt.

## Serial protocol (USB, 115200)

Output, one event per line:

- `<category>:0x<ID>` — tag placed (e.g. `3:0x19`), or slot emptied (`3:0x0`). Hex has no
  zero-padding and category is a single digit `1|2|3`.
- `L` — language button pressed.
- With `debugMode` on, human-readable debug lines are interleaved — **a host parser must tolerate
  arbitrary extra lines** (topic TPI state is printed every loop in debug mode).

Input: none in normal scan mode. (`T`/`W` commands mentioned in the boot banner are handled only by
the missing `write.h`.)

## RFID_B1 library (lib/RFID_B1) — what an agent needs

UART driver for the B1 reader module, 9600 baud, STX + size + CRC packet framing (details in
`include/PROTOCOL_REFERENCE.md`). Methods actually used by this firmware:
`begin(baud)`, `dummyCommand()`, `startPresenceWatch(periodX100ms)` (polling with only the TPI
hardware pin active), `stopPolling()`, `getUIDandType()`, `readNTAG215(startPage, numPages, buf)`,
`printBuffer()`. Also available (unused here): `writeNTAG215*`, `readPage`/`writePage`,
`pollForPacket`, `setDefinedTagList` + `unlock`/`lock`, password auth, data-buffer ops, and
`getTagUID`/`getTagType`/`getLastResult` with name-lookup helpers. Per the B1 manual, call
`stopPolling()` before `getUIDandType()` — which is exactly what the state machine does.

## Known discrepancies & quirks (verified in code — do not "fix" silently)

1. **`write.h` missing** → project doesn't build (see Build section).
2. **`Documentation/Firmware/RFID Group Tags by Hex.md` contradicts the code**: it assigns
   Group=0x01–0x0C/Serial3, Interest=0x0D–0x18, Topic=0x19–0x24. The code (authoritative) is
   Interest=0x01–0x0C/Serial3, Topic=0x0D–0x18/Serial4, Group=0x19–0x24/Serial5.
3. Only `groupCheck()` guards the confirm with `currentGroupID != 0`; topic/interest confirm and
   latch even when the read failed/matched nothing. Also `getTopicData()`/`getInterestData()`
   return the *stale previous* tag on a failed match, while `getGroupData()` returns 0.
4. `rescan*Timer`s are set but never read; `rfidTimeout` unused; `BTN_1_PWM` never driven.
5. Copy-pasted debug strings: `topicCheck()` logs "Group Slot is probably empty."; all three
   getters log "Matched group tag".
6. `specificData[]` read buffer is shared across all three readers (fine while reads are
   sequential in one loop).
7. `pins.h` TPI comments are swapped (see pin map note).

## Related documents

- `Firmware/include/PROTOCOL_REFERENCE.md` — B1 UART packet framing + worked examples.
- `Documentation/Firmware/RFID Group Tags by Hex.md` — tag ID assignments (**names wrong**, see above).
- `Documentation/Firmware/Firmware Tests/` — older standalone test project ("00_Three RFIDs Read and Write").
