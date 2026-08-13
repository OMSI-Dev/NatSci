/*
 * HALL EFFECT SENSOR - ItsyBitsy M0 Express (SIMPLIFIED)
 * 
 * Reads three Hall effect sensors to detect magnetic game pieces.
 * Simple state machine: IDLE → REGISTERING → CORRECT/INCORRECT
 * 
 * SENSOR LAYOUT:
 *   Physical PCB: S2 — S1 — S3
 *   Array index:  [1] [0] [2]
 * 
 * ADC THRESHOLDS (12-bit):
 *   SOUTH: < 1700
 *   NORTH: > 2400
 *   UNCERTAIN: Between
 * 
 * LED FEEDBACK:
 *   IDLE        → Off
 *   REGISTERING → White chase
 *   CORRECT     → Green
 *   INCORRECT   → Red
 * 
 * I2C TX (4 bytes):
 *   [0] State (0=IDLE, 1=REGISTERING, 2=CORRECT, 3=INCORRECT)
 *   [1] S1 polarity (0=UNCERTAIN, 1=SOUTH, 2=NORTH)
 *   [2] S2 polarity
 *   [3] S3 polarity
 */

#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>
#include <i2C_Address.h>

// Pins
#define SENSOR_1_PIN A0
#define SENSOR_2_PIN A1
#define SENSOR_3_PIN A2
#define SEN1_LED_PIN 11
#define SEN2_LED_PIN 10
#define SEN3_LED_PIN 9
#define LED_PIN 2
#define NUM_LEDS 20

// ADC
#define ADC_SAMPLES 5
#define THRESHOLD_SOUTH 1700
#define THRESHOLD_NORTH 2400

// Registration
#define CONFIRM_SAMPLES 8  // Consecutive stable readings to lock

CRGB leds[NUM_LEDS];

enum Polarity : uint8_t { POL_UNCERTAIN = 0, POL_SOUTH = 1, POL_NORTH = 2 };
enum State : uint8_t { STATE_IDLE = 0, STATE_REGISTERING = 1, STATE_CORRECT = 2, STATE_INCORRECT = 3 };

struct Sensor {
  Polarity confirmed;
  Polarity current;
  uint8_t confirmCount;
  bool locked;
};

uint16_t i2cAddress = 0x08;
State state = STATE_IDLE;
Sensor sensors[3];
volatile uint8_t txBuf[4] = {0, 0, 0, 0};

// Read sensor with averaging
uint16_t readSensor(uint8_t pin) {
  uint32_t sum = 0;
  for (uint8_t i = 0; i < ADC_SAMPLES; i++) {
    sum += analogRead(pin);
    delayMicroseconds(50);
  }
  return sum / ADC_SAMPLES;
}

// Classify sensor reading
Polarity classify(uint16_t raw) {
  if (raw < THRESHOLD_SOUTH) return POL_SOUTH;
  if (raw > THRESHOLD_NORTH) return POL_NORTH;
  return POL_UNCERTAIN;
}

// Reset sensors
void resetSensors() {
  for (uint8_t i = 0; i < 3; i++) {
    sensors[i] = {POL_UNCERTAIN, POL_UNCERTAIN, 0, false};
  }
}

// White chase animation
void whiteChase() {
  static uint8_t pos = 0;
  static uint32_t lastMs = 0;
  if (millis() - lastMs > 40) {
    fadeToBlackBy(leds, NUM_LEDS, 48);
    leds[pos] = CRGB(200, 200, 200);
    leds[(pos + NUM_LEDS - 1) % NUM_LEDS] = CRGB(100, 100, 100);
    FastLED.show();
    pos = (pos + 1) % NUM_LEDS;
    lastMs = millis();
  }
}

// Set solid color
void setLEDs(CRGB color) {
  fill_solid(leds, NUM_LEDS, color);
  FastLED.show();
}

// Update I2C buffer
void updateTxBuf() {
  noInterrupts();
  txBuf[0] = (uint8_t)state;
  txBuf[1] = (uint8_t)sensors[0].confirmed;
  txBuf[2] = (uint8_t)sensors[1].confirmed;
  txBuf[3] = (uint8_t)sensors[2].confirmed;
  interrupts();
}

// I2C request handler
void onRequest() {
  Wire.write((uint8_t*)txBuf, 4);
}

// Check if pattern matches expected for this address
bool isCorrect() {
  Polarity p0 = sensors[0].confirmed; // S1 (middle)
  Polarity p1 = sensors[1].confirmed; // S2 (left)
  Polarity p2 = sensors[2].confirmed; // S3 (right)

  bool isBuoy = (p0 == POL_SOUTH && p1 == POL_SOUTH && p2 == POL_SOUTH);
  bool isDam = (p0 == POL_NORTH && p1 == POL_NORTH && p2 == POL_NORTH);
  bool isGeo = (p0 == POL_SOUTH && ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) || (p1 == POL_UNCERTAIN && p2 == POL_NORTH)));
  bool isSolar = (p0 == POL_UNCERTAIN && ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) || (p1 == POL_UNCERTAIN && p2 == POL_NORTH)));
  bool isWind = (p0 == POL_NORTH && ((p1 == POL_NORTH && p2 == POL_UNCERTAIN) || (p1 == POL_UNCERTAIN && p2 == POL_NORTH)));

  switch (i2cAddress) {
    case 0x08: case 0x0C: return (isBuoy || isWind);
    case 0x09: case 0x0D: case 0x10: return (isDam || isWind || isSolar);
    case 0x0A: case 0x0E: case 0x0F: case 0x11: return (isGeo || isWind || isSolar);
    case 0x0B: return (isSolar || isWind);
    default: return false;
  }
}

// Update sensor LED diagnostics
void updateSensorLEDs() {
  const uint8_t LED_PINS[] = {SEN1_LED_PIN, SEN2_LED_PIN, SEN3_LED_PIN};
  for (uint8_t i = 0; i < 3; i++) {
    if (sensors[i].current == POL_UNCERTAIN) {
      digitalWrite(LED_PINS[i], LOW);
    } else if (sensors[i].current == POL_SOUTH) {
      digitalWrite(LED_PINS[i], (millis() / 500) % 2 ? HIGH : LOW);  // Slow blink
    } else {
      digitalWrite(LED_PINS[i], (millis() / 200) % 2 ? HIGH : LOW);  // Fast blink
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Configure pins
  pinMode(SEN1_LED_PIN, OUTPUT);
  pinMode(SEN2_LED_PIN, OUTPUT);
  pinMode(SEN3_LED_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  
  // Configure ADC
  analogReadResolution(12);
  delay(100);
  
  // Initialize LEDs
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 500);
  setLEDs(CRGB::Black);
  
  // Initialize sensors
  resetSensors();
  updateTxBuf();
  
  // Read I2C address from hardware pins
  setPins();
  i2cAddress = setAddr();
  
  // Start I2C
  Wire.begin(i2cAddress);
  Wire.onRequest(onRequest);
  
  Serial.println("\n=== HALL SENSOR BOARD INITIALIZED ===");
  Serial.print("I2C Address: 0x");
  Serial.println(i2cAddress, HEX);
  Serial.print("Type: ");
  printI2Caddress();
  Serial.println("======================================\n");
}

void loop() {
  const uint8_t PINS[] = {SENSOR_1_PIN, SENSOR_2_PIN, SENSOR_3_PIN};
  
  // Read all sensors
  for (uint8_t i = 0; i < 3; i++) {
    uint16_t raw = readSensor(PINS[i]);
    sensors[i].current = classify(raw);
  }
  
  // Update sensor LEDs
  updateSensorLEDs();
  
  // Check if all uncertain
  bool allUncertain = (sensors[0].current == POL_UNCERTAIN && 
                       sensors[1].current == POL_UNCERTAIN && 
                       sensors[2].current == POL_UNCERTAIN);
  
  // State machine
  switch (state) {
    
    case STATE_IDLE:
      setLEDs(CRGB::Black);
      if (!allUncertain) {
        resetSensors();
        state = STATE_REGISTERING;
        Serial.println("\n>>> REGISTERING <<<");
      }
      break;
    
    case STATE_REGISTERING: {
      whiteChase();
      
      if (allUncertain) {
        // Magnet removed
        state = STATE_IDLE;
        Serial.println(">>> BACK TO IDLE <<<");
        break;
      }
      
      // Check each sensor
      bool allLocked = true;
      for (uint8_t i = 0; i < 3; i++) {
        if (sensors[i].locked) continue;
        
        if (sensors[i].current == sensors[i].confirmed) {
          sensors[i].confirmCount++;
          if (sensors[i].confirmCount >= CONFIRM_SAMPLES) {
            sensors[i].locked = true;
            Serial.print("Sensor ");
            Serial.print(i + 1);
            Serial.println(" LOCKED");
          } else {
            allLocked = false;
          }
        } else {
          sensors[i].confirmed = sensors[i].current;
          sensors[i].confirmCount = 1;
          allLocked = false;
        }
      }
      
      // All locked?
      if (allLocked) {
        bool correct = isCorrect();
        state = correct ? STATE_CORRECT : STATE_INCORRECT;
        Serial.print(">>> ");
        Serial.print(correct ? "CORRECT" : "INCORRECT");
        Serial.println(" <<<");
        Serial.print("Pattern: S2=");
        Serial.print(sensors[1].confirmed);
        Serial.print(" S1=");
        Serial.print(sensors[0].confirmed);
        Serial.print(" S3=");
        Serial.println(sensors[2].confirmed);
      }
      break;
    }
    
    case STATE_CORRECT:
      setLEDs(CRGB(0, 200, 0));  // Green
      if (allUncertain) {
        state = STATE_IDLE;
        Serial.println(">>> REMOVED - BACK TO IDLE <<<\n");
      }
      break;
    
    case STATE_INCORRECT:
      setLEDs(CRGB(200, 0, 0));  // Red
      if (allUncertain) {
        state = STATE_IDLE;
        Serial.println(">>> REMOVED - BACK TO IDLE <<<\n");
      }
      break;
  }
  
  // Update I2C buffer
  updateTxBuf();
  
  delay(10);
}
