#include <Arduino.h>
#include <FastLED.h>

// City Lights Test - Teensy LED Output
// Outputs red color to 5 RGB LED strips on pins 3-7

#define NUM_LEDS_PER_STRIP 5  
#define NUM_CITIES 7
#define BRIGHTNESS 128         // 0-255
#define LED_TYPE WS2812B       // Change if using different LED type (WS2811, APA102, etc.)
#define COLOR_ORDER GRB        // Change if needed (RGB, GRB, BRG, etc.)

// Define LED arrays for each strip
CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];
CRGB leds3[NUM_LEDS_PER_STRIP];
CRGB leds4[NUM_LEDS_PER_STRIP];
CRGB leds5[NUM_LEDS_PER_STRIP];
CRGB leds6[NUM_LEDS_PER_STRIP];
CRGB leds7[NUM_LEDS_PER_STRIP];

void setup() 
{
  Serial.begin(115200);
  delay(100);
  
  Serial.println("=== City Lights Test - Teensy LED Output ===");
  Serial.println("Initializing FastLED...");
  
  // Initialize FastLED for each strip on pins 3-7
  FastLED.addLeds<LED_TYPE, 3, COLOR_ORDER>(leds1, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 4, COLOR_ORDER>(leds2, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 5, COLOR_ORDER>(leds3, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 6, COLOR_ORDER>(leds4, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 7, COLOR_ORDER>(leds5, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 8, COLOR_ORDER>(leds6, NUM_LEDS_PER_STRIP);
  FastLED.addLeds<LED_TYPE, 9, COLOR_ORDER>(leds7, NUM_LEDS_PER_STRIP);

  
  // Set power limit: 5V at 2A (2000mA)
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 2000);
  
  // Set global brightness
  FastLED.setBrightness(BRIGHTNESS);
  
  // Set all LEDs to red
  fill_solid(leds1, NUM_LEDS_PER_STRIP, CRGB::Red);
  fill_solid(leds2, NUM_LEDS_PER_STRIP, CRGB::Red);
  fill_solid(leds3, NUM_LEDS_PER_STRIP, CRGB::Red);
  fill_solid(leds4, NUM_LEDS_PER_STRIP, CRGB::Red);
  fill_solid(leds5, NUM_LEDS_PER_STRIP, CRGB::Red);
  fill_solid(leds6, NUM_LEDS_PER_STRIP, CRGB::Red);
  fill_solid(leds7, NUM_LEDS_PER_STRIP, CRGB::Red);

  // Update the LEDs
  FastLED.show();
}

void loop() 
{
  // LEDs remain red - nothing in loop
}
