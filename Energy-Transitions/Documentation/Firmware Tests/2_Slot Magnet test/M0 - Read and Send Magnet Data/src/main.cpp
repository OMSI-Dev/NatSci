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
 *   0x08  None   Buoy   S S S
 *   0x09  A      Dam    N N N
 *   0x0A  B      Geo    N S X
 *   0x0B  C      Geo    X N S
 *   0x0C  D      Solar  N X X
 *   0x0D  AB     Solar  X X N
 *   0x0E  AC     Wind   N N X
 *   0x0F  AD     Wind   X N N
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

// ── ItsyBitsy M0 DotStar LED pins ─────────────────────────────────────────────
#define DOTSTAR_DATA  41
#define DOTSTAR_CLK   40

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

// Turn off DotStar LED (APA102 protocol)
void turnOffDotStar() {
  pinMode(DOTSTAR_DATA, OUTPUT);
  pinMode(DOTSTAR_CLK, OUTPUT);
  
  // Start frame (32 bits of 0)
  for (uint8_t i = 0; i < 32; i++) {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, LOW);
    digitalWrite(DOTSTAR_CLK, HIGH);
  }
  
  // LED frame: brightness=0, R=0, G=0, B=0
  // First byte: 111xxxxx where x=brightness (all 0s = off)
  for (uint8_t bit = 0; bit < 8; bit++) {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, (bit < 3) ? HIGH : LOW);  // 111 prefix
    digitalWrite(DOTSTAR_CLK, HIGH);
  }
  // RGB bytes (all zeros)
  for (uint8_t i = 0; i < 24; i++) {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, LOW);
    digitalWrite(DOTSTAR_CLK, HIGH);
  }
  
  // End frame
  for (uint8_t i = 0; i < 32; i++) {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, LOW);
    digitalWrite(DOTSTAR_CLK, HIGH);
  }
  
  // Leave pins in safe state
  digitalWrite(DOTSTAR_CLK, LOW);
  digitalWrite(DOTSTAR_DATA, LOW);
  pinMode(DOTSTAR_DATA, INPUT);
  pinMode(DOTSTAR_CLK, INPUT);
}

bool isCorrect() {
  Polarity p0 = track[0].confirmed;
  Polarity p1 = track[1].confirmed;
  Polarity p2 = track[2].confirmed;
  
  switch (i2cAddress) {
    case 0x08:  // None/Buoy: S S S
      return p0 == POL_SOUTH && p1 == POL_SOUTH && p2 == POL_SOUTH;
    
    case 0x09:  // A/Dam: N N N
      return p0 == POL_NORTH && p1 == POL_NORTH && p2 == POL_NORTH;
    
    case 0x0A:  // B/Geo: N S X
      return p0 == POL_NORTH && p1 == POL_SOUTH && p2 == POL_UNCERTAIN;
    
    case 0x0B:  // C/Geo: X N S
      return p0 == POL_UNCERTAIN && p1 == POL_NORTH && p2 == POL_SOUTH;
    
    case 0x0C:  // D/Solar: N X X
      return p0 == POL_NORTH && p1 == POL_UNCERTAIN && p2 == POL_UNCERTAIN;
    
    case 0x0D:  // AB/Solar: X X N
      return p0 == POL_UNCERTAIN && p1 == POL_UNCERTAIN && p2 == POL_NORTH;
    
    case 0x0E:  // AC/Wind: N N X
      return p0 == POL_NORTH && p1 == POL_NORTH && p2 == POL_UNCERTAIN;
    
    case 0x0F:  // AD/Wind: X N N
      return p0 == POL_UNCERTAIN && p1 == POL_NORTH && p2 == POL_NORTH;
    
    default:
      return false;
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  analogReadResolution(12);

  // Initialize WS2812 LED ring first
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 750);
  FastLED.setBrightness(75);
  setLEDs(CRGB::Black);
  
  // Turn off DotStar after LED ring is initialized
  turnOffDotStar();

  resetTracks();
  writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);

  setPins();
  i2cAddress = setAddr();
  txBuf[4]   = (uint8_t)(i2cAddress & 0xFF);
  
  Serial.println("\n=== M0 BOARD INITIALIZED ===");
  Serial.print("I2C Address: 0x");
  Serial.println(i2cAddress, HEX);
  Serial.print("Expected Pattern: ");
  
  switch (i2cAddress) {
    case 0x08: Serial.println("Buoy - S S S"); break;
    case 0x09: Serial.println("Dam - N N N"); break;
    case 0x0A: Serial.println("Geo - N S X"); break;
    case 0x0B: Serial.println("Geo - X N S"); break;
    case 0x0C: Serial.println("Solar - N X X"); break;
    case 0x0D: Serial.println("Solar - X X N"); break;
    case 0x0E: Serial.println("Wind - N N X"); break;
    case 0x0F: Serial.println("Wind - X N N"); break;
    default: Serial.println("UNKNOWN"); break;
  }
  Serial.println("============================\n");
  
  Wire.begin(i2cAddress);
  Wire.onRequest(onRequest);
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  static const uint8_t PINS[3] = { SENSOR_1_PIN, SENSOR_2_PIN, SENSOR_3_PIN };
  static uint32_t lastDebug = 0;

  Polarity cur[3];
  uint16_t raw[3];
  for (uint8_t i = 0; i < 3; i++) {
    raw[i] = analogRead(PINS[i]);
    cur[i] = classify(raw[i]);
  }

  bool allUncertain = (cur[0] == POL_UNCERTAIN &&
                       cur[1] == POL_UNCERTAIN &&
                       cur[2] == POL_UNCERTAIN);

  switch (detectState) {

    // ── IDLE ──────────────────────────────────────────────────────────────────
    case STATE_IDLE:
      if (!allUncertain) {
        resetTracks();
        detectState = STATE_REGISTERING;
        Serial.println("\n>>> MAGNETISM DETECTED - STARTING REGISTRATION <<<");
        setLEDs(CRGB(50, 50, 50));  // dim white — magnetism detected, acquiring
        writeTxBuf(STATE_REGISTERING, cur[0], cur[1], cur[2]);
      }
      break;

    // ── REGISTERING ───────────────────────────────────────────────────────────
    case STATE_REGISTERING: {
      static uint32_t registerStartTime = 0;
      static bool timerStarted = false;
      
      if (!timerStarted) {
        registerStartTime = millis();
        timerStarted = true;
      }
      
      if (allUncertain) {
        // Object removed before confirmation — re-arm
        resetTracks();
        detectState = STATE_IDLE;
        timerStarted = false;
        setLEDs(CRGB::Black);
        writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);
        break;
      }

      bool allLocked = true;
      for (uint8_t i = 0; i < 3; i++) {
        if (track[i].locked) continue;

        if (cur[i] == track[i].candidate) {
          // Current reading matches candidate - increment count
          track[i].count++;
          if (track[i].count >= CONFIRM_SAMPLES) {
            track[i].confirmed = track[i].candidate;
            track[i].locked    = true;
          } else {
            allLocked = false;
          }
        } else if (cur[i] == POL_UNCERTAIN && track[i].candidate != POL_UNCERTAIN && track[i].count >= 5) {
          // Reading UNCERTAIN but have a strong S/N candidate (5+ samples)
          // Slowly decrement count instead of resetting (protects Buoy from false X)
          if (track[i].count > 0) track[i].count--;
          allLocked = false;
        } else {
          // New candidate reading or weak candidate - allow switch
          track[i].candidate = cur[i];
          track[i].count     = 1;
          allLocked          = false;
        }
      }
      
      // Force-lock timeout: if we've been registering for 3+ seconds and a sensor
      // is currently reading UNCERTAIN, lock it as UNCERTAIN (handles Wind pattern)
      if (millis() - registerStartTime > 3000) {
        for (uint8_t i = 0; i < 3; i++) {
          if (!track[i].locked && cur[i] == POL_UNCERTAIN) {
            Serial.print("FORCE-LOCKING sensor ");
            Serial.print(i + 1);
            Serial.println(" as UNCERTAIN (timeout)");
            track[i].confirmed = POL_UNCERTAIN;
            track[i].locked = true;
          }
        }
      }

      writeTxBuf(STATE_REGISTERING, cur[0], cur[1], cur[2]);

      // Debug output every 500ms
      if (millis() - lastDebug > 500) {
        Serial.print("RAW: ");
        Serial.print(raw[0]); Serial.print("\t"); 
        Serial.print(raw[1]); Serial.print("\t"); 
        Serial.println(raw[2]);
        
        Serial.print("CUR: ");
        Serial.print(cur[0]); Serial.print("\t"); 
        Serial.print(cur[1]); Serial.print("\t"); 
        Serial.println(cur[2]);
        
        Serial.print("Candidate: ");
        Serial.print(track[0].candidate); Serial.print("\t"); 
        Serial.print(track[1].candidate); Serial.print("\t"); 
        Serial.println(track[2].candidate);
        
        Serial.print("Count: ");
        Serial.print(track[0].count); Serial.print("/"); Serial.print(track[0].locked ? "LOCK" : "....");
        Serial.print("\t");
        Serial.print(track[1].count); Serial.print("/"); Serial.print(track[1].locked ? "LOCK" : "....");
        Serial.print("\t");
        Serial.print(track[2].count); Serial.print("/"); Serial.println(track[2].locked ? "LOCK" : "....");
        Serial.println();
        
        lastDebug = millis();
      }

      if (allLocked) {
        bool correct = isCorrect();
        detectState  = correct ? STATE_CORRECT : STATE_INCORRECT;
        timerStarted = false;  // Reset timer for next registration
        
        Serial.print("\n=== ALL LOCKED === S1:");
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
        Serial.println(">>> MAGNET REMOVED - BACK TO IDLE <<<\n");
        resetTracks();
        detectState = STATE_IDLE;
        setLEDs(CRGB::Black);
        writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);
      }
      break;
  }

  delay(10);
}

