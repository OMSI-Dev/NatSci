/*
 * HALL EFFECT SENSOR POLARITY TEST - ItsyBitsy M0 Express
 * Firmware Test 2: Read Magnet Polarities and Display on LEDs
 * 
 * Simplified test to read three SS39ET Hall effect sensors and display
 * their polarity using both indicator LEDs and the LED ring.
 * 
 * SENSOR CONFIGURATION:
 *   Physical PCB layout (left to right): S2 — S1 — S3
 *   Sensor pins: S1=A0, S2=A1, S3=A2
 *   Indicator LEDs: S1=pin 11, S2=pin 10, S3=pin 9
 *
 * ADC THRESHOLDS (12-bit, 3.3V ref, adjusted for milkplex barrier):
 *   SOUTH:     < 1650 mV (enter) / < 1750 mV (stay)
 *   NORTH:     > 2450 mV (enter) / > 2350 mV (stay)
 *   UNCERTAIN: Between thresholds
 *   Hysteresis prevents boundary oscillation during transitions.
 *
 * LED DISPLAY:
 *   Indicator LEDs (green):
 *     OFF = UNCERTAIN
 *     ON  = definite polarity detected (SOUTH or NORTH)
 *   
 *   Ring LEDs (20 LEDs divided into 3 segments):
 *     Segment 1 (LEDs 0-6):   Sensor 1 (S1)
 *     Segment 2 (LEDs 7-13):  Sensor 2 (S2)
 *     Segment 3 (LEDs 14-19): Sensor 3 (S3)
 *     Colors: RED = SOUTH, BLUE = NORTH, DIM WHITE = UNCERTAIN
 *
 * Version: 1.0 (2026-08-04)
 * Updated from working main.cpp with latest ADC and classification code
 */

#include <Arduino.h>
#include <FastLED.h>

// ── Sensor pins ───────────────────────────────────────────────────────────────
#define SENSOR_1_PIN  A0
#define SENSOR_2_PIN  A1
#define SENSOR_3_PIN  A2

// ── Sensor indicator LED pins ─────────────────────────────────────────────────
#define SEN1_LED_PIN  11
#define SEN2_LED_PIN  10
#define SEN3_LED_PIN  9

// ── DotStar pins (ItsyBitsy M0) ───────────────────────────────────────────────
#define DOTSTAR_DATA  41
#define DOTSTAR_CLK   40

// ── ADC Configuration ─────────────────────────────────────────────────────────
#define ADC_SAMPLES      5     // Number of ADC readings to average per sensor

// ── ADC Thresholds (12-bit, adjusted for milkplex barrier) ────────────────────
#define THRESHOLD_SOUTH_LOW   1650  // Below this = definitely SOUTH
#define THRESHOLD_SOUTH_HIGH  1750  // Above this = leaving SOUTH
#define THRESHOLD_NORTH_LOW   2350  // Below this = leaving NORTH  
#define THRESHOLD_NORTH_HIGH  2450  // Above this = definitely NORTH

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

// ── Globals ───────────────────────────────────────────────────────────────────
Polarity lastReading[3] = { POL_UNCERTAIN, POL_UNCERTAIN, POL_UNCERTAIN };

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
 * Update LED ring to display sensor polarities
 * Segment 1 (0-6): S1, Segment 2 (7-13): S2, Segment 3 (14-19): S3
 */
void updateRingLEDs(Polarity pol[3]) {
  // Sensor segments in ring: [S1: 0-6] [S2: 7-13] [S3: 14-19]
  const uint8_t segmentStarts[3] = {0, 7, 14};
  const uint8_t segmentSizes[3] = {7, 7, 6};
  
  for (uint8_t sensor = 0; sensor < 3; sensor++) {
    CRGB color;
    
    switch (pol[sensor]) {
      case POL_SOUTH:
        color = CRGB::Red;      // RED = SOUTH
        break;
      case POL_NORTH:
        color = CRGB::Blue;     // BLUE = NORTH
        break;
      case POL_UNCERTAIN:
      default:
        color = CRGB(30, 30, 30);  // DIM WHITE = UNCERTAIN
        break;
    }
    
    // Fill segment
    for (uint8_t i = 0; i < segmentSizes[sensor]; i++) {
      leds[segmentStarts[sensor] + i] = color;
    }
  }
  
  FastLED.show();
}

/**
 * Update indicator LEDs to show which sensors have definite readings
 */
void updateIndicatorLEDs(Polarity pol[3]) {
  // S1 on pin 11, S2 on pin 10, S3 on pin 9
  digitalWrite(SEN1_LED_PIN, (pol[0] != POL_UNCERTAIN) ? HIGH : LOW);
  digitalWrite(SEN2_LED_PIN, (pol[1] != POL_UNCERTAIN) ? HIGH : LOW);
  digitalWrite(SEN3_LED_PIN, (pol[2] != POL_UNCERTAIN) ? HIGH : LOW);
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial && millis() < 3000);  // Wait up to 3s for serial
  
  // Disable on-board LEDs to prevent interference
  turnOffDotStar();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  
  // Configure ADC for 12-bit resolution (0-4095)
  analogReadResolution(12);
  
  // Allow ADC to stabilize after resolution change
  delay(100);

  // Initialize sensor indicator LED pins
  pinMode(SEN1_LED_PIN, OUTPUT);
  pinMode(SEN2_LED_PIN, OUTPUT);
  pinMode(SEN3_LED_PIN, OUTPUT);
  digitalWrite(SEN1_LED_PIN, LOW);
  digitalWrite(SEN2_LED_PIN, LOW);
  digitalWrite(SEN3_LED_PIN, LOW);

  // Initialize external LED ring
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 750);
  FastLED.setBrightness(75);
  fill_solid(leds, NUM_LEDS, CRGB(30, 30, 30));  // Start with dim white
  FastLED.show();
  
  // Print startup information
  Serial.println("\n=== HALL EFFECT SENSOR POLARITY TEST ===");
  Serial.println("Firmware Test 2: Read and Display Magnet Data");
  Serial.println();
  Serial.println("SENSOR LAYOUT (Physical L→R): S2 — S1 — S3");
  Serial.println("SENSOR PINS: S1=A0, S2=A1, S3=A2");
  Serial.println("INDICATOR LEDS: S1=pin11, S2=pin10, S3=pin9");
  Serial.println();
  Serial.println("THRESHOLDS:");
  Serial.print("  SOUTH: < ");
  Serial.print(THRESHOLD_SOUTH_LOW);
  Serial.print(" (enter) / < ");
  Serial.print(THRESHOLD_SOUTH_HIGH);
  Serial.println(" (stay)");
  Serial.print("  NORTH: > ");
  Serial.print(THRESHOLD_NORTH_HIGH);
  Serial.print(" (enter) / > ");
  Serial.print(THRESHOLD_NORTH_LOW);
  Serial.println(" (stay)");
  Serial.println();
  Serial.println("LED COLORS:");
  Serial.println("  RED = SOUTH pole");
  Serial.println("  BLUE = NORTH pole");
  Serial.println("  DIM WHITE = UNCERTAIN");
  Serial.println();
  Serial.println("INDICATOR LED: ON = definite reading, OFF = uncertain");
  Serial.println("==========================================\n");
  
  // Perform dummy reads to prime the ADC and clear any startup transients
  Serial.println("Initializing sensors...");
  for (uint8_t warmup = 0; warmup < 10; warmup++) {
    analogRead(SENSOR_1_PIN);
    analogRead(SENSOR_2_PIN);
    analogRead(SENSOR_3_PIN);
    delay(10);
  }
  
  // Read and display initial baseline values (should be ~2048 with no magnet)
  Serial.println("Baseline readings (no magnet present):");
  uint16_t baseline[3];
  baseline[0] = readSensorAveraged(SENSOR_1_PIN);
  baseline[1] = readSensorAveraged(SENSOR_2_PIN);
  baseline[2] = readSensorAveraged(SENSOR_3_PIN);
  
  Serial.println("       S2      S1      S3    (physical L→R)");
  Serial.print("RAW:   ");
  Serial.print(baseline[1]);  Serial.print("\t");
  Serial.print(baseline[0]);  Serial.print("\t");
  Serial.println(baseline[2]);
  Serial.println("Expected: ~2048 for each sensor (mid-range = UNCERTAIN)");
  Serial.println();
  
  // Check if any baseline readings are out of expected range
  bool baselineWarning = false;
  for (uint8_t i = 0; i < 3; i++) {
    if (baseline[i] < 1900 || baseline[i] > 2200) {
      baselineWarning = true;
      break;
    }
  }
  
  if (baselineWarning) {
    Serial.println("WARNING: Baseline readings outside expected range!");
    Serial.println("Check sensor connections or allow more warm-up time.");
    Serial.println();
  } else {
    Serial.println("Baseline readings OK - sensors ready!");
    Serial.println();
  }
  
  Serial.println("Starting continuous monitoring...\n");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  static const uint8_t PINS[3] = { SENSOR_1_PIN, SENSOR_2_PIN, SENSOR_3_PIN };
  static uint32_t lastPrint = 0;
  static const char* POL_NAMES[] = { "  X  ", "  S  ", "  N  " };

  // Read all sensors with averaging and hysteresis
  Polarity current[3];
  uint16_t raw[3];
  
  for (uint8_t i = 0; i < 3; i++) {
    raw[i] = readSensorAveraged(PINS[i]);
    current[i] = classifyWithHysteresis(raw[i], lastReading[i]);
    lastReading[i] = current[i];  // Update for next iteration
  }

  // Update LEDs
  updateRingLEDs(current);
  updateIndicatorLEDs(current);

  // Print status every 500ms
  if (millis() - lastPrint > 500) {
    Serial.println("       S2      S1      S3    (physical L→R)");
    Serial.print("RAW:   ");
    Serial.print(raw[1]);  Serial.print("\t");
    Serial.print(raw[0]);  Serial.print("\t");
    Serial.println(raw[2]);
    
    Serial.print("POL:  ");
    Serial.print(POL_NAMES[current[1]]);  Serial.print("   ");
    Serial.print(POL_NAMES[current[0]]);  Serial.print("   ");
    Serial.println(POL_NAMES[current[2]]);
    Serial.println();
    
    lastPrint = millis();
  }

  delay(50);  // Short delay for stability
}
