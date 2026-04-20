========================================
  TEST 2 - SLOT MAGNET DETECTION
========================================

OBJECTIVE:
- M0 boards read 3x Hall effect sensors (SS39ET) to detect magnet polarity
- Confirm correct magnet pattern based on I2C address
- Send detection status to Teensy via I2C
- Light LED ring based on detection state

HARDWARE SETUP:
===============

** M0 BOARDS **
- 3x SS39ET Hall effect sensors connected to A0, A1, A2
- LED ring on Pin 2 (20 LEDs)
- I2C address from GPIO pins (0x08 = Buoy, 0x09 = Dam)
- Milkplex barrier layer between magnets and sensors

** HALL SENSOR WIRING **
- SS39ET sensor (3 pins):
  Pin 1 (VCC) → 3.3V
  Pin 2 (OUT) → M0 analog pin (A0/A1/A2)
  Pin 3 (GND) → GND

** EXPECTED MAGNET PATTERNS **
- Address 0x08 (Buoy):  SOUTH SOUTH SOUTH
- Address 0x09 (Dam):   NORTH NORTH NORTH

DETECTION THRESHOLDS (12-bit ADC):
===================================

** ADJUSTED FOR MILKPLEX BARRIER (2026-04-20) **
- SOUTH pole:      raw < 1700 (~1.37V)
- NORTH pole:      raw > 2400 (~1.94V)
- UNCERTAIN:       1700 - 2400 (no magnet or transition)

Note: Thresholds were adjusted from original calibration
      (SOUTH < 1450, NORTH > 2800) to account for weaker
      magnetic field through milkplex barrier.

** IF DETECTION IS UNRELIABLE **
Try more aggressive thresholds:
- SOUTH < 1800
- NORTH > 2300

DETECTION STATES:
=================

IDLE (0):
- No magnetic field detected
- LEDs: OFF
- Waiting for object insertion

REGISTERING (1):
- Magnetism detected, confirming polarity
- Requires 10 consecutive consistent readings per sensor
- LEDs: Dim white (15,15,15)

CORRECT (2):
- All sensors confirmed correct pattern
- LEDs: Dim green (0,30,0)
- Waits for object removal

INCORRECT (3):
- Wrong magnet pattern detected
- LEDs: Dim red (30,0,0)
- Waits for object removal

I2C COMMUNICATION:
==================

M0 → TEENSY (6 bytes on requestFrom):
- Byte 0: State (0=IDLE, 1=REGISTERING, 2=CORRECT, 3=INCORRECT)
- Byte 1: Sensor 1 polarity (0=UNCERTAIN, 1=SOUTH, 2=NORTH)
- Byte 2: Sensor 2 polarity
- Byte 3: Sensor 3 polarity
- Byte 4: I2C address (low byte)
- Byte 5: Reserved (0x00)

EXPECTED BEHAVIOR:
==================

M0 BOARD:
1. Powers up, reads I2C address from GPIO
2. Starts in IDLE state, LEDs off
3. When magnet approaches:
   - Enters REGISTERING (dim white)
   - Samples each sensor 10 times
   - Confirms polarity for each sensor
4. After confirmation:
   - CORRECT: green if pattern matches address
   - INCORRECT: red if pattern doesn't match
5. Returns to IDLE when magnet removed

TEENSY BOARD:
- Continuously polls M0 boards via I2C
- Displays detection state and polarity readings
- Shows when correct/incorrect patterns detected

CALIBRATION & TROUBLESHOOTING:
==============================

** If sensors don't detect magnets through barrier:**
1. Check sensor wiring and power
2. Test sensors without barrier first
3. Increase THRESHOLD_SOUTH (try 1800, 1850, 1900)
4. Decrease THRESHOLD_NORTH (try 2300, 2250, 2200)

** If false triggers occur:**
1. Decrease THRESHOLD_SOUTH (make more strict)
2. Increase THRESHOLD_NORTH (make more strict)
3. Check for electromagnetic interference

** To recalibrate:**
1. Place correct magnet in slot
2. Monitor serial output for raw ADC values
3. Note minimum (south) and maximum (north) readings
4. Set thresholds with ~200-300 count margin

SUCCESS CRITERIA:
=================
✓ M0 detects magnet insertion (IDLE → REGISTERING)
✓ All 3 sensors confirm correct polarity
✓ Correct pattern shows green LED
✓ Wrong pattern shows red LED
✓ Teensy receives accurate status via I2C
✓ System resets to IDLE when magnet removed

========================================
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

