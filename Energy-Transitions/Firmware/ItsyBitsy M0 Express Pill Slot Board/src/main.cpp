/*
 * HALL EFFECT SENSOR POLARITY DETECTION - ItsyBitsy M0 Express
 * 
 * Reads three SS39ET Hall effect sensors to detect magnetic game piece patterns.
 * Features noise-filtered ADC readings, hysteresis-based classification, and
 * debounced registration to ensure stable, reliable pattern detection.
 *
 * DETECTION FLOW:
 *   IDLE → DEBOUNCING → REGISTERING → CORRECT/INCORRECT → IDLE
 *
 * SENSOR CONFIGURATION:
 *   Physical PCB layout (left to right): S2 — S1 — S3
 *   Code mapping: p0=S1 (middle), p1=S2 (left), p2=S3 (right)
 *
 * ADC THRESHOLDS (12-bit, 3.3V ref, adjusted for milkplex barrier):
 *   SOUTH:     < 1650 mV (enter) / < 1750 mV (stay)
 *   NORTH:     > 2450 mV (enter) / > 2350 mV (stay)
 *   UNCERTAIN: Between thresholds
 *   Hysteresis prevents boundary oscillation during transitions.
 *
 * PIECE PATTERNS (by I2C address):
 *   Addr   Header  Piece   Physical L→R   p0(S1)  p1(S2)  p2(S3)
 *   0x08   None    Buoy    S  S  S          S       S       S
 *   0x09   A       Dam     N  N  N          N       N       N
 *   0x0A   B       Geo     N  S  X          S       N       X
 *   0x0B   C       Geo     X  N  S          N       X       S
 *   0x0C   D       Solar   N  X  X          X       N       X
 *   0x0D   AB      Solar   X  X  N          X       X       N
 *   0x0E   AC      Wind    N  N  X          N       N       X
 *   0x0F   AD      Wind    X  N  N          N       X       N
 *   (Geo/Solar/Wind patterns accept either orientation via rotation logic)
 *
 * LED FEEDBACK:
 *   IDLE / DEBOUNCING → Off
 *   REGISTERING       → Dim white
 *   CORRECT           → Dim green
 *   INCORRECT         → Dim red
 *
 * I2C INTERFACE:
 *   TX packet (6 bytes on master request):
 *     [0] State:    0=IDLE, 1=DEBOUNCING, 2=REGISTERING, 3=CORRECT, 4=INCORRECT
 *     [1] S1 pol:   0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *     [2] S2 pol:   0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *     [3] S3 pol:   0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *     [4] Address:  Low byte of I2C address
 *     [5] Reserved: 0x00
 *
 * Version: 2.0 (2026-04-21)
 * - Added ADC averaging (5 samples per read)
 * - Implemented hysteresis for stable classification
 * - Added debounce delay (300ms) before registration
 * - Improved candidate switching with stability requirements
 * - Enhanced code documentation and structure
 */

#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>
#include <i2C_Address.h>

// ── Sensor pins ───────────────────────────────────────────────────────────────
#define SENSOR_1_PIN  A0
#define SENSOR_2_PIN  A1
#define SENSOR_3_PIN  A2

// ── DotStar pins (ItsyBitsy M0) ───────────────────────────────────────────────
#define DOTSTAR_DATA  41
#define DOTSTAR_CLK   40

// ── ADC Configuration ─────────────────────────────────────────────────────────
#define ADC_SAMPLES      5     // Number of ADC readings to average per sensor

// ── ADC Thresholds (12-bit, adjusted for milkplex barrier) ────────────────────
// Hysteresis prevents oscillation near boundaries
#define THRESHOLD_SOUTH_LOW   1650  // Below this = definitely SOUTH
#define THRESHOLD_SOUTH_HIGH  1750  // Above this = leaving SOUTH
#define THRESHOLD_NORTH_LOW   2350  // Below this = leaving NORTH  
#define THRESHOLD_NORTH_HIGH  2450  // Above this = definitely NORTH

// ── Registration Configuration ────────────────────────────────────────────────
#define DEBOUNCE_DELAY_MS     500   // Delay before starting registration (ms)
#define CONFIRM_SAMPLES       10    // Consecutive samples needed to lock polarity
#define CANDIDATE_STABILITY   3     // Consecutive reads needed to switch candidates
#define FORCE_LOCK_TIMEOUT_MS 3000  // Timeout to force-lock uncertain sensors (ms)

// ── LED ring ──────────────────────────────────────────────────────────────────
#define LED_PIN   2
#define NUM_LEDS  20
CRGB leds[NUM_LEDS];

// ── Types ─────────────────────────────────────────────────────────────────────
enum Polarity : uint8_t {
  POL_UNCERTAIN = 0,
  POL_SOUTH     = 1,
  POL_NORTH     = 2
};

enum DetectState : uint8_t {
  STATE_IDLE       = 0,
  STATE_DEBOUNCING = 1,  // New state: waiting before registration
  STATE_REGISTERING = 2,
  STATE_CORRECT    = 3,
  STATE_INCORRECT  = 4
};

struct SensorTrack {
  Polarity confirmed;        // Locked-in polarity
  Polarity candidate;        // Current candidate polarity
  Polarity lastReading;      // Previous reading (for hysteresis)
  Polarity prevCandidate;    // Previous candidate (for stability tracking)
  uint8_t  confirmCount;     // Consecutive matches for confirmation
  uint8_t  candidateCount;   // Consecutive reads for candidate stability
  bool     locked;           // Whether sensor is locked
};

// ── Globals ───────────────────────────────────────────────────────────────────
uint16_t    i2cAddress  = 0x08;
DetectState detectState = STATE_IDLE;
SensorTrack track[3];
volatile uint8_t txBuf[6] = { 0, 0, 0, 0, 0x08, 0 };

// ── ADC and Classification Helpers ───────────────────────────────────────────

/**
 * Read and average multiple ADC samples from a sensor pin.
 * Reduces noise and improves reading stability.
 */
uint16_t readSensorAveraged(uint8_t pin) {
  uint32_t sum = 0;
  for (uint8_t i = 0; i < ADC_SAMPLES; i++) {
    sum += analogRead(pin);
    delayMicroseconds(100);  // Small delay between samples
  }
  return (uint16_t)(sum / ADC_SAMPLES);
}

/**
 * Classify sensor reading with hysteresis to prevent boundary oscillation.
 * Uses lastReading to apply appropriate thresholds based on previous state.
 */
Polarity classifyWithHysteresis(uint16_t raw, Polarity lastReading) {
  // Apply hysteresis based on previous state
  if (lastReading == POL_SOUTH) {
    // Currently SOUTH: need to exceed high threshold to leave
    if (raw < THRESHOLD_SOUTH_HIGH) return POL_SOUTH;
    if (raw > THRESHOLD_NORTH_LOW) return POL_NORTH;
    return POL_UNCERTAIN;
  }
  else if (lastReading == POL_NORTH) {
    // Currently NORTH: need to drop below low threshold to leave
    if (raw > THRESHOLD_NORTH_LOW) return POL_NORTH;
    if (raw < THRESHOLD_SOUTH_HIGH) return POL_SOUTH;
    return POL_UNCERTAIN;
  }
  else {
    // UNCERTAIN: use stricter thresholds to enter S/N
    if (raw < THRESHOLD_SOUTH_LOW) return POL_SOUTH;
    if (raw > THRESHOLD_NORTH_HIGH) return POL_NORTH;
    return POL_UNCERTAIN;
  }
}

/**
 * Reset all sensor tracking state to initial values.
 */
void resetTracks() {
  for (uint8_t i = 0; i < 3; i++) {
    track[i] = {
      POL_UNCERTAIN,  // confirmed
      POL_UNCERTAIN,  // candidate
      POL_UNCERTAIN,  // lastReading
      POL_UNCERTAIN,  // prevCandidate
      0,              // confirmCount
      0,              // candidateCount
      false           // locked
    };
  }
}

void setLEDs(CRGB color) {
  fill_solid(leds, NUM_LEDS, color);
  FastLED.show();
}

/**
 * Update I2C transmit buffer with current state and sensor polarities.
 * Thread-safe with interrupt protection.
 */
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

/**
 * I2C request handler - sends current state to master device.
 */
void onRequest() {
  Wire.write((uint8_t*)txBuf, 6);
}

/**
 * Turn off on-board DotStar LED using APA102 protocol.
 * Called during setup to prevent interference with external LED ring.
 */
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

/**
 * Verify if detected polarity pattern matches expected pattern for this board.
 * Handles both forward and 180° rotated orientations for asymmetric patterns.
 * 
 * @return true if pattern is correct for this board's I2C address
 */
bool isCorrect() {
  // Sensor mapping: p0=S1 (middle), p1=S2 (left), p2=S3 (right)
  // Physical PCB layout (L→R): S2, S1, S3
  
  Polarity p0 = track[0].confirmed;  // S1 (middle)
  Polarity p1 = track[1].confirmed;  // S2 (left)
  Polarity p2 = track[2].confirmed;  // S3 (right)
  
  switch (i2cAddress) {
    // ── 0x08: Buoy = S S S (symmetric, no rotation needed) ──
    case 0x08:
      return (p0 == POL_SOUTH && p1 == POL_SOUTH && p2 == POL_SOUTH);
    
    // ── 0x09: Dam = N N N (symmetric, no rotation needed) ──
    case 0x09:
      return (p0 == POL_NORTH && p1 == POL_NORTH && p2 == POL_NORTH);
    
    // ── 0x0A, 0x0B: Both Geo boards accept EITHER Geo pattern ──
    // Geo B (0x0A): N S X → forward: p0=S,p1=N,p2=X | reversed: p0=S,p1=X,p2=N
    // Geo C (0x0B): X N S → forward: p0=N,p1=X,p2=S | reversed: p0=N,p1=S,p2=X
    case 0x0A:
    case 0x0B:
      return ((p0 == POL_SOUTH) && ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) || (p1 == POL_UNCERTAIN && p2 == POL_NORTH))) ||
             ((p0 == POL_NORTH) && ((p1 == POL_UNCERTAIN && p2 == POL_SOUTH) || (p1 == POL_SOUTH && p2 == POL_UNCERTAIN)));
    
    // ── 0x0C, 0x0D: Both Solar boards accept EITHER Solar pattern ──
    // Solar D (0x0C):  N X X → forward: p0=X,p1=N,p2=X | reversed: p0=X,p1=X,p2=N
    // Solar AB (0x0D): X X N → forward: p0=X,p1=X,p2=N | reversed: p0=X,p1=N,p2=X
    case 0x0C:
    case 0x0D:
      return (p0 == POL_UNCERTAIN) &&
             ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) || (p1 == POL_UNCERTAIN && p2 == POL_NORTH));
    
    // ── 0x0E, 0x0F: Both Wind boards accept EITHER Wind pattern ──
    // Wind AC (0x0E): N N X → forward: p0=N,p1=N,p2=X | reversed: p0=N,p1=X,p2=N
    // Wind AD (0x0F): X N N → forward: p0=N,p1=X,p2=N | reversed: p0=N,p1=N,p2=X
    case 0x0E:
    case 0x0F:
      return (p0 == POL_NORTH) &&
             ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) || (p1 == POL_UNCERTAIN && p2 == POL_NORTH));
    
    default:
      return false;
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(2500);  // Wait for serial monitor to connect
  
  // Disable on-board LEDs to prevent interference
  turnOffDotStar();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  
  // Configure ADC for 12-bit resolution (0-4095)
  analogReadResolution(12);

  // Initialize external LED ring
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 750);
  FastLED.setBrightness(75);
  setLEDs(CRGB::Black);

  // Initialize sensor tracking and I2C buffer
  resetTracks();
  writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);

  // Read I2C address from hardware pins
  Serial.println("\n=== READING I2C ADDRESS FROM HARDWARE PINS ===");
  setPins();
  i2cAddress = setAddr();
  txBuf[4] = (uint8_t)(i2cAddress & 0xFF);
  Serial.println("==============================================");
  
  // Print startup information
  Serial.println("\n=== HALL EFFECT SENSOR BOARD INITIALIZED ===");
  Serial.print("I2C Address: 0x");
  Serial.println(i2cAddress, HEX);
  Serial.print("Expected Pattern: ");
  
  switch (i2cAddress) {
    case 0x08: Serial.println("Buoy - S S S"); break;
    case 0x09: Serial.println("Dam - N N N"); break;
    case 0x0A: Serial.println("Geo B - N S X"); break;
    case 0x0B: Serial.println("Geo C - X N S"); break;
    case 0x0C: Serial.println("Solar D - N X X"); break;
    case 0x0D: Serial.println("Solar AB - X X N"); break;
    case 0x0E: Serial.println("Wind AC - N N X"); break;
    case 0x0F: Serial.println("Wind AD - X N N"); break;
    default: Serial.println("UNKNOWN"); break;
  }
  
  Serial.print("Configuration: ");
  Serial.print(ADC_SAMPLES); Serial.print(" ADC samples, ");
  Serial.print(CONFIRM_SAMPLES); Serial.print(" confirm samples, ");
  Serial.print(DEBOUNCE_DELAY_MS); Serial.println("ms debounce");
  Serial.println("============================================\n");
  
  // Start I2C peripheral
  Wire.begin(i2cAddress);
  Wire.onRequest(onRequest);
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  static const uint8_t PINS[3] = { SENSOR_1_PIN, SENSOR_2_PIN, SENSOR_3_PIN };
  static uint32_t lastDebug = 0;

  // Read all sensors with averaging and hysteresis
  Polarity cur[3];
  uint16_t raw[3];
  for (uint8_t i = 0; i < 3; i++) {
    raw[i] = readSensorAveraged(PINS[i]);
    cur[i] = classifyWithHysteresis(raw[i], track[i].lastReading);
    track[i].lastReading = cur[i];  // Update for next iteration
  }

  bool allUncertain = (cur[0] == POL_UNCERTAIN &&
                       cur[1] == POL_UNCERTAIN &&
                       cur[2] == POL_UNCERTAIN);

  switch (detectState) {

    // ── IDLE: Waiting for magnet detection ───────────────────────────────────
    case STATE_IDLE:
      if (!allUncertain) {
        resetTracks();
        detectState = STATE_DEBOUNCING;
        Serial.println("\n>>> MAGNETISM DETECTED - DEBOUNCING <<<");
        // Stay dark during debounce - don't light up for transient signals
        writeTxBuf(STATE_DEBOUNCING, cur[0], cur[1], cur[2]);
      }
      break;

    // ── DEBOUNCING: Short delay to filter transient signals ──────────────────
    case STATE_DEBOUNCING: {
      static uint32_t debounceStartTime = 0;
      static bool debounceTimerStarted = false;
      
      if (!debounceTimerStarted) {
        debounceStartTime = millis();
        debounceTimerStarted = true;
      }
      
      if (allUncertain) {
        // Magnet removed during debounce - false trigger
        Serial.println(">>> FALSE TRIGGER - BACK TO IDLE <<<");
        detectState = STATE_IDLE;
        debounceTimerStarted = false;
        writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);
      }
      else if (millis() - debounceStartTime >= DEBOUNCE_DELAY_MS) {
        // Debounce complete - start registration
        Serial.println(">>> DEBOUNCE COMPLETE - STARTING REGISTRATION <<<");
        resetTracks();
        detectState = STATE_REGISTERING;
        debounceTimerStarted = false;
        setLEDs(CRGB(50, 50, 50));  // Dim white - actively acquiring
        writeTxBuf(STATE_REGISTERING, cur[0], cur[1], cur[2]);
      }
      break;
    }

    // ── REGISTERING: Confirming stable polarity pattern ───────────────────────
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

        // Check if current reading matches previous candidate
        if (cur[i] == track[i].prevCandidate) {
          // Same as before - increment stability
          track[i].candidateCount++;
        } else {
          // Different reading - reset stability tracking
          track[i].candidateCount = 1;
          track[i].prevCandidate = cur[i];
        }

        // After CANDIDATE_STABILITY consecutive identical reads, establish as candidate
        if (track[i].candidateCount >= CANDIDATE_STABILITY) {
          if (track[i].candidate != cur[i]) {
            // New candidate established - reset confirmation
            track[i].candidate = cur[i];
            track[i].confirmCount = 0;
          }
        }

        // Check if current reading matches the established candidate
        if (cur[i] == track[i].candidate && track[i].candidateCount >= CANDIDATE_STABILITY) {
          // Reading matches established candidate - increment confirmation
          track[i].confirmCount++;
          
          if (track[i].confirmCount >= CONFIRM_SAMPLES) {
            // Sufficient consecutive matches
            // Lock S/N immediately, but X must wait for force-lock timeout
            if (track[i].candidate == POL_SOUTH || track[i].candidate == POL_NORTH) {
              track[i].confirmed = track[i].candidate;
              track[i].locked = true;
            } else {
              // UNCERTAIN - keep counting, will be force-locked by timeout
              allLocked = false;
            }
          } else {
            allLocked = false;
          }
        }
        else if (cur[i] == POL_UNCERTAIN && 
                 track[i].candidate != POL_UNCERTAIN && 
                 track[i].confirmCount >= 5) {
          // Strong S/N candidate but momentary UNCERTAIN reading
          // Slowly decrement instead of immediate reset
          if (track[i].confirmCount > 0) track[i].confirmCount--;
          allLocked = false;
        }
        else {
          // Reading doesn't match candidate
          if (track[i].confirmCount > 0) track[i].confirmCount--;
          allLocked = false;
        }
      }
      
      // Force-lock timeout: if registering too long, lock stable UNCERTAIN sensors
      // Only locks if sensor has been consistently UNCERTAIN (not flickering)
      if (millis() - registerStartTime > FORCE_LOCK_TIMEOUT_MS) {
        for (uint8_t i = 0; i < 3; i++) {
          if (!track[i].locked && 
              track[i].candidate == POL_UNCERTAIN && 
              track[i].confirmCount >= 5) {
            // Sensor has been stably UNCERTAIN - lock it
            Serial.print("FORCE-LOCKING sensor ");
            Serial.print(i + 1);
            Serial.println(" as UNCERTAIN (stable timeout)");
            track[i].confirmed = POL_UNCERTAIN;
            track[i].locked = true;
          }
        }
      }

      writeTxBuf(STATE_REGISTERING, cur[0], cur[1], cur[2]);

      // Debug output every 500ms during registration
      if (millis() - lastDebug > 500) {
        static const char* POL_LABEL[] = { "  X  ", "  S  ", "  N  " };
        
        Serial.println("         S2      S1      S3    (physical L→R)");
        Serial.print(  "RAW:   ");
        Serial.print(raw[1]); Serial.print("\t");
        Serial.print(raw[0]); Serial.print("\t");
        Serial.println(raw[2]);
        Serial.print(  "CUR:  ");
        Serial.print(POL_LABEL[cur[1]]); Serial.print("   ");
        Serial.print(POL_LABEL[cur[0]]); Serial.print("   ");
        Serial.println(POL_LABEL[cur[2]]);
        Serial.print(  "CAND: ");
        Serial.print(POL_LABEL[track[1].candidate]); Serial.print("   ");
        Serial.print(POL_LABEL[track[0].candidate]); Serial.print("   ");
        Serial.println(POL_LABEL[track[2].candidate]);
        Serial.print(  "PROG: ");
        Serial.print(track[1].confirmCount); Serial.print("/"); Serial.print(CONFIRM_SAMPLES);
        if (track[1].locked) Serial.print(" LOCKED");
        Serial.print("  ");
        Serial.print(track[0].confirmCount); Serial.print("/"); Serial.print(CONFIRM_SAMPLES);
        if (track[0].locked) Serial.print(" LOCKED");
        Serial.print("  ");
        Serial.print(track[2].confirmCount); Serial.print("/"); Serial.print(CONFIRM_SAMPLES);
        if (track[2].locked) Serial.println(" LOCKED");
        else Serial.println();
        Serial.println();

        lastDebug = millis();
      }

      if (allLocked) {
        bool correct = isCorrect();
        detectState  = correct ? STATE_CORRECT : STATE_INCORRECT;
        timerStarted = false;

        static const char* PL[] = { "X", "S", "N" };

        Serial.print("\n=== ALL SENSORS LOCKED === Address: 0x");
        Serial.print(i2cAddress, HEX);
        Serial.print(" (");
        switch (i2cAddress) {
          case 0x08: Serial.print("Buoy");  break;
          case 0x09: Serial.print("Dam");   break;
          case 0x0A: Serial.print("Geo");   break;
          case 0x0B: Serial.print("Geo");   break;
          case 0x0C: Serial.print("Solar"); break;
          case 0x0D: Serial.print("Solar"); break;
          case 0x0E: Serial.print("Wind");  break;
          case 0x0F: Serial.print("Wind");  break;
          default:   Serial.print("???");   break;
        }
        Serial.println(")");
        Serial.println("         S2    S1    S3    (physical L→R)");
        Serial.print(  "GOT:     ");
        Serial.print(PL[track[1].confirmed]); Serial.print("     ");
        Serial.print(PL[track[0].confirmed]); Serial.print("     ");
        Serial.println(PL[track[2].confirmed]);
        Serial.print(  "RESULT:  ");
        Serial.println(correct ? ">>> CORRECT <<<" : ">>> INCORRECT <<<");
        
        setLEDs(correct ? CRGB(0, 100, 0) : CRGB(100, 0, 0));  // dim green / dim red
        writeTxBuf(detectState,
                   track[0].confirmed,
                   track[1].confirmed,
                   track[2].confirmed);
      }
      break;
    }

    // ── CORRECT / INCORRECT: Waiting for magnet removal ──────────────────────
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

