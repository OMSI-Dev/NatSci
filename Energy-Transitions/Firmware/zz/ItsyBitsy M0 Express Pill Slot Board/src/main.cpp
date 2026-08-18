/*
 * HALL EFFECT SENSOR POLARITY DETECTION - ItsyBitsy M0 Express
 * ═══════════════════════════════════════════════════════════════════════════════
 * REWRITTEN FROM SCRATCH - 2026-08-05
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * PURPOSE:
 *   Reads three SS39ET Hall effect sensors to detect magnetic game piece patterns.
 *   Simplified architecture with robust lock-integrity checking.
 *
 * CORE FIX:
 *   When locked, ANY sustained change to ANY sensor (not just to UNCERTAIN) triggers
 *   a full reset to IDLE. This prevents stale/stuck locked states when pieces are
 *   nudged or partially changed.
 *
 * DETECTION FLOW:
 *   IDLE → DEBOUNCING → REGISTERING → LOCKED (CORRECT/INCORRECT) → IDLE
 *
 * SENSOR CONFIGURATION:
 *   Physical PCB layout (left to right): S2 — S1 — S3
 *   Code mapping: p0=S1 (middle), p1=S2 (left), p2=S3 (right)
 *
 * ⚠️ CALIBRATION REQUIRED ⚠️
 * The following constants are STARTING VALUES and must be re-measured/tuned on
 * real hardware once sensors are operational:
 *   - ADC thresholds (THRESHOLD_SOUTH_LOW/HIGH, THRESHOLD_NORTH_LOW/HIGH)
 *   - Hysteresis band
 *   - Debounce/confirm timings
 *   - Piece pattern polarity definitions
 *   - Address→accepted-piece mappings
 *
 * I2C INTERFACE (preserved from original):
 *   TX packet (8 bytes on master request):
 *     [0] DetectState: 0=IDLE, 1=DEBOUNCING, 2=REGISTERING, 3=CORRECT, 4=INCORRECT
 *     [1] S1 polarity: 0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *     [2] S2 polarity: 0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *     [3] S3 polarity: 0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *     [4] Address:     Low byte of I2C address
 *     [5] GameState:   1=READY_IDLE, 2=ACTIVE, 3=PRE_RESULTS, 4=RESULTS
 *     [6] IsRegistered: 1 if locked, 0 otherwise
 *     [7] IsCorrect:   1 if correct placement (valid only if registered)
 *   RX: Single byte (new GameState from Teensy)
 */

#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>
#include <i2C_Address.h>

// ══════════════════════════════════════════════════════════════════════════════
// HARDWARE CONFIGURATION
// ══════════════════════════════════════════════════════════════════════════════

// ── Sensor Pins ──────────────────────────────────────────────────────────────
#define SENSOR_1_PIN A0  // S1 (middle)
#define SENSOR_2_PIN A1  // S2 (left)
#define SENSOR_3_PIN A2  // S3 (right)

// ── Diagnostic LED Pins ──────────────────────────────────────────────────────
#define SEN1_LED_PIN 11  // S1 (middle)
#define SEN2_LED_PIN 10  // S2 (left)
#define SEN3_LED_PIN 9   // S3 (right)

// ── DotStar Pins (ItsyBitsy M0 on-board LED, must be disabled) ───────────────
#define DOTSTAR_DATA 41
#define DOTSTAR_CLK 40

// ── WS2812 LED Ring ──────────────────────────────────────────────────────────
#define LED_PIN 2
#define NUM_LEDS 20
CRGB leds[NUM_LEDS];


// ── ADC Configuration ────────────────────────────────────────────────────────
#define ADC_SAMPLES 8  // Number of readings to average per sensor (increased for noisy power)
#define ADC_SETTLE_DELAY_US 200  // Delay between ADC samples for stability

// ── ADC Thresholds (12-bit, 3.3V ref) ───────────────────────────────────────
// Widened ranges to accommodate board-to-board variation and power supply differences
// Hysteresis prevents oscillation at boundaries
#define THRESHOLD_SOUTH_LOW 1550   // Below this = definitely SOUTH (was 1650)
#define THRESHOLD_SOUTH_HIGH 1850  // Above this = leaving SOUTH (was 1750)
#define THRESHOLD_NORTH_LOW 2250   // Below this = leaving NORTH (was 2350)
#define THRESHOLD_NORTH_HIGH 2550  // Above this = definitely NORTH (was 2450)
// UNCERTAIN range is now 1850-2250 (400 ADC counts wide vs. 600 before)
// This gives ±100 ADC count margin for power/board variation

// ── Debounce / Registration Timings ──────────────────────────────────────────
#define DEBOUNCE_DELAY_MS 120         // Initial debounce before starting registration
#define CONFIRM_SAMPLES 6             // Consecutive stable samples to lock a sensor (reduced for faster lock)
#define CANDIDATE_STABILITY 3         // Consecutive reads to establish a candidate
#define FORCE_LOCK_TIMEOUT_MS 800     // Max time in REGISTERING before forcing lock (reduced from 1200ms)
#define NORTH_PATTERN_EARLY_LOCK_MS 50 // Early force-lock for N N X, N N N, N X X patterns (VERY aggressive - almost instant)
#define MIN_REGISTERING_DISPLAY_MS 50 // Minimum time to show registration feedback (minimal delay for instant response)

// ── Lock Integrity Check (Section 6 of spec) ─────────────────────────────────
#define LOCK_MISMATCH_DEBOUNCE_MS 10  // Time a mismatch must persist to trigger reset (reduced for faster unlock)
                                       // (filters ADC noise, prevents false unlocks)
#define LOCK_FAILSAFE_TIMEOUT_MS 5000 // Max time in LOCKED before forcing reset (5s failsafe)
#define LOCK_NOCHANGE_TIMEOUT_MS 3000 // Force uSnlock if ADC values haven't changed for 3s
                                       // (catches power supply drift stuck states)

// ── I2C Contact / Fault Detection ───────────────────────────────────────────
#define I2C_CONTACT_TIMEOUT_MS 3000

// ── Diagnostic LED Blink Timing ──────────────────────────────────────────────
#define SENSOR_LED_SLOW_BLINK_MS 500   // SOUTH indicator
#define SENSOR_LED_FAST_BLINK_MS 150   // NORTH indicator
#define SENSOR_LED_FAULT_BLINK_MS 250  // I2C fault indicator

// ══════════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS
// ══════════════════════════════════════════════════════════════════════════════

enum Polarity : uint8_t
{
  POL_UNCERTAIN = 0,
  POL_SOUTH = 1,
  POL_NORTH = 2
};

enum DetectState : uint8_t
{
  STATE_IDLE = 0,
  STATE_DEBOUNCING = 1,
  STATE_REGISTERING = 2,
  STATE_CORRECT = 3,
  STATE_INCORRECT = 4
};

enum GameState : uint8_t
{
  GAME_READY_IDLE = 1,
  GAME_ACTIVE = 2,
  GAME_PRE_RESULTS = 3,
  GAME_RESULTS = 4
};

// Simplified sensor tracking structure
struct SensorTrack
{
  Polarity confirmed;     // Locked-in polarity (valid when board is LOCKED)
  Polarity candidate;     // Current candidate polarity during registration
  Polarity lastReading;   // Previous classification (for hysteresis)
  Polarity prevCandidate; // Previous candidate (for stability tracking)
  uint8_t confirmCount;   // Consecutive matches for confirmation
  uint8_t candidateCount; // Consecutive reads for candidate stability
  bool locked;            // Whether this sensor is locked
};

// ══════════════════════════════════════════════════════════════════════════════
// GLOBAL STATE
// ══════════════════════════════════════════════════════════════════════════════

// ── Board & Detection State ──────────────────────────────────────────────────
uint16_t i2cAddress = 0x08;
DetectState detectState = STATE_IDLE;
GameState gameState = GAME_READY_IDLE;
bool isRegistered = false;
bool isCorrectPlacement = false;
SensorTrack track[3];

// ── Single State Timestamp (replaces scattered static timers) ────────────────
uint32_t stateEnteredAtMs = 0;

// ── Lock Integrity Tracking ──────────────────────────────────────────────────
uint32_t lockMismatchStartMs = 0;  // When mismatch was first detected (0 = none active)
uint32_t lastRawChangeMs = 0;       // Last time any raw ADC value changed (for stuck detection)
uint16_t prevRaw[3] = {0, 0, 0};    // Previous raw readings for change detection

// ── I2C Communication ────────────────────────────────────────────────────────
volatile uint8_t txBuf[8] = {0, 0, 0, 0, 0x08, 0, 0, 0};
volatile bool teensyContactFlag = false;
bool hasSeenTeensyContact = false;
uint32_t lastTeensyContactMs = 0;

// ══════════════════════════════════════════════════════════════════════════════
// CORE HELPER FUNCTIONS
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Read and average multiple ADC samples from a sensor pin.
 * Reduces noise and improves reading stability.
 */
uint16_t readSensorAveraged(uint8_t pin)
{
  uint32_t sum = 0;
  // Discard first reading (may be stale from ADC mux switching)
  analogRead(pin);
  delayMicroseconds(ADC_SETTLE_DELAY_US);
  
  for (uint8_t i = 0; i < ADC_SAMPLES; i++)
  {
    sum += analogRead(pin);
    delayMicroseconds(ADC_SETTLE_DELAY_US);
  }
  return (uint16_t)(sum / ADC_SAMPLES);
}

/**
 * Classify sensor reading with hysteresis to prevent boundary oscillation.
 * Uses lastReading to apply appropriate thresholds based on previous state.
 */
Polarity classifyWithHysteresis(uint16_t raw, Polarity lastReading)
{
  if (lastReading == POL_SOUTH)
  {
    // Currently SOUTH: need to exceed high threshold to leave
    if (raw < THRESHOLD_SOUTH_HIGH)
      return POL_SOUTH;
    if (raw > THRESHOLD_NORTH_LOW)
      return POL_NORTH;
    return POL_UNCERTAIN;
  }
  else if (lastReading == POL_NORTH)
  {
    // Currently NORTH: need to drop below low threshold to leave
    if (raw > THRESHOLD_NORTH_LOW)
      return POL_NORTH;
    if (raw < THRESHOLD_SOUTH_HIGH)
      return POL_SOUTH;
    return POL_UNCERTAIN;
  }
  else
  {
    // UNCERTAIN: use stricter thresholds to enter S/N
    if (raw < THRESHOLD_SOUTH_LOW)
      return POL_SOUTH;
    if (raw > THRESHOLD_NORTH_HIGH)
      return POL_NORTH;
    return POL_UNCERTAIN;
  }
}

/**
 * Reset all sensor tracking state to initial values.
 * Single unified reset function used by all exit paths to IDLE.
 */
void resetAllTracks()
{
  for (uint8_t i = 0; i < 3; i++)
  {
    track[i].confirmed = POL_UNCERTAIN;
    track[i].candidate = POL_UNCERTAIN;
    track[i].lastReading = POL_UNCERTAIN;
    track[i].prevCandidate = POL_UNCERTAIN;
    track[i].confirmCount = 0;
    track[i].candidateCount = 0;
    track[i].locked = false;
  }
  lockMismatchStartMs = 0;
  lastRawChangeMs = millis();
  prevRaw[0] = prevRaw[1] = prevRaw[2] = 0;
}

/**
 * Update registration tracking for all sensors.
 * Called during STATE_REGISTERING to progressively lock each sensor's polarity.
 * 
 * @param cur Current polarity readings from all 3 sensors
 * @return true if all 3 sensors are locked, false otherwise
 */
bool updateRegistration(Polarity cur[3])
{
  bool allLocked = true;
  uint32_t registerDuration = millis() - stateEnteredAtMs;

  for (uint8_t i = 0; i < 3; i++)
  {
    if (track[i].locked)
      continue;

    // Track stability of current reading
    if (cur[i] == track[i].prevCandidate)
    {
      track[i].candidateCount++;
    }
    else
    {
      track[i].candidateCount = 1;
      track[i].prevCandidate = cur[i];
    }

    // After CANDIDATE_STABILITY consecutive identical reads, establish as candidate
    if (track[i].candidateCount >= CANDIDATE_STABILITY)
    {
      if (track[i].candidate != cur[i])
      {
        // New candidate established - reset confirmation
        track[i].candidate = cur[i];
        track[i].confirmCount = 0;
      }
    }

    // Check if current reading matches the established candidate
    if (cur[i] == track[i].candidate && track[i].candidateCount >= CANDIDATE_STABILITY)
    {
      track[i].confirmCount++;

      if (track[i].confirmCount >= CONFIRM_SAMPLES)
      {
        // Lock SOUTH/NORTH immediately, UNCERTAIN waits for force-lock timeout
        if (track[i].candidate == POL_SOUTH || track[i].candidate == POL_NORTH)
        {
          track[i].confirmed = track[i].candidate;
          track[i].locked = true;
        }
        else
        {
          allLocked = false;
        }
      }
      else
      {
        allLocked = false;
      }
    }
    else if (cur[i] == POL_UNCERTAIN &&
             track[i].candidate != POL_UNCERTAIN &&
             track[i].confirmCount >= 5)
    {
      // Strong S/N candidate but momentary UNCERTAIN - slowly decrement instead of reset
      if (track[i].confirmCount > 0)
        track[i].confirmCount--;
      allLocked = false;
    }
    else
    {
      // Reading doesn't match candidate
      if (track[i].confirmCount > 0)
        track[i].confirmCount--;
      allLocked = false;
    }
  }

  // CRITICAL FIX: Early force-lock for problematic NORTH patterns (N N X, N N N, N X X)
  // If ANY NORTH is detected (locked, candidate, or current reading) and we've been registering,
  // force-lock any oscillating UNCERTAIN sensors immediately
  bool hasNorth = false;
  for (uint8_t i = 0; i < 3; i++)
  {
    if ((track[i].locked && track[i].confirmed == POL_NORTH) ||
        track[i].candidate == POL_NORTH ||
        cur[i] == POL_NORTH)
    {
      hasNorth = true;
      break;
    }
  }
  
  if (hasNorth && registerDuration > NORTH_PATTERN_EARLY_LOCK_MS)
  {
    for (uint8_t i = 0; i < 3; i++)
    {
      if (!track[i].locked)
      {
        // Force-lock oscillating UNCERTAIN sensors when NORTH is present
        if (track[i].candidate == POL_UNCERTAIN || cur[i] == POL_UNCERTAIN)
        {
          Serial.print("EARLY FORCE-LOCK sensor ");
          Serial.print(i + 1);
          Serial.println(" as UNCERTAIN (NORTH pattern detected)");
          track[i].confirmed = POL_UNCERTAIN;
          track[i].candidate = POL_UNCERTAIN;
          track[i].locked = true;
        }
        // Also force-lock if it has a NORTH candidate (ANY confirmCount - no waiting)
        else if (track[i].candidate == POL_NORTH && track[i].confirmCount >= 1)
        {
          Serial.print("EARLY FORCE-LOCK sensor ");
          Serial.print(i + 1);
          Serial.println(" as NORTH (stable NORTH pattern)");
          track[i].confirmed = POL_NORTH;
          track[i].locked = true;
        }
      }
    }
  }
  
  // AGGRESSIVE FALLBACK: If some sensors locked but others stuck, force-lock the rest
  // This catches any pattern where stable sensors lock quickly but oscillating ones don't
  int lockedCount = 0;
  for (uint8_t i = 0; i < 3; i++)
  {
    if (track[i].locked)
      lockedCount++;
  }
  
  if (lockedCount >= 1 && registerDuration > 200)
  {
    for (uint8_t i = 0; i < 3; i++)
    {
      if (!track[i].locked)
      {
        // Force-lock based on current candidate or reading
        Polarity lockValue = (track[i].candidate != POL_UNCERTAIN) ? track[i].candidate : cur[i];
        Serial.print("AGGRESSIVE FORCE-LOCK sensor ");
        Serial.print(i + 1);
        Serial.print(" as ");
        Serial.println(lockValue == POL_NORTH ? "NORTH" : lockValue == POL_SOUTH ? "SOUTH" : "UNCERTAIN");
        track[i].confirmed = lockValue;
        track[i].candidate = lockValue;
        track[i].locked = true;
      }
    }
  }

  // Force-lock timeout: lock stable UNCERTAIN sensors after timeout
  if (registerDuration > FORCE_LOCK_TIMEOUT_MS)
  {
    for (uint8_t i = 0; i < 3; i++)
    {
      if (!track[i].locked &&
          track[i].candidate == POL_UNCERTAIN &&
          track[i].confirmCount >= 5)
      {
        Serial.print("FORCE-LOCKING sensor ");
        Serial.print(i + 1);
        Serial.println(" as UNCERTAIN (stable timeout)");
        track[i].confirmed = POL_UNCERTAIN;
        track[i].locked = true;
      }
    }
  }

  return allLocked;
}

/**
 * CRITICAL LOCK INTEGRITY CHECK (Section 6 of spec)
 * ═══════════════════════════════════════════════════════════════════════════════
 * Called only while in LOCKED state (CORRECT or INCORRECT).
 * 
 * Monitors all 3 locked sensors and triggers a full reset to IDLE if ANY sensor's
 * current reading differs from its locked value for longer than the debounce period.
 * 
 * This fixes the core bug: previously only UNCERTAIN unlocked sensors individually;
 * now ANY sustained change (SOUTH→NORTH, NORTH→SOUTH, or →UNCERTAIN) triggers a
 * full board reset.
 * 
 * ENHANCED: Also checks raw ADC values to detect piece removal even when hysteresis
 * keeps polarity classification stuck (e.g., NORTH → UNCERTAIN transition).
 * 
 * @param cur Current polarity readings from all 3 sensors
 * @param raw Current raw ADC values from all 3 sensors
 * @return true if a reset was triggered, false if lock remains valid
 */
bool checkLockIntegrity(Polarity cur[3], uint16_t raw[3])
{
  bool mismatchDetected = false;

  // Check all 3 sensors for any deviation from locked values
  for (uint8_t i = 0; i < 3; i++)
  {
    // Check polarity classification change
    if (cur[i] != track[i].confirmed)
    {
      mismatchDetected = true;
      break;
    }
    
    // CRITICAL: Also check for large raw ADC changes (bypasses hysteresis)
    // This catches piece removal even when hysteresis hasn't transitioned yet
    // Example: NORTH piece removed, ADC drops from 2600→2100 but hysteresis keeps it NORTH
    if (abs((int16_t)raw[i] - (int16_t)prevRaw[i]) > 200)
    {
      mismatchDetected = true;
      break;
    }
  }

  if (mismatchDetected)
  {
    // Start mismatch timer if not already running
    if (lockMismatchStartMs == 0)
    {
      lockMismatchStartMs = millis();
    }

    // Check if mismatch has persisted long enough
    if (millis() - lockMismatchStartMs >= LOCK_MISMATCH_DEBOUNCE_MS)
    {
      // Sustained mismatch - trigger full reset
      Serial.println("\n>>> LOCK INTEGRITY VIOLATED - SENSOR CHANGE DETECTED <<<");
      Serial.println(">>> RESETTING TO IDLE <<<\n");
      resetAllTracks();
      detectState = STATE_IDLE;
      stateEnteredAtMs = millis();
      isRegistered = false;
      isCorrectPlacement = false;
      return true;
    }
  }
  else
  {
    // All sensors match locked values - cancel any pending mismatch
    lockMismatchStartMs = 0;
  }

  return false;
}

/**
 * ⚠️ FLAGGED FOR RECALIBRATION ⚠️
 * Check if detected polarity pattern matches expected patterns for this board.
 * 
 * Pattern definitions (S1/S2/S3 = middle/left/right):
 *   Buoy  = S,S,S
 *   Dam   = N,N,N
 *   Geo   = S + (N,X) or (X,N)
 *   Solar = X + (N,X) or (X,N)
 *   Wind  = N + (N,X) or (X,N)
 * 
 * Address mapping:
 *   0x08, 0x0C        = Buoy  (accepts Buoy + Wind)
 *   0x09, 0x0D, 0x10  = Dam   (accepts Dam + Wind + Solar)
 *   0x0A, 0x0E, 0x0F, 0x11 = Geo   (accepts Geo + Wind + Solar)
 *   0x0B, 0x0F        = Solar (accepts Solar + Wind)
 * 
 * @return true if pattern is correct for this board's I2C address
 */
bool isCorrect()
{
  Polarity p0 = track[0].confirmed; // S1 (middle)
  Polarity p1 = track[1].confirmed; // S2 (left)
  Polarity p2 = track[2].confirmed; // S3 (right)

  // Define patterns for each piece type
  bool isBuoy = (p0 == POL_SOUTH && p1 == POL_SOUTH && p2 == POL_SOUTH);
  bool isDam = (p0 == POL_NORTH && p1 == POL_NORTH && p2 == POL_NORTH);
  bool isGeo = (p0 == POL_SOUTH) &&
               ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) ||
                (p1 == POL_UNCERTAIN && p2 == POL_NORTH));
  bool isSolar = (p0 == POL_UNCERTAIN) &&
                 ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) ||
                  (p1 == POL_UNCERTAIN && p2 == POL_NORTH));
  bool isWind = (p0 == POL_NORTH) &&
                ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) ||
                 (p1 == POL_UNCERTAIN && p2 == POL_NORTH));

  switch (i2cAddress)
  {
  case 0x08:
  case 0x0C:
    return (isBuoy || isWind);

  case 0x09:
  case 0x0D:
  case 0x10:
    return (isDam || isWind || isSolar);

  case 0x0A:
  case 0x0E:
  case 0x0F:
  case 0x11:
    return (isGeo || isWind || isSolar);

  case 0x0B:
    return (isSolar || isWind);

  default:
    return false;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// LED FEEDBACK FUNCTIONS
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Set all ring LEDs to a solid color.
 */
void setLEDs(CRGB color)
{
  fill_solid(leds, NUM_LEDS, color);
  FastLED.show();
}

/**
 * White trail chase animation for registration feedback.
 */
void setLEDsWhiteTrailChase()
{
  static uint16_t head = 0;
  static uint32_t lastStepMs = 0;
  const uint32_t stepMs = 40;

  if (millis() - lastStepMs >= stepMs)
  {
    head = (head + 1) % NUM_LEDS;
    lastStepMs = millis();
  }

  fadeToBlackBy(leds, NUM_LEDS, 48);
  leds[head] = CRGB(220, 220, 220);
  leds[(head + NUM_LEDS - 1) % NUM_LEDS] = CRGB(120, 120, 120);
  leds[(head + NUM_LEDS - 2) % NUM_LEDS] = CRGB(60, 60, 60);
  FastLED.show();
}

/**
 * Breathing effect (sine wave).
 */
void setLEDsBreathing(CRGB baseColor, uint8_t minBrightness, uint8_t maxBrightness, uint16_t periodMs)
{
  uint32_t now = millis();
  float phase = (float)(now % periodMs) / periodMs * 2.0 * PI;
  float sineWave = (sin(phase) + 1.0) / 2.0;
  uint8_t brightness = minBrightness + (uint8_t)(sineWave * (maxBrightness - minBrightness));

  CRGB color = baseColor;
  color.nscale8(brightness);
  fill_solid(leds, NUM_LEDS, color);
  FastLED.show();
}

/**
 * Update ring LEDs based on detection state and game state.
 * Single function called once per loop - no LED logic scattered through state machine.
 * 
 * LED behavior:
 *  - IDLE: breathing white animation
 *  - REGISTERING: white tail chase animation
 *  - LOCKED (CORRECT/INCORRECT): continue tail chase (until RESULTS state)
 *  - GAME_RESULTS + CORRECT: solid green
 *  - GAME_RESULTS + INCORRECT: solid red
 */
void updateRingLeds(GameState gs, DetectState ds, bool registered, bool correct, bool i2cFault)
{
  // During I2C fault, show breathing animation
  if (i2cFault)
  {
    setLEDsBreathing(CRGB::White, 20, 150, 2000);
    return;
  }

  // RESULTS state shows final colors
  if (gs == GAME_RESULTS)
  {
    if (!registered)
    {
      setLEDsBreathing(CRGB::White, 20, 150, 2000); // Empty slot
    }
    else if (correct)
    {
      setLEDs(CRGB(0, 200, 0)); // Green for correct
    }
    else
    {
      setLEDs(CRGB(200, 0, 0)); // Red for incorrect
    }
    return;
  }

  // LED behavior driven by detection state (for all non-RESULTS game states)
  switch (ds)
  {
  case STATE_IDLE:
  case STATE_DEBOUNCING:
    // Not registered - breathing animation
    setLEDsBreathing(CRGB::White, 20, 150, 2000);
    break;

  case STATE_REGISTERING:
  case STATE_CORRECT:
  case STATE_INCORRECT:
    // Registration or locked - tail chase continues
    setLEDsWhiteTrailChase();
    break;

  default:
    setLEDsBreathing(CRGB::White, 20, 150, 2000);
    break;
  }
}

/**
 * Update diagnostic LEDs (pins 9/10/11) based on sensor state and lock status.
 * During registration: Off = uncertain, slow blink = SOUTH, fast blink = NORTH
 * When locked: Solid on (green indicator that backend is locked)
 * I2C fault: all-fast-blink
 */
void updateDiagnosticLeds(Polarity cur[3], bool i2cFault, bool isLocked)
{
  if (i2cFault)
  {
    // I2C fault: all LEDs fast blink in sync
    bool ledOn = ((millis() / SENSOR_LED_FAULT_BLINK_MS) % 2) == 0;
    digitalWrite(SEN1_LED_PIN, ledOn ? HIGH : LOW);
    digitalWrite(SEN2_LED_PIN, ledOn ? HIGH : LOW);
    digitalWrite(SEN3_LED_PIN, ledOn ? HIGH : LOW);
  }
  else if (isLocked)
  {
    // Locked: all diagnostic LEDs solid on (backend lock indicator)
    digitalWrite(SEN1_LED_PIN, HIGH);
    digitalWrite(SEN2_LED_PIN, HIGH);
    digitalWrite(SEN3_LED_PIN, HIGH);
  }
  else
  {
    // Normal operation: indicate polarity per sensor
    const uint8_t LED_PINS[3] = {SEN1_LED_PIN, SEN2_LED_PIN, SEN3_LED_PIN};
    for (uint8_t i = 0; i < 3; i++)
    {
      if (cur[i] == POL_UNCERTAIN)
      {
        digitalWrite(LED_PINS[i], LOW);
      }
      else if (cur[i] == POL_SOUTH)
      {
        bool ledOn = ((millis() / SENSOR_LED_SLOW_BLINK_MS) % 2) == 0;
        digitalWrite(LED_PINS[i], ledOn ? HIGH : LOW);
      }
      else // POL_NORTH
      {
        bool ledOn = ((millis() / SENSOR_LED_FAST_BLINK_MS) % 2) == 0;
        digitalWrite(LED_PINS[i], ledOn ? HIGH : LOW);
      }
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// I2C COMMUNICATION (preserved from original - known working)
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Update I2C transmit buffer with current state and sensor polarities.
 * Thread-safe with interrupt protection.
 * 
 * Packet format (8 bytes):
 *   [0] DetectState:  0=IDLE, 1=DEBOUNCING, 2=REGISTERING, 3=CORRECT, 4=INCORRECT
 *   [1] S1 polarity:  0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *   [2] S2 polarity:  0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *   [3] S3 polarity:  0=UNCERTAIN, 1=SOUTH, 2=NORTH
 *   [4] Address:      Low byte of I2C address
 *   [5] GameState:    Current game state
 *   [6] IsRegistered: 1 if piece locked, 0 otherwise
 *   [7] IsCorrect:    1 if correct placement, 0 otherwise (valid only if registered)
 */
void writeTxBuf(DetectState st, Polarity p0, Polarity p1, Polarity p2)
{
  noInterrupts();
  txBuf[0] = (uint8_t)st;
  txBuf[1] = (uint8_t)p0;
  txBuf[2] = (uint8_t)p1;
  txBuf[3] = (uint8_t)p2;
  txBuf[4] = (uint8_t)(i2cAddress & 0xFF);
  txBuf[5] = (uint8_t)gameState;
  txBuf[6] = isRegistered ? 1 : 0;
  txBuf[7] = isCorrectPlacement ? 1 : 0;
  interrupts();
}

/**
 * I2C request handler - sends current state to master (Teensy).
 */
void onRequest()
{
  teensyContactFlag = true;
  Wire.write((uint8_t *)txBuf, 8);
}

/**
 * I2C receive handler - receives game state commands from Teensy.
 * Packet format: [gameState]
 */
void onReceive(int numBytes)
{
  if (numBytes >= 1)
  {
    teensyContactFlag = true;
    uint8_t receivedState = Wire.read();

    // Clear remaining bytes
    while (Wire.available())
    {
      Wire.read();
    }

    // Validate and update game state
    if (receivedState >= (uint8_t)GAME_READY_IDLE && 
        receivedState <= (uint8_t)GAME_RESULTS)
    {
      GameState newGameState = (GameState)receivedState;
      
      if (newGameState != gameState)
      {
        gameState = newGameState;
        
        Serial.print(">>> GAME STATE CHANGED: ");
        switch (gameState)
        {
        case GAME_READY_IDLE:
          Serial.println("READY IDLE");
          break;
        case GAME_ACTIVE:
          Serial.println("ACTIVE GAME");
          break;
        case GAME_PRE_RESULTS:
          Serial.println("PRE-RESULTS");
          break;
        case GAME_RESULTS:
          Serial.println("RESULTS");
          break;
        }
      }
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// STARTUP HELPERS
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Turn off on-board DotStar LED using APA102 protocol.
 * Called during setup to prevent interference with external LED ring.
 */
void turnOffDotStar()
{
  pinMode(DOTSTAR_DATA, OUTPUT);
  pinMode(DOTSTAR_CLK, OUTPUT);

  // Start frame (32 bits of 0)
  for (uint8_t i = 0; i < 32; i++)
  {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, LOW);
    digitalWrite(DOTSTAR_CLK, HIGH);
  }

  // LED frame: brightness=0, R=0, G=0, B=0
  for (uint8_t bit = 0; bit < 8; bit++)
  {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, (bit < 3) ? HIGH : LOW); // 111 prefix
    digitalWrite(DOTSTAR_CLK, HIGH);
  }

  // RGB bytes (all zeros)
  for (uint8_t i = 0; i < 24; i++)
  {
    digitalWrite(DOTSTAR_CLK, LOW);
    digitalWrite(DOTSTAR_DATA, LOW);
    digitalWrite(DOTSTAR_CLK, HIGH);
  }

  // End frame
  for (uint8_t i = 0; i < 32; i++)
  {
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

// ══════════════════════════════════════════════════════════════════════════════
// SETUP
// ══════════════════════════════════════════════════════════════════════════════

void setup()
{
  // Initialize serial communication
  Serial.begin(115200);
  uint32_t serialWaitStart = millis();
  while (!Serial && (millis() - serialWaitStart) < 1500)
  {
  }

  // Disable on-board LEDs
  turnOffDotStar();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // Configure diagnostic LED pins
  pinMode(SEN1_LED_PIN, OUTPUT);
  pinMode(SEN2_LED_PIN, OUTPUT);
  pinMode(SEN3_LED_PIN, OUTPUT);
  digitalWrite(SEN1_LED_PIN, LOW);
  digitalWrite(SEN2_LED_PIN, LOW);
  digitalWrite(SEN3_LED_PIN, LOW);

  // Configure ADC for 12-bit resolution
  analogReadResolution(12);
  
  // Allow power supply to stabilize (critical for external power)
  Serial.println("Waiting for power stabilization...");
  delay(500);

  // Initialize external LED ring
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 500);
  setLEDs(CRGB::Black);

  // Initialize sensor tracking and state
  resetAllTracks();
  detectState = STATE_IDLE;
  gameState = GAME_READY_IDLE;
  isRegistered = false;
  isCorrectPlacement = false;
  stateEnteredAtMs = millis();
  lastTeensyContactMs = millis();

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
  printI2Caddress();
  Serial.print("Configuration: ");
  Serial.print(ADC_SAMPLES);
  Serial.print(" ADC samples ("  );
  Serial.print(ADC_SETTLE_DELAY_US);
  Serial.print("us settle), ");
  Serial.print(CONFIRM_SAMPLES);
  Serial.print(" confirm samples, ");
  Serial.print(DEBOUNCE_DELAY_MS);
  Serial.println("ms debounce");
  Serial.println("⚠️  THRESHOLDS & PATTERNS FLAGGED FOR RECALIBRATION ⚠️");
  Serial.println("============================================\n");

  // Initialize I2C TX buffer and start I2C peripheral
  writeTxBuf(STATE_IDLE, POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN);
  Wire.begin(i2cAddress);
  Wire.onRequest(onRequest);
  Wire.onReceive(onReceive);

  // Display baseline ADC readings (for threshold calibration)
  delay(250); // Let ADC fully stabilize after power-up
  Serial.println("\n=== BASELINE ADC READINGS (NO MAGNET) ===");
  Serial.println("         S2      S1      S3    (physical L→R)");
  uint16_t baseline_s2 = readSensorAveraged(SENSOR_2_PIN);
  uint16_t baseline_s1 = readSensorAveraged(SENSOR_1_PIN);
  uint16_t baseline_s3 = readSensorAveraged(SENSOR_3_PIN);
  Serial.print("RAW:   ");
  Serial.print(baseline_s2);
  Serial.print("\t");
  Serial.print(baseline_s1);
  Serial.print("\t");
  Serial.println(baseline_s3);
  Serial.println("Expected: All values between 1850-2250 for UNCERTAIN");
  Serial.print("  SOUTH range: < ");
  Serial.println(THRESHOLD_SOUTH_HIGH);
  Serial.print("  NORTH range: > ");
  Serial.println(THRESHOLD_NORTH_LOW);
  
  // Warn if any sensor is outside expected UNCERTAIN range
  bool baseline_ok = true;
  if (baseline_s1 < THRESHOLD_SOUTH_HIGH || baseline_s1 > THRESHOLD_NORTH_LOW)
  {
    Serial.println("⚠️  WARNING: S1 baseline outside UNCERTAIN range!");
    baseline_ok = false;
  }
  if (baseline_s2 < THRESHOLD_SOUTH_HIGH || baseline_s2 > THRESHOLD_NORTH_LOW)
  {
    Serial.println("⚠️  WARNING: S2 baseline outside UNCERTAIN range!");
    baseline_ok = false;
  }
  if (baseline_s3 < THRESHOLD_SOUTH_HIGH || baseline_s3 > THRESHOLD_NORTH_LOW)
  {
    Serial.println("⚠️  WARNING: S3 baseline outside UNCERTAIN range!");
    baseline_ok = false;
  }
  
  if (!baseline_ok)
  {
    Serial.println("⚠️  CHECK POWER SUPPLY VOLTAGE (should be 3.3V)");
  }
  Serial.println("==========================================\n");

  Serial.println("System ready.\n");
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN LOOP
// ══════════════════════════════════════════════════════════════════════════════

void loop()
{
  static const uint8_t PINS[3] = {SENSOR_1_PIN, SENSOR_2_PIN, SENSOR_3_PIN};
  static uint32_t lastDebugMs = 0;
  static uint32_t lastLockedDebugMs = 0;

  // ── I2C Contact Tracking ───────────────────────────────────────────────────
  if (teensyContactFlag)
  {
    noInterrupts();
    teensyContactFlag = false;
    interrupts();
    hasSeenTeensyContact = true;
    lastTeensyContactMs = millis();
  }

  // Detect I2C fault (suppress during PRE_RESULTS/RESULTS where I2C loss is expected)
  bool i2cFaultActive = hasSeenTeensyContact &&
                        (millis() - lastTeensyContactMs) > I2C_CONTACT_TIMEOUT_MS &&
                        (gameState != GAME_PRE_RESULTS && gameState != GAME_RESULTS);

  // ── Sensor Reading & Classification ────────────────────────────────────────
  Polarity cur[3];
  uint16_t raw[3];
  bool anyRawChanged = false;
  
  for (uint8_t i = 0; i < 3; i++)
  {
    raw[i] = readSensorAveraged(PINS[i]);
    cur[i] = classifyWithHysteresis(raw[i], track[i].lastReading);
    track[i].lastReading = cur[i];
    
    // Track if any raw value changed (for stuck detection)
    if (abs((int16_t)raw[i] - (int16_t)prevRaw[i]) > 15)  // 15 ADC count threshold (was 10)
    {
      anyRawChanged = true;
    }
  }
  
  // Update last-change timestamp if any sensor moved
  if (anyRawChanged)
  {
    lastRawChangeMs = millis();
    // NOTE: prevRaw update moved to AFTER state machine so lock integrity
    // can detect changes by comparing raw vs prevRaw
  }

  bool allUncertain = (cur[0] == POL_UNCERTAIN &&
                       cur[1] == POL_UNCERTAIN &&
                       cur[2] == POL_UNCERTAIN);

  // Update registration flag
  isRegistered = (detectState == STATE_CORRECT || detectState == STATE_INCORRECT);

  // ── State Machine ───────────────────────────────────────────────────────────
  switch (detectState)
  {
  case STATE_IDLE:
    // ── IDLE: Waiting for magnet detection ─────────────────────────────────
    if (!allUncertain)
    {
      resetAllTracks();
      detectState = STATE_DEBOUNCING;
      stateEnteredAtMs = millis();
      Serial.println("\n>>> MAGNETISM DETECTED - DEBOUNCING <<<");
    }
    break;

  case STATE_DEBOUNCING:
    // ── DEBOUNCING: Short delay to filter transient signals ────────────────
    if (allUncertain)
    {
      // Magnet removed during debounce - false trigger
      Serial.println(">>> FALSE TRIGGER - BACK TO IDLE <<<");
      resetAllTracks();
      detectState = STATE_IDLE;
      stateEnteredAtMs = millis();
      isRegistered = false;
      isCorrectPlacement = false;
    }
    else if (millis() - stateEnteredAtMs >= DEBOUNCE_DELAY_MS)
    {
      // Debounce complete - start registration
      Serial.println(">>> DEBOUNCE COMPLETE - STARTING REGISTRATION <<<");
      resetAllTracks();
      detectState = STATE_REGISTERING;
      stateEnteredAtMs = millis();
    }
    break;

  case STATE_REGISTERING:
    // ── REGISTERING: Confirming stable polarity pattern ────────────────────
    if (allUncertain)
    {
      // Object removed before confirmation - return to idle
      Serial.println(">>> OBJECT REMOVED BEFORE CONFIRMATION - BACK TO IDLE <<<");
      resetAllTracks();
      detectState = STATE_IDLE;
      stateEnteredAtMs = millis();
      isRegistered = false;
      isCorrectPlacement = false;
    }
    else
    {
      bool allLocked = updateRegistration(cur);
      uint32_t registerDuration = millis() - stateEnteredAtMs;

      // Lock when all sensors locked AND minimum display time elapsed
      // BUT: re-check if piece was removed during the wait
      if (allLocked && registerDuration >= MIN_REGISTERING_DISPLAY_MS)
      {
        // Double-check piece is still present before locking
        if (allUncertain)
        {
          Serial.println(">>> PIECE REMOVED DURING LOCK WAIT - BACK TO IDLE <<<");
          resetAllTracks();
          detectState = STATE_IDLE;
          stateEnteredAtMs = millis();
          isRegistered = false;
          isCorrectPlacement = false;
          break;
        }
        
        bool correct = isCorrect();
        detectState = correct ? STATE_CORRECT : STATE_INCORRECT;
        stateEnteredAtMs = millis();
        isCorrectPlacement = correct;

        static const char *PL[] = {"X", "S", "N"};
        Serial.print("\n=== ALL SENSORS LOCKED === Address: 0x");
        Serial.print(i2cAddress, HEX);
        Serial.print(" (");
        printI2Caddress();
        Serial.print(")");
        Serial.println("         S2    S1    S3    (physical L→R)");
        Serial.print("GOT:     ");
        Serial.print(PL[track[1].confirmed]);
        Serial.print("     ");
        Serial.print(PL[track[0].confirmed]);
        Serial.print("     ");
        Serial.println(PL[track[2].confirmed]);
        Serial.print("RESULT:  ");
        Serial.println(correct ? ">>> CORRECT <<<" : ">>> INCORRECT <<<");
      }

      // Debug output every 500ms during registration
      if (millis() - lastDebugMs > 500)
      {
        static const char *POL_LABEL[] = {"  X  ", "  S  ", "  N  "};
        Serial.println("         S2      S1      S3    (physical L→R)");
        Serial.print("RAW:   ");
        Serial.print(raw[1]);
        Serial.print("\t");
        Serial.print(raw[0]);
        Serial.print("\t");
        Serial.println(raw[2]);
        Serial.print("CUR:  ");
        Serial.print(POL_LABEL[cur[1]]);
        Serial.print("   ");
        Serial.print(POL_LABEL[cur[0]]);
        Serial.print("   ");
        Serial.println(POL_LABEL[cur[2]]);
        Serial.print("CAND: ");
        Serial.print(POL_LABEL[track[1].candidate]);
        Serial.print("   ");
        Serial.print(POL_LABEL[track[0].candidate]);
        Serial.print("   ");
        Serial.println(POL_LABEL[track[2].candidate]);
        Serial.print("PROG: ");
        Serial.print(track[1].confirmCount);
        Serial.print("/");
        Serial.print(CONFIRM_SAMPLES);
        if (track[1].locked)
          Serial.print(" LOCKED");
        Serial.print("  ");
        Serial.print(track[0].confirmCount);
        Serial.print("/");
        Serial.print(CONFIRM_SAMPLES);
        if (track[0].locked)
          Serial.print(" LOCKED");
        Serial.print("  ");
        Serial.print(track[2].confirmCount);
        Serial.print("/");
        Serial.print(CONFIRM_SAMPLES);
        if (track[2].locked)
          Serial.println(" LOCKED");
        else
          Serial.println();
        Serial.println();

        lastDebugMs = millis();
      }
    }
    break;

  case STATE_CORRECT:
  case STATE_INCORRECT:
    // ── LOCKED (CORRECT/INCORRECT): Monitor lock integrity ─────────────────
    
    // CRITICAL: Check lock integrity - triggers reset if any sensor changes
    if (checkLockIntegrity(cur, raw))
    {
      // Reset was triggered inside checkLockIntegrity
      break;
    }

    // Check for complete removal (all sensors UNCERTAIN)
    if (allUncertain)
    {
      Serial.println(">>> MAGNET REMOVED - BACK TO IDLE <<<\n");
      resetAllTracks();
      detectState = STATE_IDLE;
      stateEnteredAtMs = millis();
      isRegistered = false;
      isCorrectPlacement = false;
    }
    
    // FAILSAFE: Force unlock if locked too long (catches stuck sensors)
    if (millis() - stateEnteredAtMs > LOCK_FAILSAFE_TIMEOUT_MS)
    {
      Serial.println("\n>>> FAILSAFE TIMEOUT - FORCING UNLOCK <<<");
      Serial.println(">>> (Sensors may need recalibration) <<<\n");
      resetAllTracks();
      detectState = STATE_IDLE;
      stateEnteredAtMs = millis();
      isRegistered = false;
      isCorrectPlacement = false;
    }
    
    // STUCK DETECTION: Force unlock if ADC values haven't changed AND are outside baseline
    // This catches cases where power supply drift makes sensors stuck at non-baseline values
    // Don't trigger if readings are stable at valid magnet-present levels
    if (millis() - lastRawChangeMs > LOCK_NOCHANGE_TIMEOUT_MS)
    {
      // Check if readings are stuck OUTSIDE the expected UNCERTAIN baseline range
      // If all sensors are reading definitive NORTH/SOUTH in expected ranges, piece is still present
      bool stuckOutsideBaseline = false;
      
      // Check if any sensor is stuck in the "drift zone" (just beyond baseline)
      // Baseline is 1850-2250, drift zone is 2250-2400 or 1600-1850 (marginal readings)
      for (uint8_t i = 0; i < 3; i++)
      {
        if ((raw[i] > THRESHOLD_NORTH_LOW && raw[i] < THRESHOLD_NORTH_HIGH) ||
            (raw[i] < THRESHOLD_SOUTH_HIGH && raw[i] > THRESHOLD_SOUTH_LOW))
        {
          // Sensor is in the marginal zone - likely drift, not strong magnet
          stuckOutsideBaseline = true;
          break;
        }
      }
      
      if (stuckOutsideBaseline)
      {
        Serial.println("\n>>> NO SENSOR ACTIVITY + MARGINAL READINGS - FORCING UNLOCK <<<");
        Serial.println(">>> (Power supply voltage may have drifted) <<<\n");
        resetAllTracks();
        detectState = STATE_IDLE;
        stateEnteredAtMs = millis();
        isRegistered = false;
        isCorrectPlacement = false;
      }
    }
    
    // Debug output every 2s while locked to monitor sensor drift
    if (millis() - lastLockedDebugMs > 2000)
    {
      static const char *PL[] = {"X", "S", "N"};
      Serial.println("\n[LOCKED STATE DEBUG]");
      Serial.println("         S2      S1      S3    (physical L→R)");
      Serial.print("RAW:   ");
      Serial.print(raw[1]);
      Serial.print("\t");
      Serial.print(raw[0]);
      Serial.print("\t");
      Serial.println(raw[2]);
      Serial.print("CUR:    ");
      Serial.print(PL[cur[1]]);
      Serial.print("       ");
      Serial.print(PL[cur[0]]);
      Serial.print("       ");
      Serial.println(PL[cur[2]]);
      Serial.print("LOCKED: ");
      Serial.print(PL[track[1].confirmed]);
      Serial.print("       ");
      Serial.print(PL[track[0].confirmed]);
      Serial.print("       ");
      Serial.println(PL[track[2].confirmed]);
      Serial.print("Match:  ");
      Serial.print((cur[1] == track[1].confirmed) ? "YES" : "NO ");
      Serial.print("     ");
      Serial.print((cur[0] == track[0].confirmed) ? "YES" : "NO ");
      Serial.print("     ");
      Serial.println((cur[2] == track[2].confirmed) ? "YES" : "NO ");
      Serial.print("Locked for: ");
      Serial.print((millis() - stateEnteredAtMs) / 1000);
      Serial.println("s\n");
      
      lastLockedDebugMs = millis();
    }
    break;
  }

  // ── Update Previous Raw Values ──────────────────────────────────────────────
  // Done AFTER state machine so lock integrity can detect changes
  if (anyRawChanged)
  {
    for (uint8_t i = 0; i < 3; i++)
    {
      prevRaw[i] = raw[i];
    }
  }

  // ── Update I2C TX Buffer ────────────────────────────────────────────────────
  // Publish fresh status every loop so Teensy never reads stale state
  Polarity txS1 = cur[0];
  Polarity txS2 = cur[1];
  Polarity txS3 = cur[2];
  
  // If locked, send confirmed values instead of current readings
  if (detectState == STATE_CORRECT || detectState == STATE_INCORRECT)
  {
    txS1 = track[0].confirmed;
    txS2 = track[1].confirmed;
    txS3 = track[2].confirmed;
  }
  
  writeTxBuf(detectState, txS1, txS2, txS3);

  // ── Update LEDs ─────────────────────────────────────────────────────────────
  updateRingLeds(gameState, detectState, isRegistered, isCorrectPlacement, i2cFaultActive);
  updateDiagnosticLeds(cur, i2cFaultActive, isRegistered);

  delay(10);
}
