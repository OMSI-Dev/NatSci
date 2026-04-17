========================================
  TEST 1 - ADDRESSING AND COMMUNICATION
========================================

OBJECTIVE:
- M0 boards initialize I2C addresses from GPIO header pins
- Teensy waits for 2x M0 boards to appear on I2C bus
- Once both M0 boards are detected, establish active bidirectional communication

HARDWARE SETUP:
===============

** 2x M0 BOARDS **
- Each M0 gets unique I2C address from GPIO pins (A=3, B=4, C=12, D=7)
- Connect GPIO pins to GND or leave floating to set address (0x08-0x11)
- Both M0 boards share the same I2C bus

** TEENSY 4.1 (MASTER) **
- Pin 18 (SDA) - connect to both M0 SDA pins
- Pin 19 (SCL) - connect to both M0 SCL pins
- GND - connect to both M0 GND pins
- 4.7kΩ pull-up resistors on SDA and SCL to 3.3V

WIRING DIAGRAM:
===============
                    Teensy 4.1
                  +-----------+
                  |           |
          Pin 18  |  SDA      |  --- (4.7kΩ to 3.3V)
                  |           |       |
                  |           |       +---> M0 #1 Pin 26 (SDA)
                  |           |       |
                  |           |       +---> M0 #2 Pin 26 (SDA)
                  |           |
          Pin 19  |  SCL      |  --- (4.7kΩ to 3.3V)
                  |           |       |
                  |           |       +---> M0 #1 Pin 27 (SCL)
                  |           |       |
                  |           |       +---> M0 #2 Pin 27 (SCL)
                  |           |
                  |  GND      |  ----+---> M0 #1 GND
                  |           |      |
                  |           |      +---> M0 #2 GND
                  +-----------+

M0 ADDRESS CONFIGURATION:
=========================
Using GPIO pins 3, 4, 12, 7 (A, B, C, D):
- All floating (HIGH with INPUT_PULLUP): Address 0x08
- Pin 3 to GND (A=1):                    Address 0x09
- Pin 4 to GND (B=1):                    Address 0x0A
- Pin 3+4 to GND (A=1, B=1):             Address 0x0B
- etc... (see i2C_Address.h for full mapping)

For this test, configure:
- M0 Board #1: All pins floating → Address 0x08
- M0 Board #2: Pin 3 to GND     → Address 0x09

COMMUNICATION PROTOCOL:
=======================

M0 -> TEENSY (Request/Response):
- M0 sends incrementing counter value when requested
- Counter increments with each request

TEENSY -> M0 (Commands):
- 0xFF: Turn LEDs ON (white)
- 0x00: Turn LEDs OFF
- 0x01-0x0F: Set LED color by hue

EXPECTED BEHAVIOR:
==================

M0 BOARDS:
- Initialize with unique I2C addresses
- Print heartbeat every 5 seconds
- Show [RX] when receiving commands
- Show [TX] when sending counter data
- LEDs respond to commands from Teensy

TEENSY BOARD:
- Scan for M0 devices every 3 seconds
- Wait until 2 devices are detected
- Once ready, communicate every 1 second:
  * Request counter from each M0
  * Send cycling commands (ON/OFF/colors)
- Display all communication via serial

SERIAL COMMANDS (Teensy):
=========================
s - Manual scan for M0 devices
i - Show system status
h - Show help

SUCCESS CRITERIA:
=================
✓ Both M0 boards report correct unique addresses
✓ Teensy detects both M0 boards
✓ Teensy shows "SYSTEM READY"
✓ Counter values increment on both M0 boards
✓ LEDs respond to commands from Teensy
✓ No communication errors

========================================

Reference pinouts:

**M0 Express**
Sensors to M0 Express
1. Sen1_OUT to Pin A0
2. Sen2_OUT to Pin A1
3. Sen3_OUT to Pin A2

**Teensy 4.1**
4-Pin Phoenix to Sensor 1
1. SCL to Pin 19 of Teensy 4.1
2. SDA to Pin 18 of Teensy 4.1
3. GND to GND 
4. 3.3V to 3.3V

