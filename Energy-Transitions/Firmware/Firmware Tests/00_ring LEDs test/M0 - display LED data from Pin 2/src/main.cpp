#include <Arduino.h>
#include <FastLED.h>

// LED Chain Configuration
const int LED_PIN = 2;        // Data pin for LED chain
const int NUM_LEDS = 20;      // Number of LEDs in the chain

// Define the array of LEDs
CRGB leds[NUM_LEDS];

void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("=== LED Chain Test ===");
  Serial.print("Number of LEDs: ");
  Serial.println(NUM_LEDS);
  Serial.print("Data Pin: ");
  Serial.println(LED_PIN);
  
  // Initialize FastLED
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(50);  // Brightness level (0-255)
  FastLED.clear();
  FastLED.show();
  delay(100);  // Give LEDs time to initialize
  
  // Turn on all LEDs to white
  Serial.println("Turning on all LEDs...");
  for(int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::White;
  }
  FastLED.show();
  
  Serial.println("All LEDs turned ON!");
}

void loop() {
  // LEDs stay on - nothing to do in loop
}
