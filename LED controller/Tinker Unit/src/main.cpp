/*
  LED strip test with Trinker M0 connected to the Teensy with the OLED_buttons_test pinout
*/

#include <Adafruit_NeoPixel.h>

// LED setup
#define LED_PIN 4
#define NUM_LEDS 6  // Change if using a strip
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);
  
  // Initialize LED strip
  strip.begin();
  strip.show();  // Turn off all LEDs
  
  Serial.println("Trinket M0 LED Test Started");
}

void loop() {
  // Red - all LEDs on
  Serial.println("RED");
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(255, 0, 0));
  }
  strip.show();
  delay(1000);
  
  // Green - all LEDs on
  Serial.println("GREEN");
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(0, 255, 0));
  }
  strip.show();
  delay(1000);
  
  // Blue - all LEDs on
  Serial.println("BLUE");
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(0, 0, 255));
  }
  strip.show();
  delay(1000);
  
  // White - all LEDs on
  Serial.println("WHITE");
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(255, 255, 255));
  }
  strip.show();
  delay(1000);
  
  // Off
  Serial.println("OFF");
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(0, 0, 0));
  }
  strip.show();
  delay(1000);
}
