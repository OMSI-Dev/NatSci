/*
Autumn 8/4/26 Added simple digitalwrite for three sensor LEDs to turn on
*/

#include <Arduino.h>
#include <FastLED.h>

// LED Chain Configuration
const int LED_PIN = 2;        // Data pin for LED chain
const int NUM_LEDS = 20;      // Number of LEDs in the chain
CRGB leds[NUM_LEDS];

// Sensor LED pins - standard green LEDs
const int SEN1_LED_PIN = 11;
const int SEN2_LED_PIN = 10;
const int SEN3_LED_PIN = 9;

void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("=== LED Chain Test ===");
  Serial.print("Number of LEDs: ");
  Serial.println(NUM_LEDS);
  Serial.print("Data Pin: ");
  Serial.println(LED_PIN);
  
  // Initialize FastLED for main LED chain
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(50);
  
  // Initialize sensor LED pins as outputs
  pinMode(SEN1_LED_PIN, OUTPUT);
  pinMode(SEN2_LED_PIN, OUTPUT);
  pinMode(SEN3_LED_PIN, OUTPUT);
  
  // Turn on all LEDs
  Serial.println("Turning on all LEDs...");
  for(int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::White;
  }
  FastLED.show();
  
  // Turn on sensor LEDs
  digitalWrite(SEN1_LED_PIN, HIGH);
  digitalWrite(SEN2_LED_PIN, HIGH);
  digitalWrite(SEN3_LED_PIN, HIGH);
  
  Serial.println("All LEDs turned ON!");
}

void loop() {
  // Nothing to do - LEDs stay on
}