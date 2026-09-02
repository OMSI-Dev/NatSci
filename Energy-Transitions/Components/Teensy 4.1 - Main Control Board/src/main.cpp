/*
 * ENERGY TRANSITIONS EXHIBIT - TEENSY 4.1 MAIN CONTROLLER
 * 
 * Manages game state machine and coordinates with ItsyBitsy M0 sensor boards
 * via I2C. Provides audio feedback using WAV Trigger.
 * 
 * GAME STATE FLOW:
 *   READY_IDLE (white pulse, wait for piece registration) → 
 *   ACTIVE (piece registered, pull switch to check) → 
 *   PRE_RESULTS → RESULTS → READY_IDLE
 * 
 * I2C COMMUNICATION:
 *   - Teensy is I2C master
 *   - Sends game state commands to M0 boards
 *   - Receives 8-byte status packets from M0 boards
 * 
 * INPUTS:
 *   - Energy switch on pin 14 (ONLY during ACTIVE state, triggers PRE_RESULTS)
 *   - M0 piece registration (triggers READY_IDLE → ACTIVE transition)
 *   - Serial dev tools for manual state cycling
 * 
 * OUTPUTS:
 *   - I2C commands to M0 boards
 *   - Audio playback via WAV Trigger
 * 
 */

#include <Arduino.h>
#include <Wire.h>
// FastLED >= 3.9 defaults to the ObjectFLED DMA driver for WS2812 on Teensy 4.x,
// which conflicts with the I2C peripheral (pins 18/19). Force the classic driver.
#define FASTLED_NOT_USES_OBJECTFLED
#include <FastLED.h>
#include <Bounce2.h>
#include <Keyboard.h>

// ── Pin definitions ────────────────────────────────────────────────────────────
#define ENERGY_SWITCH_PIN 14
#define LANGUAGE_BUTTON_PIN 15
#define BUTTON_LED_PIN 1  // TX pin repurposed for button LED PWM
#define LANGUAGE_BUTTON_LED_PIN 22  // Language button LED PWM

// ── City LED definitions ───────────────────────────────────────────────────────
#define NUM_LEDS_PER_STRIP 35
#define NUM_CITIES 7
#define LED_BRIGHTNESS 128
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

// ── Game configuration ─────────────────────────────────────────────────────────
#define NUM_M0_BOARDS 10      // Number of M0 sensor boards expected
#define ENERGY_SWITCH_DEBOUNCE_MS 200  // Debounce time for energy switch
#define LANGUAGE_BUTTON_DEBOUNCE_MS 200  // Debounce time for language button
#define INACTIVITY_TIMEOUT_MS 120000  // 2 minutes of inactivity before auto-reset

// ── Game state enum ────────────────────────────────────────────────────────────
enum GameState : uint8_t {
  GAME_READY_IDLE  = 1,
  GAME_ACTIVE      = 2,
  GAME_PRE_RESULTS = 3,
  GAME_RESULTS     = 4
};

// ── M0 Board status structure ──────────────────────────────────────────────────
struct M0Status {
  uint8_t detectState;    // 0=IDLE, 1=DEBOUNCING, 2=REGISTERING, 3=CORRECT, 4=INCORRECT
  uint8_t s1Polarity;     // Sensor 1 polarity
  uint8_t s2Polarity;     // Sensor 2 polarity
  uint8_t s3Polarity;     // Sensor 3 polarity
  uint8_t address;        // I2C address
  uint8_t gameState;      // Game state (as known by M0)
  bool isRegistered;      // True if piece is registered
  bool isCorrect;         // True if placement is correct
  uint16_t rawSensor1;    // Raw sensor 1 ADC reading (16-bit for debugging)
  uint16_t rawSensor2;    // Raw sensor 2 ADC reading (16-bit for debugging)
  uint16_t rawSensor3;    // Raw sensor 3 ADC reading (16-bit for debugging)
  bool responseReceived;  // True if we received a response this cycle
};

// ── Global variables ───────────────────────────────────────────────────────────
GameState currentGameState = GAME_READY_IDLE;
M0Status m0Boards[NUM_M0_BOARDS];
volatile bool i2cTransactionInProgress = false;

// Debounced physical inputs
Bounce energySwitchDebouncer = Bounce();
Bounce languageButtonDebouncer = Bounce();

// uint8_t m0Addresses[NUM_M0_BOARDS] = {0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11};

uint8_t m0Addresses[NUM_M0_BOARDS] = {0x08, 0x0C, 0x09, 0x0B, 0x0A, 0x0D, 0x10, 0x0E, 0x0F, 0x11};

// City LED arrays
CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];
CRGB leds3[NUM_LEDS_PER_STRIP];
CRGB leds4[NUM_LEDS_PER_STRIP];
CRGB leds5[NUM_LEDS_PER_STRIP];
CRGB leds6[NUM_LEDS_PER_STRIP];
CRGB leds7[NUM_LEDS_PER_STRIP];

// Results display timer
uint32_t resultsDisplayStartTime = 0;
const uint32_t RESULTS_DISPLAY_DURATION_MS = 10000;  // Show results for 10 seconds

// State machine control
bool preResultsProcessed = false;

// Piece registration tracking for PIECE_REGISTERED sound
uint8_t previousRegisteredCount = 0;

// Inactivity timer for auto-reset
uint32_t lastActivityTime = 0;

void changeGameState(GameState newState);
void sendGameStateToM0s();
void pollM0Boards(bool verbose = false);
void processResults();
void handleSerialDevTools();
void scanI2CBus();
bool checkEnergySwitchPulled();
bool checkLanguageButtonPressed();
void printCurrentStateStatus();
const char* getGameStateName(GameState state);
void updateCityLEDs();
void setAllCitiesColor(CRGB color);
void setAllCitiesPulsating(CRGB baseColor, uint8_t minBright, uint8_t maxBright, uint16_t periodMs);
void setAllCitiesRainbow();
void setAllCitiesOff();
bool validatePiecePlacement(uint8_t address, uint8_t s1, uint8_t s2, uint8_t s3);
void updateButtonLED();
void updateLanguageButtonLED();

static void acquireI2CBus() {
  while (i2cTransactionInProgress) {
    delayMicroseconds(200);
  }
  i2cTransactionInProgress = true;
}

static void releaseI2CBus() {
  i2cTransactionInProgress = false;
}

static void resetI2CBus() {
  Wire.end();
  delay(20);
  Wire.begin();
  Wire.setClock(100000);
  delay(50);
  i2cTransactionInProgress = false;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize USB Keyboard
  Keyboard.begin();
  // Serial.println("✓ USB Keyboard initialized");

  // Initialize I2C as big friend
  Wire.begin();
  Wire.setClock(100000);  // 100kHz I2C clock
  delay(100);  // give M0 slaves a moment after init
  
  // Energy switch
  pinMode(ENERGY_SWITCH_PIN, INPUT_PULLUP);
  energySwitchDebouncer.attach(ENERGY_SWITCH_PIN, INPUT_PULLUP);
  energySwitchDebouncer.interval(ENERGY_SWITCH_DEBOUNCE_MS);
  energySwitchDebouncer.update();
  // Serial.println("✓ Energy switch initialized on pin 14");
  
  // Language button
  pinMode(LANGUAGE_BUTTON_PIN, INPUT_PULLUP);
  languageButtonDebouncer.attach(LANGUAGE_BUTTON_PIN, INPUT_PULLUP);
  languageButtonDebouncer.interval(LANGUAGE_BUTTON_DEBOUNCE_MS);
  languageButtonDebouncer.update();
  // Serial.println("✓ Language button initialized on pin 15");
  
  // Initialize Button LED PWM (repurposed TX pin)
  pinMode(BUTTON_LED_PIN, OUTPUT);
  analogWriteFrequency(BUTTON_LED_PIN, 25000);  // 25kHz PWM frequency
  analogWrite(BUTTON_LED_PIN, 0);  // Start off
  // Serial.println("✓ Button LED PWM initialized on pin 1 (TX)");
  
  // Initialize Language Button LED PWM
  pinMode(LANGUAGE_BUTTON_LED_PIN, OUTPUT);
  analogWriteFrequency(LANGUAGE_BUTTON_LED_PIN, 25000);  // 25kHz PWM frequency
  analogWrite(LANGUAGE_BUTTON_LED_PIN, 0);  // Start off
  // Serial.println("✓ Language Button LED PWM initialized on pin 22");
  
  // Initialize City LEDs
  FastLED.addLeds<LED_TYPE, 3, COLOR_ORDER>(leds1, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 4, COLOR_ORDER>(leds2, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 5, COLOR_ORDER>(leds3, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 6, COLOR_ORDER>(leds4, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 7, COLOR_ORDER>(leds5, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 8, COLOR_ORDER>(leds6, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 9, COLOR_ORDER>(leds7, NUM_LEDS_PER_STRIP);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 1300); // 5V and 2A max for all LEDs combined
  // FastLED.setMaxPowerInVoltsAndMilliamps(3.3, 2000); // 3.3V and 2A max for all LEDs combined
  // FastLED.setBrightness(LED_BRIGHTNESS);
  setAllCitiesOff();
  // Serial.println("✓ City LEDs initialized on pins 3-9");

  delay(1000);
  // Initialize M0 board tracking
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    m0Boards[i].detectState = 0;
    m0Boards[i].isRegistered = false;
    m0Boards[i].isCorrect = false;
    m0Boards[i].responseReceived = false;
    m0Boards[i].address = m0Addresses[i];
  }
  
  // Start in READY_IDLE state
  changeGameState(GAME_READY_IDLE);
  lastActivityTime = millis();
  

  // Serial.println("'2' = Force READY_IDLE");
  // Serial.println("'3' = Force ACTIVE");
  // Serial.println("'4' = Force PRE_RESULTS");
  // Serial.println("'5' = Force RESULTS");
  // Serial.println("'p' = Poll M0 boards");
  // Serial.println("'e' = Simulate energy switch pull");
  // Serial.println("'s' = Print current state status");

}

void loop() {
  static uint32_t lastPollTime = 0;
  static uint32_t lastStatusPrintTime = 0;
  const uint32_t POLL_INTERVAL = 500;  // Poll M0s every 500ms
  const uint32_t STATUS_PRINT_INTERVAL = 5000;  // Print status every 5 seconds
  
  // RAW diagnostic: bypasses debounce entirely, prints on any raw pin change
  static bool lastRawPinState = digitalRead(ENERGY_SWITCH_PIN);
  bool rawPinState = digitalRead(ENERGY_SWITCH_PIN);
  if (rawPinState != lastRawPinState) {
    Serial.print("[RAW] Pin 14 changed to ");
    Serial.println(rawPinState == HIGH ? "HIGH" : "LOW");
    lastRawPinState = rawPinState;
  }
  
  // Language button works in any game state - sends Space keypress to Godot
  if (checkLanguageButtonPressed()) {
    Keyboard.press(' ');
    delay(50);
    Keyboard.release(' ');
  }
  
  // Update city LEDs continuously
  updateCityLEDs();
  
  // Update button LED breathing effects
  updateButtonLED();
  updateLanguageButtonLED();
  
  // Handle serial dev tools
  handleSerialDevTools();
  
  // Periodic status printing 
  if (currentGameState != GAME_PRE_RESULTS && 
      (millis() - lastStatusPrintTime >= STATUS_PRINT_INTERVAL)) {
    printCurrentStateStatus();
    lastStatusPrintTime = millis();
  }
  
  // State machine
  switch (currentGameState) {
    
    // READY_IDLE: Wait for piece registration 
    case GAME_READY_IDLE:
      // Check if energy switch is pulled (ignore in READY_IDLE)
      if (checkEnergySwitchPulled()) {
        // Serial.println("\n[READY_IDLE] Energy switch pulled too early!");
        // Ignore - no audio feedback
      }
      
      // Poll M0 boards periodically to update status
      if (millis() - lastPollTime >= POLL_INTERVAL) {
        // Poll quietly (detailed status available via 's' dev command)
        pollM0Boards();
        lastPollTime = millis();
        
        // Check if any piece is being registered or fully registered
        // detectState: 0=IDLE, 1=DEBOUNCING, 2=REGISTERING, 3=CORRECT, 4=INCORRECT
        bool anyPieceDetected = false;
        for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
          if (m0Boards[i].detectState >= 2) {
            anyPieceDetected = true;
            // Serial.print("\n  Detected piece on M0 #");
            // Serial.print(i + 1);
            // Serial.print(" (state=");
            // Serial.print(m0Boards[i].detectState);
            // Serial.print(")");
            break;
          }
        }
        
        if (anyPieceDetected) {
          // Serial.println("\n>>> PIECE DETECTED - Game starting!");
          previousRegisteredCount = 0;  // Reset for ACTIVE state
          lastActivityTime = millis();  // Reset inactivity timer
          changeGameState(GAME_ACTIVE);
        }
      }
      break;
    
    // ── ACTIVE: Game in progress, wait for energy switch ───────────────────────
    case GAME_ACTIVE:
      // Poll M0 boards periodically to update status
      if (millis() - lastPollTime >= POLL_INTERVAL) {
        pollM0Boards();
        lastPollTime = millis();
        
        // Track piece registration changes for activity timer and sound
        uint8_t currentRegisteredCount = 0;
        for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
          if (m0Boards[i].isRegistered) {
            currentRegisteredCount++;
          }
        }
        
        // Check if registration count changed (piece added or removed)
        if (currentRegisteredCount != previousRegisteredCount) {
          lastActivityTime = millis();  // Reset inactivity timer
          
          // Signal Godot when a NEW piece is added
          if (currentRegisteredCount > previousRegisteredCount) {
            // Serial.println("[ACTIVE] Piece registered!");
            Keyboard.press('p');
            delay(50);
            Keyboard.release('p');
          }
          
          previousRegisteredCount = currentRegisteredCount;
        }
      }
      
      // Check for inactivity timeout (2 minutes)
      if (millis() - lastActivityTime >= INACTIVITY_TIMEOUT_MS) {
        // Serial.println("\n>>> INACTIVITY TIMEOUT - Auto-resetting game!");
        changeGameState(GAME_READY_IDLE);
      }
      
          // Energy switch only works in ACTIVE state
      if (checkEnergySwitchPulled()) {
        Serial.println("\n>>> ENERGY SWITCH PULLED - Checking results!");
        preResultsProcessed = false;  // Reset flag for next results check
        changeGameState(GAME_PRE_RESULTS);
        delay(150);  // Let the M0s finish processing the PRE_RESULTS state change before polling.
      }
      break;
    
    // PRE_RESULTS: Poll M0s for final results 
    case GAME_PRE_RESULTS:
      // Keep debounce state in sync even though a pull here has no effect
      checkEnergySwitchPulled();
      
      // Only process results once when entering this state
      if (!preResultsProcessed) {
        // Serial.println("\n[PRE_RESULTS] Collecting final board states...");
        delay(100);  // Give the M0s a brief settle window after the state transition.
        pollM0Boards(false);  //turn to true for verbose output
        
        delay(100);
        processResults();
        
        preResultsProcessed = true;
        changeGameState(GAME_RESULTS);
      }
      break;
    
    // RESULTS: Display results, then auto-reset
    case GAME_RESULTS:
      {
        // Check if results display time has elapsed
        uint32_t elapsed = millis() - resultsDisplayStartTime;
        uint32_t remaining = (elapsed < RESULTS_DISPLAY_DURATION_MS) ? 
                             (RESULTS_DISPLAY_DURATION_MS - elapsed) / 1000 : 0;
        
        static uint32_t lastCountdownPrint = 0;
        if (millis() - lastCountdownPrint >= 1000 && remaining > 0) {
          // Serial.print("[RESULTS] Resetting in ");
          // Serial.print(remaining);
          // Serial.println(" seconds... (press 'r' to reset now)");
          lastCountdownPrint = millis();
        }
        
        if (elapsed >= RESULTS_DISPLAY_DURATION_MS) {
          // Serial.println("\n>>> Results display time complete - ready for next game!");
          changeGameState(GAME_READY_IDLE);
        }
      }
      break;
  }
  
  delay(10);
}

// ══════════════════════════════════════════════════════════════════════════════
// GAME STATE MANAGEMENT
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Change game state and notify all M0 boards
 */
void changeGameState(GameState newState) {
  if (newState == currentGameState) return;
  
  GameState oldState = currentGameState;
  currentGameState = newState;
  
  // Serial.println("\n╔══════════════════════════════════════════════════════════╗");
  // Serial.print("║  STATE TRANSITION: ");
  // Serial.print(getGameStateName(oldState));
  // Serial.print(" → ");
  // Serial.print(getGameStateName(newState));
  // Serial.println("  ║");
  // Serial.println("╚══════════════════════════════════════════════════════════╝");
  
  // Send new state to all M0 boards
  sendGameStateToM0s();
  delay(100);  // Give the M0s time to process the state-change write before the next poll.
  
  // State-specific initialization
  switch (currentGameState) {
    case GAME_READY_IDLE:
      Keyboard.press('i');
      delay(50);
      Keyboard.release('i');
      break;
      
    case GAME_ACTIVE:
      Keyboard.press('g');
      delay(50);
      Keyboard.release('g');
      break;
      
    case GAME_PRE_RESULTS:
      preResultsProcessed = false;
      break;
      
    case GAME_RESULTS:
      Keyboard.press('s');
      delay(50);
      Keyboard.release('s');
      resultsDisplayStartTime = millis();
      break;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// I2C COMMUNICATION
// ══════════════════════════════════════════════════════════════════════════════

// Send current game state to all M0 boards via I2C
void sendGameStateToM0s() {
  uint8_t successCount = 0;

  acquireI2CBus();
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    Wire.beginTransmission(m0Addresses[i]);
    Wire.write((uint8_t)currentGameState);
    uint8_t error = Wire.endTransmission();
    if (error == 0) {
      successCount++;
    }
    delayMicroseconds(200);
  }
  releaseI2CBus();
}

/**
 * Poll all M0 boards and update their status
 * Print results with dev command 'p'
 */
void pollM0Boards(bool verbose) {
  uint8_t registeredCount = 0;
  uint8_t correctCount = 0;
  uint8_t incorrectCount = 0;
  uint8_t unregisteredCount = 0;

  acquireI2CBus();
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    uint8_t bytesReceived = Wire.requestFrom(m0Addresses[i], (uint8_t)14);

    if (bytesReceived == 14) {
      m0Boards[i].detectState = Wire.read();
      m0Boards[i].s1Polarity = Wire.read();
      m0Boards[i].s2Polarity = Wire.read();
      m0Boards[i].s3Polarity = Wire.read();
      m0Boards[i].address = Wire.read();
      m0Boards[i].gameState = Wire.read();
      m0Boards[i].isRegistered = Wire.read() == 1;
      m0Boards[i].isCorrect = Wire.read() == 1;

      uint8_t raw1High = Wire.read();
      uint8_t raw1Low = Wire.read();
      m0Boards[i].rawSensor1 = (raw1High << 8) | raw1Low;

      uint8_t raw2High = Wire.read();
      uint8_t raw2Low = Wire.read();
      m0Boards[i].rawSensor2 = (raw2High << 8) | raw2Low;

      uint8_t raw3High = Wire.read();
      uint8_t raw3Low = Wire.read();
      m0Boards[i].rawSensor3 = (raw3High << 8) | raw3Low;

      m0Boards[i].responseReceived = true;

      if (m0Boards[i].isRegistered) {
        registeredCount++;
        if (m0Boards[i].isCorrect) {
          correctCount++;
        } else {
          incorrectCount++;
        }
      } else {
        unregisteredCount++;
      }

      if (verbose) {
        Serial.print(" | M0#");
        Serial.print(i + 1);
        Serial.print("(0x");
        Serial.print(m0Addresses[i], HEX);
        Serial.print("):state=");
        Serial.print(m0Boards[i].detectState);
      }
    } else {
      while (Wire.available()) {
        Wire.read();
      }
      m0Boards[i].responseReceived = false;

      if (verbose) {
        Serial.print("\n  ⚠ M0 #");
        Serial.print(i + 1);
        Serial.print(" at 0x");
        Serial.print(m0Addresses[i], HEX);
        Serial.print(": received ");
        Serial.print(bytesReceived);
        Serial.print("/14 bytes");
      }

      if (bytesReceived == 0 || bytesReceived < 14) {
        resetI2CBus();
        break;
      }
    }
    delayMicroseconds(200);
  }
  releaseI2CBus();

  if (verbose) {
    Serial.print("\n  Status: ");
    Serial.print(registeredCount);
    Serial.print(" registered (");
    Serial.print(correctCount);
    Serial.print(" correct, ");
    Serial.print(incorrectCount);
    Serial.print(" incorrect), ");
    Serial.print(unregisteredCount);
    Serial.println(" unregistered");
  }
}

/**
 * Placement validity
 * Polarity values: 0=UNCERTAIN, 1=SOUTH, 2=NORTH
 * Sensor mapping: s1=S1 (middle), s2=S2 (left), s3=S3 (right)
 */
bool validatePiecePlacement(uint8_t address, uint8_t s1, uint8_t s2, uint8_t s3) {
  bool isBuoy  = (s1 == 1 && s2 == 1 && s3 == 1);  // All SOUTH
  bool isDam   = (s1 == 2 && s2 == 2 && s3 == 2);  // All NORTH
  bool isGeo   = (s1 == 1) && ((s2 == 2 && s3 == 0) || (s2 == 0 && s3 == 2));  // S1=SOUTH + one NORTH
  bool isSolar = (s1 == 0) && ((s2 == 2 && s3 == 0) || (s2 == 0 && s3 == 2));  // S1=UNCERTAIN + one NORTH
  bool isWind  = (s1 == 2) && ((s2 == 2 && s3 == 0) || (s2 == 0 && s3 == 2));  // S1=NORTH + one NORTH
  
  switch (address) {
    // Type Buoy: 0x08, 0x0C (accepts gpppppppp + Wind)
    case 0x08:
    case 0x0C:
      return (isBuoy || isWind);
    
    // Type Dam: 0x09, 0x0D, 0x10 (accepts Dam + Wind + Solar)
    case 0x09:
    case 0x0D:
    case 0x10:
      return (isDam || isWind || isSolar);
    
    // Type Geo: 0x0A, 0x0E, 0x0F, 0x11 (accepts Geo + Wind + Solar)
    case 0x0A:
    case 0x0E:
    case 0x0F:
    case 0x11:
      return (isGeo || isWind || isSolar);
    
    // Type Solar: 0x0B (accepts Solar + Wind)
    case 0x0B:
      return (isSolar || isWind);
    
    default:
      return false;
  }
}

//Process results and determine WIN/YELLOW/FAIL
void processResults() {
  
  uint8_t registeredCount = 0;
  uint8_t correctCount = 0;
  uint8_t incorrectCount = 0;
  
  Serial.println("\n[DEBUG] Polled M0 Board States:");
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    Serial.print("  M0#");
    Serial.print(i + 1);
    Serial.print(" [0x");
    Serial.print(m0Addresses[i], HEX);
    Serial.print("]: S1=");
    Serial.print(m0Boards[i].s1Polarity);
    Serial.print(" S2=");
    Serial.print(m0Boards[i].s2Polarity);
    Serial.print(" S3=");
    Serial.print(m0Boards[i].s3Polarity);
    Serial.print(" | Raw[0]=");
    Serial.print(m0Boards[i].rawSensor1);
    Serial.print(" Raw[1]=");
    Serial.print(m0Boards[i].rawSensor2);
    Serial.print(" Raw[2]=");
    Serial.print(m0Boards[i].rawSensor3);
    Serial.print(" | isReg=");
    Serial.print(m0Boards[i].isRegistered);
    Serial.print(", isCorr=");
    Serial.print(m0Boards[i].isCorrect);
    Serial.println();
    
    if (m0Boards[i].isRegistered) {
      registeredCount++;
      // Use M0's correctness determination
      if (m0Boards[i].isCorrect) {
        correctCount++;
      } else {
        incorrectCount++;
      }
    }
  }
  
  Serial.print("[DEBUG] COUNTS: registered=");
  Serial.print(registeredCount);
  Serial.print(", correct=");
  Serial.print(correctCount);
  Serial.print(", incorrect=");
  Serial.println(incorrectCount);
  
  
  if (correctCount == NUM_M0_BOARDS) {
    //RAINBOW
    Serial.println("[DEBUG] OUTCOME: WIN");
  }
  else if (correctCount > 0) {
    //YELLOW - any correct piece, but not all
    Serial.println("[DEBUG] OUTCOME: YELLOW");
  }
  else {
    //RED - none correct
    Serial.println("[DEBUG] OUTCOME: FAIL");
  }
  
}


void handleSerialDevTools() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    //Dev commands for switching states
    switch (cmd) {
      case '2':
        changeGameState(GAME_READY_IDLE);
        break;
        
      case '3':
        changeGameState(GAME_ACTIVE);
        break;
        
      case '4':
        changeGameState(GAME_PRE_RESULTS);
        break;
        
      case '5':
        changeGameState(GAME_RESULTS);
        break;
        
      case 'p':
      case 'P':
        Serial.println("\n[DEV] Polling M0 boards...");
        pollM0Boards(true);  
        break;
        
      case 'i':
      case 'I':
        Serial.println("\n[DEV] Scanning I2C bus...");
        scanI2CBus();
        break;
        
      case 'e':
      case 'E':
        if (currentGameState == GAME_ACTIVE) {
          changeGameState(GAME_PRE_RESULTS);
        }
        break;
        
      case 's':
      case 'S':
        Serial.println("\n[DEV] Current state status:");
        printCurrentStateStatus();
        break;
        
      case '\n':
      case '\r':
        // Ignore newlines
        break;
        
      default:
        // Ignore unknown commands
        break;
    }
  }
}

bool checkEnergySwitchPulled() {
  energySwitchDebouncer.update();
  if (energySwitchDebouncer.fell()) {
    Serial.println("[DEBUG] Energy switch PULLED (edge detected)");
    return true;
  }
  return false;
}

bool checkLanguageButtonPressed() {
  languageButtonDebouncer.update();
  if (languageButtonDebouncer.fell()) {
    return true;
  }
  return false;
}

const char* getGameStateName(GameState state) {
  switch (state) {
    case GAME_READY_IDLE:  return "READY_IDLE";
    case GAME_ACTIVE:      return "ACTIVE";
    case GAME_PRE_RESULTS: return "PRE_RESULTS";
    case GAME_RESULTS:     return "RESULTS";
    default:               return "UNKNOWN";
  }
}

/**
 * Scan I2C bus for devices (dev command 'i')
 */
void scanI2CBus() {
  uint8_t devicesFound = 0;
  
  Serial.println("\n┌────────────────────────────────────────────────────────┐");
  Serial.println("│  I2C Bus Scan (addresses 0x01-0x7F)                   │");
  Serial.println("├────────────────────────────────────────────────────────┤");
  
  acquireI2CBus();
  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      // Device found
      Serial.print("│  Found device at 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.print(" (");
      Serial.print(address);
      Serial.print(")  ");
      
      // Check if it's one of our expected M0s
      bool isExpected = false;
      for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
        if (m0Addresses[i] == address) {
          Serial.print(" ✓ M0#");
          Serial.print(i + 1);
          isExpected = true;
          break;
        }
      }
      
      if (!isExpected) {
        Serial.print(" ⚠ UNKNOWN");
      }
      
      int pad = isExpected ? 24 : 16;
      for (int j = 0; j < pad; j++) Serial.print(" ");
      Serial.println("│");
      
      devicesFound++;
    }
  }
  releaseI2CBus();
  
  Serial.println("├────────────────────────────────────────────────────────┤");
  Serial.print("│  Total devices found: ");
  Serial.print(devicesFound);
  Serial.print("/");
  Serial.print(NUM_M0_BOARDS);
  Serial.print(" expected");
  int pad = 26 - (devicesFound >= 10 ? 2 : 1) - (NUM_M0_BOARDS >= 10 ? 2 : 1);
  for (int i = 0; i < pad; i++) Serial.print(" ");
  Serial.println("│");
  Serial.println("└────────────────────────────────────────────────────────┘");
  
  // List missing M0s
  if (devicesFound < NUM_M0_BOARDS) {
    Serial.println("\nMissing M0 boards:");
    acquireI2CBus();
    for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
      Wire.beginTransmission(m0Addresses[i]);
      uint8_t error = Wire.endTransmission();
      if (error != 0) {
        Serial.print("  M0#");
        Serial.print(i + 1);
        Serial.print(" at 0x");
        Serial.print(m0Addresses[i], HEX);
        Serial.println(" - NO RESPONSE");
      }
    }
    releaseI2CBus();
  }
}


void printCurrentStateStatus() {
  Serial.println("\n┌────────────────────────────────────────────────────────┐");
  Serial.print("│  Current State: ");
  Serial.print(getGameStateName(currentGameState));
  for (int i = 0; i < 38 - strlen(getGameStateName(currentGameState)); i++) Serial.print(" ");
  Serial.println("│");
 
  uint8_t registered = 0, correct = 0, incorrect = 0, responding = 0;
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    if (m0Boards[i].responseReceived) {
      responding++;
      if (m0Boards[i].isRegistered) {
        registered++;
        // Use M0's correctness determination
        if (m0Boards[i].isCorrect) correct++;
        else incorrect++;
      }
    }
  }
  
  Serial.print("│  M0 Boards: ");
  Serial.print(responding);
  Serial.print("/");
  Serial.print(NUM_M0_BOARDS);
  Serial.print(" responding");
  int padding1 = 36 - (responding >= 10 ? 2 : 1) - (NUM_M0_BOARDS >= 10 ? 2 : 1);
  for (int i = 0; i < padding1; i++) Serial.print(" ");
  
  Serial.print("│  Registered: ");
  Serial.print(registered);
  Serial.print("/");
  Serial.print(NUM_M0_BOARDS);
  Serial.print(" | Correct: ");
  Serial.print(correct);
  Serial.print(" | Incorrect: ");
  Serial.print(incorrect);

  int padding = 24 - (registered >= 10 ? 2 : 1) - (correct >= 10 ? 2 : 1) - (incorrect >= 10 ? 2 : 1);
  for (int i = 0; i < padding; i++) Serial.print(" ");
  Serial.println("");
  
  Serial.print("│  Energy Switch: ");
  Serial.print(digitalRead(ENERGY_SWITCH_PIN) == HIGH ? "READY" : "PULLED");
  Serial.print("                              │");
  Serial.println();
  
  Serial.println("├────────────────────────────────────────────────────────┤");
  Serial.println("│  Individual M0 Board Status:                          │");
  
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    Serial.print("│  M0#");
    Serial.print(i + 1);
    if (i < 9) Serial.print(" ");
    Serial.print(" [0x");
    Serial.print(m0Addresses[i], HEX);
    Serial.print("]: ");
    
    if (!m0Boards[i].responseReceived) {
      Serial.print("NO RESPONSE");
      for (int j = 0; j < 30; j++) Serial.print(" ");
    } else if (!m0Boards[i].isRegistered) {
      Serial.print("Empty (state=");
      Serial.print(m0Boards[i].detectState);
      Serial.print(")");
      int pad = 22 - (m0Boards[i].detectState >= 10 ? 2 : 1);
      for (int j = 0; j < pad; j++) Serial.print(" ");
    } else {
      // Use M0's correctness determination
      if (m0Boards[i].isCorrect) {
        Serial.print("✓ CORRECT");
        for (int j = 0; j < 32; j++) Serial.print(" ");
      } else {
        Serial.print("✗ INCORRECT");
        for (int j = 0; j < 30; j++) Serial.print(" ");
      }
    }
    Serial.println("│");
  }
  
  Serial.println("└────────────────────────────────────────────────────────┘");
}

//Update City LEDs
void updateCityLEDs() {
  switch (currentGameState) {
    case GAME_READY_IDLE:
    case GAME_ACTIVE:
      // No lights during gameplay
      setAllCitiesOff();
      break;
      
    case GAME_RESULTS:
      // Show results-based colors
      {
        uint8_t registeredCount = 0;
        uint8_t correctCount = 0;
        uint8_t incorrectCount = 0;
        
        for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
          if (m0Boards[i].isRegistered) {
            registeredCount++;
            // Use M0's correctness determination
            if (m0Boards[i].isCorrect) {
              correctCount++;
            } else {
              incorrectCount++;
            }
          }
        }
        
        // All boards registered and correct - Rainbow animation
        if (correctCount == NUM_M0_BOARDS) {
          setAllCitiesRainbow();
        }
        // Any correct piece, but not all - Yellow
        else if (correctCount > 0) {
          setAllCitiesColor(CRGB::Yellow);
        }
        // None correct - Red
        else {
          setAllCitiesColor(CRGB::Red);
        }
      }
      break;
      
    case GAME_PRE_RESULTS:
      // Keep lights off during pre-results
      setAllCitiesOff();
      break;
  }
}

void setAllCitiesColor(CRGB color) {
  fill_solid(leds1, NUM_LEDS_PER_STRIP, color);
  fill_solid(leds2, NUM_LEDS_PER_STRIP, color);
  fill_solid(leds3, NUM_LEDS_PER_STRIP, color);
  fill_solid(leds4, NUM_LEDS_PER_STRIP, color);
  fill_solid(leds5, NUM_LEDS_PER_STRIP, color);
  fill_solid(leds6, NUM_LEDS_PER_STRIP, color);
  fill_solid(leds7, NUM_LEDS_PER_STRIP, color);
  FastLED.show();
}

void setAllCitiesPulsating(CRGB baseColor, uint8_t minBright, uint8_t maxBright, uint16_t periodMs) {
  uint32_t now = millis();
  
  // Use triangle wave for pulsing
  float phase = (float)(now % periodMs) / periodMs;
  float triangleWave = (phase < 0.5) ? (phase * 2.0) : (2.0 - phase * 2.0);
  uint8_t brightness = minBright + (uint8_t)(triangleWave * (maxBright - minBright));
  
  // Apply brightness to base color
  CRGB color = baseColor;
  color.nscale8(brightness);
  
  setAllCitiesColor(color);
}

void setAllCitiesRainbow() {
  static uint8_t hueOffset = 0;
  
  // Shifting rainbow gradient
  fill_rainbow(leds1, NUM_LEDS_PER_STRIP, hueOffset, 255 / NUM_LEDS_PER_STRIP);
  fill_rainbow(leds2, NUM_LEDS_PER_STRIP, hueOffset + 10, 255 / NUM_LEDS_PER_STRIP);
  fill_rainbow(leds3, NUM_LEDS_PER_STRIP, hueOffset + 20, 255 / NUM_LEDS_PER_STRIP);
  fill_rainbow(leds4, NUM_LEDS_PER_STRIP, hueOffset + 30, 255 / NUM_LEDS_PER_STRIP);
  fill_rainbow(leds5, NUM_LEDS_PER_STRIP, hueOffset + 40, 255 / NUM_LEDS_PER_STRIP);
  fill_rainbow(leds6, NUM_LEDS_PER_STRIP, hueOffset + 50, 255 / NUM_LEDS_PER_STRIP);
  fill_rainbow(leds7, NUM_LEDS_PER_STRIP, hueOffset + 60, 255 / NUM_LEDS_PER_STRIP);
  
  FastLED.show();
  
  // Animate by shifting hue over time
  hueOffset += 2;  // Speed of rainbow shift
}

void setAllCitiesOff() {
  setAllCitiesColor(CRGB::Black);
}

// Update button LED with subtle breathing effect
void updateButtonLED() {
  static const uint16_t BREATH_PERIOD_MS = 3000;  // 3 second breathing cycle
  static const uint8_t MIN_BRIGHTNESS = 20;       // Minimum PWM (subtle presence)
  static const uint8_t MAX_BRIGHTNESS = 180;      // Maximum PWM (inviting but not harsh)
  
  uint32_t now = millis();
  float phase = (float)(now % BREATH_PERIOD_MS) / BREATH_PERIOD_MS;  // 0.0 to 1.0
  
  // Use sine wave for smooth, natural breathing effect
  float sineWave = (sin(phase * 2.0 * PI - PI/2.0) + 1.0) / 2.0;  // 0.0 to 1.0
  
  uint8_t brightness = MIN_BRIGHTNESS + (uint8_t)(sineWave * (MAX_BRIGHTNESS - MIN_BRIGHTNESS));
  analogWrite(BUTTON_LED_PIN, brightness);
}

// Update language button LED with subtle breathing effect
void updateLanguageButtonLED() {
  static const uint16_t BREATH_PERIOD_MS = 3000;  // 3 second breathing cycle
  static const uint8_t MIN_BRIGHTNESS = 20;       // Minimum PWM (subtle presence)
  static const uint8_t MAX_BRIGHTNESS = 180;      // Maximum PWM (inviting but not harsh)
  
  uint32_t now = millis();
  float phase = (float)(now % BREATH_PERIOD_MS) / BREATH_PERIOD_MS;  // 0.0 to 1.0
  
  // Use sine wave for smooth, natural breathing effect
  float sineWave = (sin(phase * 2.0 * PI - PI/2.0) + 1.0) / 2.0;  // 0.0 to 1.0
  
  uint8_t brightness = MIN_BRIGHTNESS + (uint8_t)(sineWave * (MAX_BRIGHTNESS - MIN_BRIGHTNESS));
  analogWrite(LANGUAGE_BUTTON_LED_PIN, brightness);
}