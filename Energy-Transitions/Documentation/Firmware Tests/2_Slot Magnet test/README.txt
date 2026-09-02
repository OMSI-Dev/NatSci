
===============================================================================
FIRMWARE TEST 2: SLOT MAGNET POLARITY TEST
===============================================================================

PURPOSE:
--------
This test validates Hall effect sensor reading and polarity classification
on the ItsyBitsy M0 Express pill slot board. It reads the three SS39ET 
sensors and displays the detected polarity using both the indicator LEDs
and the LED ring.

This is a simplified test that demonstrates the core sensor reading
functionality from the working main firmware, without the I2C communication,
state machine, or game logic.

FUNCTIONALITY:
--------------
- Reads 3 Hall effect sensors with ADC averaging (5 samples per read)
- Classifies polarity using hysteresis thresholds to prevent oscillation
- Displays results on both indicator LEDs and LED ring in real-time
- Outputs sensor readings to Serial monitor every 500ms

LED DISPLAY:
------------
Indicator LEDs (green, standard LEDs):
  - S1 (pin 11): ON when S1 has definite polarity (S or N), OFF when uncertain
  - S2 (pin 10): ON when S2 has definite polarity (S or N), OFF when uncertain
  - S3 (pin 9):  ON when S3 has definite polarity (S or N), OFF when uncertain

LED Ring (20 WS2812 LEDs, divided into 3 segments):
  - Segment 1 (LEDs 0-6):   Sensor 1 (S1) polarity
  - Segment 2 (LEDs 7-13):  Sensor 2 (S2) polarity
  - Segment 3 (LEDs 14-19): Sensor 3 (S3) polarity
  
  Colors:
  - RED = SOUTH pole detected
  - BLUE = NORTH pole detected
  - DIM WHITE = UNCERTAIN (no definite polarity)

THRESHOLDS:
-----------
Based on 12-bit ADC with 3.3V reference, adjusted for milkplex barrier:
  - SOUTH: < 1650 mV (enter) / < 1750 mV (stay)
  - NORTH: > 2450 mV (enter) / > 2350 mV (stay)
  - UNCERTAIN: Between thresholds

Hysteresis prevents oscillation when sensor readings are near boundaries.

PINOUT:
-------
**ItsyBitsy M0 Express**
Hall Effect Sensors:
  - Sen1_OUT → Pin A0 (S1, middle sensor)
  - Sen2_OUT → Pin A1 (S2, left sensor)
  - Sen3_OUT → Pin A2 (S3, right sensor)

Indicator LEDs (green):
  - Sen1_LED → Pin 11 (S1 indicator)
  - Sen2_LED → Pin 10 (S2 indicator)
  - Sen3_LED → Pin 9  (S3 indicator)

LED Ring:
  - Data → Pin 2 (WS2812 chain, 20 LEDs)

Physical Layout (PCB, left to right):
  S2 — S1 — S3

SERIAL OUTPUT EXAMPLE:
----------------------
       S2      S1      S3    (physical L→R)
RAW:   2048    1580    2890
POL:    X       S       N

       S2      S1      S3    (physical L→R)
RAW:   2048    1580    2890
POL:    X       S       N

Legend: X = UNCERTAIN, S = SOUTH, N = NORTH

HOW TO USE:
-----------
1. Upload firmware to ItsyBitsy M0 Express
2. Open Serial monitor (115200 baud)
3. Place magnetic game piece in slot
4. Observe:
   - Indicator LEDs turn on for sensors with definite readings
   - Ring LED segments change color based on polarity
   - Serial monitor shows raw ADC values and classified polarities
5. Remove piece and observe LEDs return to uncertain state

CHANGES FROM ORIGINAL TEST 2:
------------------------------
- Removed I2C communication and addressing logic
- Removed state machine (IDLE, DEBOUNCING, REGISTERING, CORRECT/INCORRECT)
- Removed pattern matching and correctness validation
- Removed registration confirmation logic
- Simplified to continuous real-time polarity display
- Added indicator LED support from Test 00
- Reduced code from ~800 lines to ~300 lines

Updated: 2026-08-04
Version: 1.0 (Simplified)

