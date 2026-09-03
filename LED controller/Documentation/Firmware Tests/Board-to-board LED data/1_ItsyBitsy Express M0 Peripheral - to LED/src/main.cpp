/* ItsyBitsy Express LED Strip Test
 * 
 * Simple test program to cycle through colors and patterns on LED strip
 * Uses FastLED library
 * 
 * Hardware:
 * - LED Strip: Data pin connected to Pin 5
 */

#include <Arduino.h>
#include <FastLED.h>

#define LED_PIN 5
#define NUM_LEDS 150  // Adjust this to match your LED strip length
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

CRGB leds[NUM_LEDS];

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Initialize LED strip
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(255);  // Full brightness (0-255)
  FastLED.clear();
  FastLED.show();
}

void loop() {
  // Red
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  FastLED.show();
  delay(1000);
  
  // Green
  fill_solid(leds, NUM_LEDS, CRGB::Green);
  FastLED.show();
  delay(1000);
  
  // Blue
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
  delay(1000);
  
  // White
  fill_solid(leds, NUM_LEDS, CRGB::White);
  FastLED.show();
  delay(1000);
  
  // Rainbow cycle
  static uint8_t hue = 0;
  for(int i = 0; i < 256; i++) {
    fill_rainbow(leds, NUM_LEDS, hue++, 7);
    FastLED.show();
    delay(20);
  }
  
  // Color wipe
  for(int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(hue, 255, 255);
    FastLED.show();
    delay(10);
  }
  hue += 32;
} 