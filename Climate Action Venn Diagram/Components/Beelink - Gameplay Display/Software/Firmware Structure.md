# System Structure — Venn Diagram Firmware

The Venn Diagram software targets a **Teensy 4.0** that drives three RFID readers (one per Venn diagram
category) and their LED rings, and reports tag events to the media player over USB serial.

## Serial protocol (USB, 115200)

- `<category>:0x<ID>` — tag placed and matched (e.g. `3:0x19`), or slot emptied (`3:0x0`). Hex has
  no zero-padding and category is a single digit `1|2|3`.
- `L` — language button pressed.
- If a read fails or matches no known tag, **no line is sent** for that placement and there is no
  retry until the tag is removed (after the 350 ms debounce) and placed again.

Input: none in normal scan mode. (`T`/`W` commands mentioned in the boot banner are handled only by
the missing `write.h`.)
