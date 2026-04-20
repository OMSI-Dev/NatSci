/*
 * TEST 2 - M0 BOARD - SS39ET POLARITY DETECTION
 *
 * Reads three Hall effect sensors, classifies each as SOUTH / NORTH / UNCERTAIN,
 * confirms polarity after CONFIRM_SAMPLES consecutive agreeing reads per sensor,
 * checks correctness against this board's I2C address, lights the LED ring, and
 * reports status to the Teensy via I2C on request.
 *
 * Thresholds (12-bit ADC, 3.3 V ref):
 *   ADJUSTED FOR MILKPLEX BARRIER (2026-04-20):
 *   SOUTH      raw < 1700  (~1370 mV) - increased from 1450 for weaker field
 *   NORTH      raw > 2400  (~1935 mV) - decreased from 2800 for weaker field
 *   UNCERTAIN  1700–2400   (no magnet or in transition)
 *
 *   Original calibration (2026-04-17, no barrier):
 *   SOUTH < 1450 (~1168 mV), NORTH > 2800 (~2256 mV)
 *
 * Expected correct patterns:
 *   0x08  Buoy  S S S
 *   0x09  Dam   N N N
 *
 * LEDs:
 *   Any magnetism detected (REGISTERING) → dim white
 *   Confirmed correct                    → dim green
 *   Confirmed incorrect                  → dim red
 *   No magnet (IDLE)                     → off
 *
 * I2C TX packet (6 bytes, returned to Teensy on requestFrom):
 *   [0] state   0=IDLE  1=REGISTERING  2=CORRECT  3=INCORRECT
 *   [1] S1 pol  0=UNCERTAIN  1=SOUTH  2=NORTH
 *   [2] S2 pol
 *   [3] S3 pol
 *   [4] I2C address low byte
 *   [5] 0x00 reserved
 */

#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>
#include <i2C_Address.h>

// ── Sensor pins ───────────────────────────────────────────────────────────────
#define SENSOR_1_PIN  A0
#define SENSOR_2_PIN  A1
#define SENSOR_3_PIN  A2

// ── ADC thresholds (12-bit) ───────────────────────────────────────────────────
// Adjusted for milkplex barrier - more lenient detection
// Increase THRESHOLD_SOUTH to catch weaker south pole readings
// Decrease THRESHOLD_NORTH to catch weaker north pole readings
#define THRESHOLD_SOUTH  1700  // Was 1450 - raised for milkplex barrier
#define THRESHOLD_NORTH  2400  // Was 2800 - lowered for milkplex barrier

// If detection is still unreliable with barrier, try:
// THRESHOLD_SOUTH  1800
// THRESHOLD_NORTH  2300

// ── Registration: samples each sensor must hold the same polarity ─────────────
#define CONFIRM_SAMPLES  10

// ── LED ring ──────────────────────────────────────────────────────────────────
#define LED_PIN   2
#define NUM_LEDS  20
CRGB leds[NUM_LEDS];

// ── Types ─────────────────────────────────────────────────────────────────────
enum Polarity    : uint8_t { POL_UNCERTAIN = 0, POL_SOUTH = 1, POL_NORTH = 2 };
enum DetectState : uint8_t { STATE_IDLE = 0, STATE_REGISTERING = 1,
                             STATE_CORRECT = 2, STATE_INCORRECT = 3 };

struct SensorTrack {
  Polarity confirmed;
  Polarity candidate;
  uint8_t  count;
  bool     locked;
};

// ── Globals ───────────────────────────────────────────────────────────────────
uint16_t    i2cAddress  = 0x08;
DetectState detectState = STATE_IDLE;
SensorTrack track[3];
volatile uint8_t txBuf[6] = { 0, 0, 0, 0, 0x08, 0 };

// ── Helpers ───────────────────────────────────────────────────────────────────
Polarity classify(uint16_t raw) {
  if (raw < THRESHOLD_SOUTH) return POL_SOUTH;
  if (raw > THRESHOLD_NORTH) return POL_NORTH;
  return POL_UNCERTAIN;
}

void resetTracks() {
  for (uint8_t i = 0; i < 3; i++)
    track[i] = { POL_UNCERTAIN, POL_UNCERTAIN, 0, false };
}

void setLEDs(CRGB color) {
  fill_solid(leds, NUM_LEDS, color);
  FastLED.show();
}

void writeTxBuf(DetectState st, Polarity p0, Polarity p1, Polarity p2) {
  noInterrupts();
  txBuf[0] = (uint8_t)st;
  txBuf[1] = (uint8_t)p0;
  txBuf[2] = (uint8_t)p1;
  txBuf[3] = (uint8_t)p2;
  txBuf[4] = (uint8_t)(i2cAddress & 0xFF);
  txBuf[5] = 0x00;
  interrupts();
}

void onRequest() {
  Wire.write((uint8_t*)txBuf, 6);
}

bool isCorrect() {
  if (i2cAddress == 0x08)   // Buoy: S S S
    return track[0].confirmed == POL_SOUTH &&
           track[1].confirmed == POL_SOUTH &&
           track[2].confirmed == POL_SOUTH;
  if (i2cAddress == 0x09)   // Dam: N N N
    return track[0].confirmed == POL_NORTH &&
           track[1].confirmed == POL_NORTH &&
           track[2].confirmed == POL_NORTH;
  return false;
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  analogReadResolution(12);

  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 500);  // Increased from 100mA to 500mA
  FastLED.setBrightness(50);  // Increased from 30 to 50
  setLEDs(CRGB::Black);

  resetTracks();
  writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);

  setPins();
  i2cAddress = setAddr();
  txBuf[4]   = (uint8_t)(i2cAddress & 0xFF);
  
  Serial.print("I2C Address: 0x");
  Serial.println(i2cAddress, HEX);
  
  if (i2cAddress == 0x08) {
    Serial.println("Expected pattern: SOUTH SOUTH SOUTH");
  } else if (i2cAddress == 0x09) {
    Serial.println("Expected pattern: NORTH NORTH NORTH");
  } else {
    Serial.println("No correct pattern defined for this address");
  }
  
  Wire.begin(i2cAddress);
  Wire.onRequest(onRequest);
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  static const uint8_t PINS[3] = { SENSOR_1_PIN, SENSOR_2_PIN, SENSOR_3_PIN };

  Polarity cur[3];
  for (uint8_t i = 0; i < 3; i++) cur[i] = classify(analogRead(PINS[i]));

  bool allUncertain = (cur[0] == POL_UNCERTAIN &&
                       cur[1] == POL_UNCERTAIN &&
                       cur[2] == POL_UNCERTAIN);

  switch (detectState) {

    // ── IDLE ──────────────────────────────────────────────────────────────────
    case STATE_IDLE:
      if (!allUncertain) {
        resetTracks();
        detectState = STATE_REGISTERING;
        setLEDs(CRGB(50, 50, 50));  // dim white — magnetism detected, acquiring
        writeTxBuf(STATE_REGISTERING, cur[0], cur[1], cur[2]);
      }
      break;

    // ── REGISTERING ───────────────────────────────────────────────────────────
    case STATE_REGISTERING: {
      if (allUncertain) {
        // Object removed before confirmation — re-arm
        resetTracks();
        detectState = STATE_IDLE;
        setLEDs(CRGB::Black);
        writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);
        break;
      }

      bool allLocked = true;
      for (uint8_t i = 0; i < 3; i++) {
        if (track[i].locked) continue;

        if (cur[i] == POL_UNCERTAIN) {
          track[i].candidate = POL_UNCERTAIN;
          track[i].count     = 0;
          allLocked          = false;
        } else if (cur[i] == track[i].candidate) {
          track[i].count++;
          if (track[i].count >= CONFIRM_SAMPLES) {
            track[i].confirmed = track[i].candidate;
            track[i].locked    = true;
          } else {
            allLocked = false;
          }
        } else {
          track[i].candidate = cur[i];
          track[i].count     = 1;
          allLocked          = false;
        }
      }

      writeTxBuf(STATE_REGISTERING, cur[0], cur[1], cur[2]);

      if (allLocked) {
        bool correct = isCorrect();
        detectState  = correct ? STATE_CORRECT : STATE_INCORRECT;
        
        Serial.print("All sensors locked! S1:");
        Serial.print(track[0].confirmed);
        Serial.print(" S2:");
        Serial.print(track[1].confirmed);
        Serial.print(" S3:");
        Serial.print(track[2].confirmed);
        Serial.print(" -> ");
        Serial.println(correct ? "CORRECT (GREEN)" : "INCORRECT (RED)");
        
        setLEDs(correct ? CRGB(0, 100, 0) : CRGB(100, 0, 0));  // dim green / dim red
        writeTxBuf(detectState,
                   track[0].confirmed,
                   track[1].confirmed,
                   track[2].confirmed);
      }
      break;
    }

    // ── CORRECT / INCORRECT — wait for object removal ─────────────────────────
    case STATE_CORRECT:
    case STATE_INCORRECT:
      if (allUncertain) {
        resetTracks();
        detectState = STATE_IDLE;
        setLEDs(CRGB::Black);
        writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);
      }
      break;
  }

  delay(10);
}

