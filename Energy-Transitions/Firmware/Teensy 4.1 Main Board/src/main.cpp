// ─────────────────────────────────────────────────────────────────────────────
// Energy Transitions – Teensy 4.1 Main Board Firmware
// Museum interactive game installation
//
// Responsibilities:
//   - Game state machine (RESET ME IDLE → READY IDLE → GAME ACTIVE → RESULT)
//   - I2C master: polls 10 ItsyBitsy M0 pill boards (slot state + LED commands)
//   - City NeoPixel control (7 chains, 35 LEDs each, FastLED)
//   - USB keyboard emulation for slideshow control (requires -DUSB_SERIAL_HID)
//   - WavTrigger audio playback via Serial1
//   - Energy switch + language toggle button inputs
//   - 2-minute inactivity auto-reset
// ─────────────────────────────────────────────────────────────────────────────

#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>
#include <wavTrigger.h>

// ─────────────────────────────────────────────────────────────────────────────
// Pin Definitions
// ─────────────────────────────────────────────────────────────────────────────
#define PIN_CITY_1          3   // DO_1 → City 1 NeoPixel chain
#define PIN_CITY_2          4   // DO_2 → City 2 NeoPixel chain
#define PIN_CITY_3          5   // DO_3 → City 3 NeoPixel chain
#define PIN_CITY_4          6   // DO_4 → City 4 NeoPixel chain
#define PIN_CITY_5          7   // DO_5 → City 5 NeoPixel chain
#define PIN_CITY_6          8   // DO_6 → City 6 NeoPixel chain
#define PIN_CITY_7          9   // DO_7 → City 7 NeoPixel chain
#define PIN_ENERGY_SWITCH   14  // Active LOW, INPUT_PULLUP
#define PIN_LANG_BUTTON     15  // Active LOW, INPUT_PULLUP
#define PIN_LANG_LED        22  // PWM backlight for language button (via current-limiting resistor)
// I2C: SDA=18, SCL=19 (Wire hardware defaults on Teensy 4.1)
// WavTrigger UART: TX=1, RX=0 (Serial1)

// ─────────────────────────────────────────────────────────────────────────────
// Configuration Constants
// ─────────────────────────────────────────────────────────────────────────────
#define NUM_SLOTS               10
#define NUM_CITIES              7
#define LEDS_PER_CITY           35

#define SLOT_I2C_BASE           0x10    // Slots 0–9 map to addresses 0x10–0x19
#define I2C_CLOCK_HZ            400000

#define INACTIVITY_TIMEOUT_MS   (2UL * 60UL * 1000UL)  // 2 minutes
#define RESULT_DURATION_MS      5000UL
#define RESULT_SOUND_DELAY_MS   1500UL  // Wait for SWITCH.wav before result sound
#define DEBOUNCE_MS             50
#define CITY_FLICKER_HALF_MS    100     // City on/off half-period in GAME ACTIVE
#define CITY_RAINBOW_STEP_MS    20      // Hue advance interval in WIN animation
#define FASTLED_SHOW_INTERVAL   16      // ~60 fps cap for FastLED.show()

// ─────────────────────────────────────────────────────────────────────────────
// I2C LED Commands — sent to each ItsyBitsy pill board (1 byte)
// ─────────────────────────────────────────────────────────────────────────────
#define CMD_OFF             0x00
#define CMD_BREATHE_RED     0x01    // RESET ME IDLE state
#define CMD_BREATHE_WHITE   0x02    // Empty slot in READY / GAME ACTIVE
#define CMD_SOLID_WHITE     0x03    // Piece placed in GAME ACTIVE
#define CMD_SOLID_GREEN     0x04    // Correct placement in RESULT
#define CMD_SOLID_RED       0x05    // Wrong placement in RESULT

// ─────────────────────────────────────────────────────────────────────────────
// WavTrigger Track Numbers
// SD card files must be named: 001_Reset.wav, 002_ReadyState.wav, etc.
// ─────────────────────────────────────────────────────────────────────────────
#define TRACK_RESET             1
#define TRACK_READY_STATE       2
#define TRACK_PIECE_PLACED      3
#define TRACK_SWITCH            4
#define TRACK_FAIL              5
#define TRACK_YELLOW            6
#define TRACK_WIN               7
#define TRACK_ERROR             8

// ─────────────────────────────────────────────────────────────────────────────
// Slot → City Mapping
//
// TODO: Update this table once the physical layout is confirmed.
// Index = slot number (0–9), value = city index (0–6).
// City 6 is treated separately: it lights when ANY slot has a piece.
// ─────────────────────────────────────────────────────────────────────────────
const uint8_t SLOT_CITY_MAP[NUM_SLOTS] = {
    0,  // Slot 0  (Offshore Washington)      → City 0  [PLACEHOLDER]
    0,  // Slot 1  (Offshore Oregon)           → City 0  [PLACEHOLDER]
    1,  // Slot 2  (Grand Coulee Dam, WA)      → City 1  [PLACEHOLDER]
    1,  // Slot 3  (Near Ellensburg, WA)       → City 1  [PLACEHOLDER]
    2,  // Slot 4  (Near Spokane, WA)          → City 2  [PLACEHOLDER]
    2,  // Slot 5  (McNary Dam, OR)            → City 2  [PLACEHOLDER]
    3,  // Slot 6  (Willamette Falls, OR)      → City 3  [PLACEHOLDER]
    3,  // Slot 7  (Near Newberry Volcano, OR) → City 3  [PLACEHOLDER]
    4,  // Slot 8  (Near Lakeview, OR)         → City 4  [PLACEHOLDER]
    5   // Slot 9  (Near Vale, OR)             → City 5  [PLACEHOLDER]
        // City 6 lights when any slot has a piece [PLACEHOLDER]
};

// ─────────────────────────────────────────────────────────────────────────────
// Game State
// ─────────────────────────────────────────────────────────────────────────────
enum GameState : uint8_t {
    STATE_RESET_ME_IDLE = 1,
    STATE_READY_IDLE    = 2,
    STATE_GAME_ACTIVE   = 3,
    STATE_RESULT        = 4
};

GameState currentState = STATE_RESET_ME_IDLE;

// ─────────────────────────────────────────────────────────────────────────────
// FastLED — separate array per city chain
// ─────────────────────────────────────────────────────────────────────────────
CRGB cityLeds[NUM_CITIES][LEDS_PER_CITY];

// ─────────────────────────────────────────────────────────────────────────────
// Slot State (updated each loop by pollSlots)
// ─────────────────────────────────────────────────────────────────────────────
bool slotPresent[NUM_SLOTS]     = {};
bool slotCorrect[NUM_SLOTS]     = {};
bool prevSlotPresent[NUM_SLOTS] = {};

// ─────────────────────────────────────────────────────────────────────────────
// Timing
// ─────────────────────────────────────────────────────────────────────────────
unsigned long lastActivityTime  = 0;
unsigned long resultEntryTime   = 0;

unsigned long lastFlickerTime   = 0;
bool          cityFlickerOn     = false;

unsigned long lastRainbowTime   = 0;
uint8_t       rainbowHue        = 0;

unsigned long lastShowTime      = 0;

// Delayed sound: play a track after a fixed delay (non-blocking)
int           pendingSoundTrack = 0;
unsigned long pendingSoundTime  = 0;

// ─────────────────────────────────────────────────────────────────────────────
// Button Debounce State
// ─────────────────────────────────────────────────────────────────────────────
bool          switchLastRaw         = HIGH;
bool          switchDebouncing      = false;
unsigned long switchDebounceTimer   = 0;

bool          langLastRaw           = HIGH;
bool          langDebouncing        = false;
unsigned long langDebounceTimer     = 0;

// ─────────────────────────────────────────────────────────────────────────────
// WavTrigger
// ─────────────────────────────────────────────────────────────────────────────
wavTrigger wTrig;

// ─────────────────────────────────────────────────────────────────────────────
// Forward Declarations
// ─────────────────────────────────────────────────────────────────────────────
void enterState(GameState newState);
void pollSlots();
void sendSlotCommand(uint8_t slot, uint8_t cmd);
void setCitiesOff();
void setCitiesSolid(CRGB color);
void updateCityFlicker();
void updateCityRainbow();
void showCities();
void playTrack(int track);
void playTrackAfterDelay(int track, unsigned long delayMs);
void updatePendingSound();
void resetActivityTimer();
bool readSwitch();
bool readLangButton();
void updateLangLed();

// ─────────────────────────────────────────────────────────────────────────────
// setup()
// ─────────────────────────────────────────────────────────────────────────────
void setup()
{
    Serial.begin(115200);
    while (!Serial && millis() < 3000) {}

    // City NeoPixel chains (one per pin) — WS2812B via FastLED
    FastLED.addLeds<WS2812B, PIN_CITY_1, GRB>(cityLeds[0], LEDS_PER_CITY);
    FastLED.addLeds<WS2812B, PIN_CITY_2, GRB>(cityLeds[1], LEDS_PER_CITY);
    FastLED.addLeds<WS2812B, PIN_CITY_3, GRB>(cityLeds[2], LEDS_PER_CITY);
    FastLED.addLeds<WS2812B, PIN_CITY_4, GRB>(cityLeds[3], LEDS_PER_CITY);
    FastLED.addLeds<WS2812B, PIN_CITY_5, GRB>(cityLeds[4], LEDS_PER_CITY);
    FastLED.addLeds<WS2812B, PIN_CITY_6, GRB>(cityLeds[5], LEDS_PER_CITY);
    FastLED.addLeds<WS2812B, PIN_CITY_7, GRB>(cityLeds[6], LEDS_PER_CITY);
    FastLED.setBrightness(180);
    setCitiesOff();
    FastLED.show();

    // Input pins
    pinMode(PIN_ENERGY_SWITCH, INPUT_PULLUP);
    pinMode(PIN_LANG_BUTTON,   INPUT_PULLUP);
    pinMode(PIN_LANG_LED,      OUTPUT);
    analogWrite(PIN_LANG_LED,  0);

    // I2C master
    Wire.begin();
    Wire.setClock(I2C_CLOCK_HZ);

    // WavTrigger via Serial1
    wTrig.start();
    delay(10);
    wTrig.stopAllTracks();
    wTrig.masterGain(0);    // 0 dB = unity gain

    lastActivityTime = millis();
    enterState(STATE_RESET_ME_IDLE);

    Serial.println("Energy Transitions Main Board — Ready");
}

// ─────────────────────────────────────────────────────────────────────────────
// loop()
// ─────────────────────────────────────────────────────────────────────────────
void loop()
{
    pollSlots();
    updatePendingSound();
    updateLangLed();

    // Language button: sends space keypress in any state
    if (readLangButton()) {
        Keyboard.press(' ');
        delay(50);
        Keyboard.release(' ');
        resetActivityTimer();
        Serial.println("Lang button → space keypress");
    }

    // Inactivity auto-reset (suppressed during RESULT so 5-second window is uninterrupted)
    if (currentState != STATE_RESULT) {
        if (millis() - lastActivityTime >= INACTIVITY_TIMEOUT_MS) {
            Serial.println("Inactivity timeout → RESET ME IDLE");
            enterState(STATE_RESET_ME_IDLE);
        }
    }

    // ── State machine ─────────────────────────────────────────────────────────
    switch (currentState)
    {
        // ── (1) RESET ME IDLE ──────────────────────────────────────────────────
        case STATE_RESET_ME_IDLE:
        {
            // Transition to READY IDLE once all slots are empty
            bool allEmpty = true;
            for (int i = 0; i < NUM_SLOTS; i++) {
                if (slotPresent[i]) { allEmpty = false; break; }
            }
            if (allEmpty) {
                enterState(STATE_READY_IDLE);
            }
            break;
        }

        // ── (2) READY IDLE ─────────────────────────────────────────────────────
        case STATE_READY_IDLE:
        {
            // Detect first piece placed → transition to GAME ACTIVE
            for (int i = 0; i < NUM_SLOTS; i++) {
                if (slotPresent[i] && !prevSlotPresent[i]) {
                    Serial.print("Slot "); Serial.print(i); Serial.println(" placed — entering GAME ACTIVE");
                    sendSlotCommand(i, CMD_SOLID_WHITE);
                    playTrack(TRACK_PIECE_PLACED);
                    resetActivityTimer();
                    enterState(STATE_GAME_ACTIVE);
                    break;
                }
            }
            // Switch pull in READY IDLE → error sound, no state change
            if (readSwitch()) {
                playTrack(TRACK_ERROR);
                resetActivityTimer();
                Serial.println("Switch in READY IDLE → Error.wav");
            }
            break;
        }

        // ── (3) GAME ACTIVE ────────────────────────────────────────────────────
        case STATE_GAME_ACTIVE:
        {
            // Handle slot changes
            for (int i = 0; i < NUM_SLOTS; i++) {
                if (slotPresent[i] && !prevSlotPresent[i]) {
                    Serial.print("Slot "); Serial.print(i); Serial.println(" piece placed");
                    sendSlotCommand(i, CMD_SOLID_WHITE);
                    playTrack(TRACK_PIECE_PLACED);
                    resetActivityTimer();
                } else if (!slotPresent[i] && prevSlotPresent[i]) {
                    Serial.print("Slot "); Serial.print(i); Serial.println(" piece removed");
                    sendSlotCommand(i, CMD_BREATHE_WHITE);
                    resetActivityTimer();
                }
            }

            // City flicker: cities whose mapped slot(s) have a piece blink slowly
            updateCityFlicker();
            showCities();

            // Energy switch → RESULT
            if (readSwitch()) {
                Serial.println("Switch pulled → RESULT");
                resetActivityTimer();
                playTrack(TRACK_SWITCH);
                enterState(STATE_RESULT);
            }
            break;
        }

        // ── (4) RESULT ─────────────────────────────────────────────────────────
        case STATE_RESULT:
        {
            // Count correct slots (evaluated on entry; just animate here)
            int correctCount = 0;
            for (int i = 0; i < NUM_SLOTS; i++) {
                if (slotPresent[i] && slotCorrect[i]) correctCount++;
            }

            // WIN: animate rainbow across cities
            if (correctCount == 10) {
                updateCityRainbow();
                showCities();
            }

            // Switch pull during RESULT window is ignored (5-second lock-out)

            // After 5 seconds, return to GAME ACTIVE
            if (millis() - resultEntryTime >= RESULT_DURATION_MS) {
                Serial.println("RESULT window ended → GAME ACTIVE");
                enterState(STATE_GAME_ACTIVE);
            }
            break;
        }
    }

    // Update edge-detection baseline for next iteration
    memcpy(prevSlotPresent, slotPresent, sizeof(slotPresent));
}

// ─────────────────────────────────────────────────────────────────────────────
// enterState() — state entry logic
// ─────────────────────────────────────────────────────────────────────────────
void enterState(GameState newState)
{
    currentState = newState;
    Serial.print("→ Entering state "); Serial.println((int)newState);

    switch (newState)
    {
        case STATE_RESET_ME_IDLE:
        {
            Keyboard.press('r');
            delay(50);
            Keyboard.release('r');
            playTrack(TRACK_RESET);
            for (int i = 0; i < NUM_SLOTS; i++) sendSlotCommand(i, CMD_BREATHE_RED);
            setCitiesOff();
            showCities();
            break;
        }

        case STATE_READY_IDLE:
        {
            Keyboard.press('i');
            delay(50);
            Keyboard.release('i');
            playTrack(TRACK_READY_STATE);
            for (int i = 0; i < NUM_SLOTS; i++) sendSlotCommand(i, CMD_BREATHE_WHITE);
            setCitiesOff();
            showCities();
            break;
        }

        case STATE_GAME_ACTIVE:
        {
            // Restore slot LED states from current slot data (used on entry from RESULT)
            for (int i = 0; i < NUM_SLOTS; i++) {
                sendSlotCommand(i, slotPresent[i] ? CMD_SOLID_WHITE : CMD_BREATHE_WHITE);
            }
            // City flicker is driven continuously by the loop; no entry action needed
            break;
        }

        case STATE_RESULT:
        {
            resultEntryTime = millis();

            // Evaluate current slot correctness
            int correctCount = 0;
            for (int i = 0; i < NUM_SLOTS; i++) {
                if (slotPresent[i] && slotCorrect[i]) correctCount++;
            }

            // Set slot ring colors immediately
            for (int i = 0; i < NUM_SLOTS; i++) {
                if (!slotPresent[i]) {
                    sendSlotCommand(i, CMD_BREATHE_WHITE);
                } else if (slotCorrect[i]) {
                    sendSlotCommand(i, CMD_SOLID_GREEN);
                } else {
                    sendSlotCommand(i, CMD_SOLID_RED);
                }
            }

            // Set city colors and queue result sound after SWITCH.wav plays
            if (correctCount == 10) {
                // Case C: WIN — rainbow is animated in the loop; clear to black first
                setCitiesOff();
                showCities();
                playTrackAfterDelay(TRACK_WIN, RESULT_SOUND_DELAY_MS);
                Serial.println("RESULT: WIN (10/10)");
            } else if (correctCount > 0) {
                // Case B: some correct
                setCitiesSolid(CRGB::Yellow);
                showCities();
                playTrackAfterDelay(TRACK_YELLOW, RESULT_SOUND_DELAY_MS);
                Serial.print("RESULT: PARTIAL ("); Serial.print(correctCount); Serial.println("/10)");
            } else {
                // Case A: none correct
                setCitiesSolid(CRGB::Red);
                showCities();
                playTrackAfterDelay(TRACK_FAIL, RESULT_SOUND_DELAY_MS);
                Serial.println("RESULT: FAIL (0/10)");
            }
            break;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// I2C: Poll all 10 pill boards
// Each slave returns 2 bytes: [piecePresent, isCorrect]
// If a slave doesn't respond, treat it as empty.
// ─────────────────────────────────────────────────────────────────────────────
void pollSlots()
{
    for (uint8_t i = 0; i < NUM_SLOTS; i++) {
        uint8_t addr      = SLOT_I2C_BASE + i;
        uint8_t bytesRead = Wire.requestFrom(addr, (uint8_t)2);

        if (bytesRead == 2) {
            uint8_t present = Wire.read();
            uint8_t correct = Wire.read();
            slotPresent[i]  = (present == 0x01);
            slotCorrect[i]  = slotPresent[i] && (correct == 0x01);
        } else {
            slotPresent[i] = false;
            slotCorrect[i] = false;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// I2C: Send a 1-byte LED command to one pill board
// ─────────────────────────────────────────────────────────────────────────────
void sendSlotCommand(uint8_t slot, uint8_t cmd)
{
    Wire.beginTransmission(SLOT_I2C_BASE + slot);
    Wire.write(cmd);
    Wire.endTransmission();
}

// ─────────────────────────────────────────────────────────────────────────────
// City LED Helpers
// ─────────────────────────────────────────────────────────────────────────────
void setCitiesOff()
{
    for (int c = 0; c < NUM_CITIES; c++)
        fill_solid(cityLeds[c], LEDS_PER_CITY, CRGB::Black);
}

void setCitiesSolid(CRGB color)
{
    for (int c = 0; c < NUM_CITIES; c++)
        fill_solid(cityLeds[c], LEDS_PER_CITY, color);
}

// Called each frame in GAME ACTIVE.
// Cities whose mapped slot(s) contain a piece flicker white.
// City 6 flickers if ANY slot has a piece (placeholder — update with SLOT_CITY_MAP).
void updateCityFlicker()
{
    bool cityHasPiece[NUM_CITIES] = {};
    bool anyPiece = false;

    for (int i = 0; i < NUM_SLOTS; i++) {
        if (slotPresent[i]) {
            cityHasPiece[SLOT_CITY_MAP[i]] = true;
            anyPiece = true;
        }
    }
    // TODO: Replace city 6 placeholder once final slot→city mapping is confirmed
    cityHasPiece[6] = anyPiece;

    if (millis() - lastFlickerTime >= CITY_FLICKER_HALF_MS) {
        lastFlickerTime = millis();
        cityFlickerOn   = !cityFlickerOn;
    }

    for (int c = 0; c < NUM_CITIES; c++) {
        CRGB color = (cityHasPiece[c] && cityFlickerOn) ? CRGB(200, 200, 200) : CRGB::Black;
        fill_solid(cityLeds[c], LEDS_PER_CITY, color);
    }
}

// Called each frame in RESULT WIN case — scrolling rainbow across all cities.
void updateCityRainbow()
{
    if (millis() - lastRainbowTime >= CITY_RAINBOW_STEP_MS) {
        lastRainbowTime = millis();
        rainbowHue++;
    }
    for (int c = 0; c < NUM_CITIES; c++) {
        for (int j = 0; j < LEDS_PER_CITY; j++) {
            cityLeds[c][j] = CHSV(rainbowHue + (uint8_t)(j * 5) + (uint8_t)(c * 20), 255, 200);
        }
    }
}

// Rate-limited FastLED.show() — caps at ~60 fps to avoid blocking the loop.
void showCities()
{
    if (millis() - lastShowTime >= FASTLED_SHOW_INTERVAL) {
        lastShowTime = millis();
        FastLED.show();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// WavTrigger Helpers
// ─────────────────────────────────────────────────────────────────────────────

// Play a track immediately, stopping any current playback.
void playTrack(int track)
{
    wTrig.trackPlaySolo(track);
}

// Queue a track to play after a delay (non-blocking).
// Used so SWITCH.wav can finish before the result sound starts.
void playTrackAfterDelay(int track, unsigned long delayMs)
{
    pendingSoundTrack = track;
    pendingSoundTime  = millis() + delayMs;
}

// Must be called each loop iteration to fire the pending sound on time.
void updatePendingSound()
{
    if (pendingSoundTrack > 0 && millis() >= pendingSoundTime) {
        wTrig.trackPlaySolo(pendingSoundTrack);
        pendingSoundTrack = 0;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Activity Timer
// ─────────────────────────────────────────────────────────────────────────────
void resetActivityTimer()
{
    lastActivityTime = millis();
}

// ─────────────────────────────────────────────────────────────────────────────
// Button Edge Detection (falling edge, debounced)
// Returns true once per press.
// ─────────────────────────────────────────────────────────────────────────────
bool readSwitch()
{
    bool raw = digitalRead(PIN_ENERGY_SWITCH);

    if (!switchDebouncing && raw == LOW && switchLastRaw == HIGH) {
        switchDebouncing    = true;
        switchDebounceTimer = millis();
    }

    if (switchDebouncing && (millis() - switchDebounceTimer >= DEBOUNCE_MS)) {
        switchDebouncing = false;
        bool confirmed = (digitalRead(PIN_ENERGY_SWITCH) == LOW);
        switchLastRaw  = HIGH;  // Reset baseline; wait for release
        if (confirmed) return true;
    }

    if (raw == HIGH) switchLastRaw = HIGH;
    return false;
}

// Breathes the language button backlight continuously to indicate it is always interactive.
// Sine wave: ~2-second period, brightness range 15–210.
void updateLangLed()
{
    float phase      = (float)(millis() % 2000) / 2000.0f * TWO_PI;
    uint8_t brightness = 15 + (uint8_t)((sinf(phase) * 0.5f + 0.5f) * 195.0f);
    analogWrite(PIN_LANG_LED, brightness);
}

bool readLangButton()
{
    bool raw = digitalRead(PIN_LANG_BUTTON);

    if (!langDebouncing && raw == LOW && langLastRaw == HIGH) {
        langDebouncing    = true;
        langDebounceTimer = millis();
    }

    if (langDebouncing && (millis() - langDebounceTimer >= DEBOUNCE_MS)) {
        langDebouncing = false;
        bool confirmed = (digitalRead(PIN_LANG_BUTTON) == LOW);
        langLastRaw    = HIGH;
        if (confirmed) return true;
    }

    if (raw == HIGH) langLastRaw = HIGH;
    return false;
}
