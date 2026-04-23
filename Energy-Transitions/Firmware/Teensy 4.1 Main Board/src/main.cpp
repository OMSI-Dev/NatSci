/*
 * ENERGY TRANSITIONS EXHIBIT - TEENSY 4.1 MAIN CONTROLLER
 * 
 * Manages game state machine and coordinates with ItsyBitsy M0 sensor boards
 * via I2C. Provides audio feedback using WAV Trigger.
 * 
 * GAME STATE FLOW:
 *   RESET_IDLE (red pulse, wait for empty) → 
 *   READY_IDLE (white pulse, wait for piece registration) → 
 *   ACTIVE (piece registered, pull switch to check) → 
 *   PRE_RESULTS → RESULTS → RESET_IDLE
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
 * Version: 3.0 (2026-04-22) - Phase 1 game state implementation
 */

#include <Arduino.h>
#include <Wire.h>
#include <wav_trigger.h>

// ── Audio track definitions ────────────────────────────────────────────────────
#define READY_STATE 1
#define ERROR 2
#define PIECE_REGISTERED 3
#define PULL_SWITCH 4
#define FAIL 5
#define YELLOW 6
#define WIN 7
#define RESET 8

// ── Pin definitions ────────────────────────────────────────────────────────────
#define ENERGY_SWITCH_PIN 14

// ── Game configuration ─────────────────────────────────────────────────────────
#define NUM_M0_BOARDS 4      // Number of M0 sensor boards expected
#define ENERGY_SWITCH_DEBOUNCE_MS 200  // Debounce time for energy switch

// ── Game state enum ────────────────────────────────────────────────────────────
enum GameState : uint8_t {
  GAME_RESET_IDLE  = 0,
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
  bool responseReceived;  // True if we received a response this cycle
};

// ── Global variables ───────────────────────────────────────────────────────────
GameState currentGameState = GAME_RESET_IDLE;
M0Status m0Boards[NUM_M0_BOARDS];
uint8_t m0Addresses[NUM_M0_BOARDS] = {0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11};

wavTrigger wavTrig;

// Energy switch state
bool energySwitchLastState = HIGH;
uint32_t energySwitchLastDebounceTime = 0;

// Results display timer
uint32_t resultsDisplayStartTime = 0;
const uint32_t RESULTS_DISPLAY_DURATION_MS = 10000;  // Show results for 10 seconds

// State machine control
bool preResultsProcessed = false;

void changeGameState(GameState newState);
void sendGameStateToM0s();
void pollM0Boards(bool verbose = false);
bool checkAllM0sUnregistered();
void processResults();
void handleSerialDevTools();
bool checkEnergySwitchPulled();
void printCurrentStateStatus();
const char* getGameStateName(GameState state);

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize I2C as big friend
  Wire.begin();
  Wire.setClock(100000);  // 100kHz I2C clock
  Serial.println("✓ I2C handshake)");
  
  //Energy switch 
  pinMode(ENERGY_SWITCH_PIN, INPUT_PULLUP);
  energySwitchLastState = digitalRead(ENERGY_SWITCH_PIN);
  Serial.println("✓ Energy switch initialized on pin 14");
  
  // Initialize WAV Trigger
  delay(1000);
  wavTrig.start();
  delay(10);
  wavTrig.stopAllTracks();
  wavTrig.samplerateOffset(0);
  wavTrig.masterGain(0);
  wavTrig.setAmpPwr(true);
  wavTrig.setReporting(true);
  Serial.println("✓ WAV Trigger initialized");
  
  // Initialize M0 board tracking
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    m0Boards[i].detectState = 0;
    m0Boards[i].isRegistered = false;
    m0Boards[i].isCorrect = false;
    m0Boards[i].responseReceived = false;
    m0Boards[i].address = m0Addresses[i];
  }
  
  // Start in RESET_IDLE state
  changeGameState(GAME_RESET_IDLE);
  

  Serial.println("'1' = Force RESET_IDLE");
  Serial.println("'2' = Force READY_IDLE");
  Serial.println("'3' = Force ACTIVE");
  Serial.println("'4' = Force PRE_RESULTS");
  Serial.println("'5' = Force RESULTS");
  Serial.println("'p' = Poll M0 boards");
  Serial.println("'e' = Simulate energy switch pull");
  Serial.println("'s' = Print current state status");
  Serial.println("'r' = Reset to RESET_IDLE");

}

void loop() {
  static uint32_t lastPollTime = 0;
  static uint32_t lastStatusPrintTime = 0;
  const uint32_t POLL_INTERVAL = 500;  // Poll M0s every 500ms
  const uint32_t STATUS_PRINT_INTERVAL = 5000;  // Print status every 5 seconds
  
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
    
    // RESET_IDLE: Wait for all M0s to report unregistered 
    case GAME_RESET_IDLE:
      // Poll M0 boards periodically
      if (millis() - lastPollTime >= POLL_INTERVAL) {
        // Poll quietly (detailed status available via 's' dev command)
        pollM0Boards();
        lastPollTime = millis();
        
        // Check if all pieces have been removed (all boards in IDLE state)
        if (checkAllM0sUnregistered()) {
          Serial.println(">>> All pieces removed - ready for new game!");
          changeGameState(GAME_READY_IDLE);
        }
      }
      break;
    
    // READY_IDLE: Wait for piece registration 
    case GAME_READY_IDLE:
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
            Serial.print("\n  Detected piece on M0 #");
            Serial.print(i + 1);
            Serial.print(" (state=");
            Serial.print(m0Boards[i].detectState);
            Serial.print(")");
            break;
          }
        }
        
        if (anyPieceDetected) {
          Serial.println("\n>>> PIECE DETECTED - Game starting!");
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
      }
      
      // Energy switch only works in ACTIVE state
      if (checkEnergySwitchPulled()) {
        Serial.println("\n>>> ENERGY SWITCH PULLED - Checking results!");
        preResultsProcessed = false;  // Reset flag for next results check
        changeGameState(GAME_PRE_RESULTS);
      }
      break;
    
    // PRE_RESULTS: Poll M0s for final results 
    case GAME_PRE_RESULTS:
      // Only process results once when entering this state
      if (!preResultsProcessed) {
        Serial.println("\n[PRE_RESULTS] Collecting final board states...");
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
          Serial.print("[RESULTS] Resetting in ");
          Serial.print(remaining);
          Serial.println(" seconds... (press 'r' to reset now)");
          lastCountdownPrint = millis();
        }
        
        if (elapsed >= RESULTS_DISPLAY_DURATION_MS) {
          Serial.println("\n>>> Results display time complete - resetting game!");
          changeGameState(GAME_RESET_IDLE);
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
  
  Serial.println("\n╔══════════════════════════════════════════════════════════╗");
  Serial.print("║  STATE TRANSITION: ");
  Serial.print(getGameStateName(oldState));
  Serial.print(" → ");
  Serial.print(getGameStateName(newState));
  Serial.println("  ║");
  Serial.println("╚══════════════════════════════════════════════════════════╝");
  
  // Send new state to all M0 boards
  sendGameStateToM0s();
  
  // State-specific initialization
  switch (currentGameState) {
    case GAME_RESET_IDLE:
      Serial.println("[INIT] Remove all pieces (M0s show pulsing RED)...");
      wavTrig.trackPlayPoly(RESET);
      break;
      
    case GAME_READY_IDLE:
      Serial.println("[INIT] Ready! Place a piece to start (M0s show pulsing WHITE).");
      wavTrig.trackPlayPoly(READY_STATE);
      break;
      
    case GAME_ACTIVE:
      Serial.println("[INIT] Game active! Arrange pieces, pull energy switch to check.");
      // No sound on transition to active
      break;
      
    case GAME_PRE_RESULTS:
      Serial.println("[INIT] Preparing to check results...");
      wavTrig.trackPlayPoly(PULL_SWITCH);
      preResultsProcessed = false;
      break;
      
    case GAME_RESULTS:
      Serial.println("[INIT] Displaying results...");
      resultsDisplayStartTime = millis();
      // Sound played in processResults()
      break;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// I2C COMMUNICATION
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Send current game state to all M0 boards via I2C
 */
void sendGameStateToM0s() {
  Serial.print("  → Broadcasting game state ");
  Serial.print((uint8_t)currentGameState);
  Serial.println(" to all M0 boards...");
  
  uint8_t successCount = 0;
  
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    Wire.beginTransmission(m0Addresses[i]);
    Wire.write((uint8_t)currentGameState);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      successCount++;
    } else {
      Serial.print("    ⚠ Failed to reach M0 at 0x");
      Serial.print(m0Addresses[i], HEX);
      Serial.print(" (error ");
      Serial.print(error);
      Serial.println(")");
    }
  }
  
  Serial.print("  ✓ Sent to ");
  Serial.print(successCount);
  Serial.print("/");
  Serial.print(NUM_M0_BOARDS);
  Serial.println(" boards");
}

/**
 * Poll all M0 boards and update their status
 * Pass verbose=true to print detailed status (used by dev tools)
 */
void pollM0Boards(bool verbose = false) {
  uint8_t registeredCount = 0;
  uint8_t correctCount = 0;
  uint8_t incorrectCount = 0;
  uint8_t unregisteredCount = 0;
  
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    // Request 8 bytes from M0
    uint8_t bytesReceived = Wire.requestFrom(m0Addresses[i], (uint8_t)8);
    
    if (bytesReceived == 8) {
      m0Boards[i].detectState = Wire.read();
      m0Boards[i].s1Polarity = Wire.read();
      m0Boards[i].s2Polarity = Wire.read();
      m0Boards[i].s3Polarity = Wire.read();
      m0Boards[i].address = Wire.read();
      m0Boards[i].gameState = Wire.read();
      m0Boards[i].isRegistered = Wire.read() == 1;
      m0Boards[i].isCorrect = Wire.read() == 1;
      m0Boards[i].responseReceived = true;
      
      // Count states
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
      
      // Debug: Show individual M0 states (only if verbose)
      if (verbose) {
        Serial.print(" | M0#");
        Serial.print(i + 1);
        Serial.print("(0x");
        Serial.print(m0Addresses[i], HEX);
        Serial.print("):state=");
        Serial.print(m0Boards[i].detectState);
      }
    } else {
      m0Boards[i].responseReceived = false;
      // Always show communication errors
      Serial.print("\n  ⚠ No response from M0 #");
      Serial.print(i + 1);
      Serial.print(" at 0x");
      Serial.print(m0Addresses[i], HEX);
      Serial.print(" (received ");
      Serial.print(bytesReceived);
      Serial.print(" bytes)");
    }
  }
  
  // Print status summary (only if verbose)
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

//M0 boards status - registered/unregistered, correct/incorrect, response received
bool checkAllM0sUnregistered() {
  bool allClear = true;
  
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    if (!m0Boards[i].responseReceived) {
      // Haven't received response from this board yet
      Serial.print("  !!! M0 #");
      Serial.print(i + 1);
      Serial.print(" at 0x");
      Serial.print(m0Addresses[i], HEX);
      Serial.println(" - No response");
      allClear = false;
      continue;
    }
    // Check that board is in IDLE or DEBOUNCING state (0 or 1)
    // detectState: 0=IDLE, 1=DEBOUNCING, 2=REGISTERING, 3=CORRECT, 4=INCORRECT
    if (m0Boards[i].detectState >= 2) {
      Serial.print("  !!! M0 #");
      Serial.print(i + 1);
      Serial.print(" at 0x");
      Serial.print(m0Addresses[i], HEX);
      Serial.print(" - Still has piece (state=");
      Serial.print(m0Boards[i].detectState);
      Serial.println(")");
      allClear = false;
    }
  }
  
  return allClear; 
}

//Process results and determine WIN/YELLOW/FAIL
void processResults() {
  Serial.println("\n═══════════════════════════════════════════════════════════");
  Serial.println("  FINAL RESULTS:");
  Serial.println("═══════════════════════════════════════════════════════════");
  
  uint8_t registeredCount = 0;
  uint8_t correctCount = 0;
  uint8_t incorrectCount = 0;
  
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    Serial.print("  Slot ");
    Serial.print(i + 1);
    Serial.print(" [0x");
    Serial.print(m0Addresses[i], HEX);
    Serial.print("]: ");
    
    if (m0Boards[i].isRegistered) {
      registeredCount++;
      if (m0Boards[i].isCorrect) {
        correctCount++;
        Serial.println("O CORRECT");
      } else {
        incorrectCount++;
        Serial.println("X INCORRECT");
      }
    } else {
      Serial.println("○ EMPTY");
    }
  }
  
  // Serial.println("───────────────────────────────────────────────────────────");
  // Serial.print("  Total: ");
  // Serial.print(correctCount);
  // Serial.print(" correct, ");
  // Serial.print(incorrectCount);
  // Serial.print(" incorrect, ");
  // Serial.print(NUM_M0_BOARDS - registeredCount);
  // Serial.println(" empty");
  // Serial.println("═══════════════════════════════════════════════════════════");
  
  if (correctCount == NUM_M0_BOARDS) {
    // All correct - WIN
    Serial.println("OUTCOME: WIN");
    wavTrig.trackPlayPoly(WIN);
  }
  else if (registeredCount == NUM_M0_BOARDS && correctCount > 0 && incorrectCount > 0) {
    // All registered, mix of correct and incorrect - YELLOW
    Serial.println("OUTCOME: YELLOW");
    wavTrig.trackPlayPoly(YELLOW);
  }
  else {
    Serial.println("OUTCOME: FAIL");
    wavTrig.trackPlayPoly(FAIL);
  }
  
  Serial.println("═══════════════════════════════════════════════════════════\n");
}

// ══════════════════════════════════════════════════════════════════════════════
// DEV TOOLS
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Handle serial input for development tools
 */
void handleSerialDevTools() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    switch (cmd) {
      case '1':
        Serial.println("\n[DEV] Forcing RESET_IDLE state");
        changeGameState(GAME_RESET_IDLE);
        break;
        
      case '2':
        Serial.println("\n[DEV] Forcing READY_IDLE state");
        changeGameState(GAME_READY_IDLE);
        break;
        
      case '3':
        Serial.println("\n[DEV] Forcing ACTIVE state");
        changeGameState(GAME_ACTIVE);
        break;
        
      case '4':
        Serial.println("\n[DEV] Forcing PRE_RESULTS state");
        changeGameState(GAME_PRE_RESULTS);
        break;
        
      case '5':
        Serial.println("\n[DEV] Forcing RESULTS state");
        changeGameState(GAME_RESULTS);
        break;
        
      case 'p':
      case 'P':
        Serial.println("\n[DEV] Polling M0 boards...");
        pollM0Boards(true);  // Verbose output
        break;
        
      case 'e':
      case 'E':
        Serial.println("\n[DEV] Simulating energy switch pull");
        if (currentGameState == GAME_ACTIVE) {
          // Energy switch only works during ACTIVE state
          changeGameState(GAME_PRE_RESULTS);
        } else {
          Serial.println("  X Energy switch only works during ACTIVE state!");
        }
        break;
        
      case 's':
      case 'S':
        Serial.println("\n[DEV] Current state status:");
        printCurrentStateStatus();
        break;
        
      case 'r':
      case 'R':
        Serial.println("\n[DEV] Manual reset to RESET_IDLE");
        changeGameState(GAME_RESET_IDLE);
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
  bool currentState = digitalRead(ENERGY_SWITCH_PIN);
  
  if (currentState != energySwitchLastState) {
    energySwitchLastDebounceTime = millis();
  }
  
  if ((millis() - energySwitchLastDebounceTime) > ENERGY_SWITCH_DEBOUNCE_MS) {
    // Switch state has been stable for debounce period
    if (currentState == LOW && energySwitchLastState == HIGH) {
      // Switch was pulled (HIGH to LOW transition)
      energySwitchLastState = currentState;
      return true;
    }
  }
  
  energySwitchLastState = currentState;
  return false;
}

const char* getGameStateName(GameState state) {
  switch (state) {
    case GAME_RESET_IDLE:  return "RESET_IDLE";
    case GAME_READY_IDLE:  return "READY_IDLE";
    case GAME_ACTIVE:      return "ACTIVE";
    case GAME_PRE_RESULTS: return "PRE_RESULTS";
    case GAME_RESULTS:     return "RESULTS";
    default:               return "UNKNOWN";
  }
}


void printCurrentStateStatus() {
  Serial.println("\n┌────────────────────────────────────────────────────────┐");
  Serial.print("│  Current State: ");
  Serial.print(getGameStateName(currentGameState));
  for (int i = 0; i < 38 - strlen(getGameStateName(currentGameState)); i++) Serial.print(" ");
 
  // uint8_t registered = 0, correct = 0, incorrect = 0;
  // for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
  //   if (m0Boards[i].isRegistered) {
  //     registered++;
  //     if (m0Boards[i].isCorrect) correct++;
  //     else incorrect++;
  //   }
  // }
  
  // Serial.print("│  Registered: ");
  // Serial.print(registered);
  // Serial.print("/");
  // Serial.print(NUM_M0_BOARDS);
  // Serial.print(" | Correct: ");
  // Serial.print(correct);
  // Serial.print(" | Incorrect: ");
  // Serial.print(incorrect);

  // int padding = 24 - (registered >= 10 ? 2 : 1) - (correct >= 10 ? 2 : 1) - (incorrect >= 10 ? 2 : 1);
  // for (int i = 0; i < padding; i++) Serial.print(" ");
  // Serial.println("│");
  
  // Serial.print("│  Energy Switch: ");
  // Serial.print(digitalRead(ENERGY_SWITCH_PIN) == HIGH ? "READY" : "PULLED");
  // Serial.print("                              │");
  // Serial.println();
  
  // Serial.println("└────────────────────────────────────────────────────────┘");
}