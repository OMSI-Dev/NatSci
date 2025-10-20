#include <FastLED.h>
#include <Arduino.h>
#include <Timer.h> 
#include "Adafruit_Pixie.h"
#include "SoftwareSerial.h"

const int MOTION_PIN = 10; 

#define NUM_LEDS 6
#define NEOPIXEL_PIN 11 

#define PIXIEPIN  6 
#define NUMPIXELS 1 

// fading and delays
MoToTimerRop delayTimer;
MoToTimerRop fadeTimer;
bool waiting = false;
bool delayExpired = false;

CRGB leds[NUM_LEDS];

uint8_t brightness = 0; 
uint8_t increment = 1;
uint8_t maxVal = 155;
uint8_t minVal = 0;

SoftwareSerial pixieSerial(-1, PIXIEPIN);
Adafruit_Pixie strip = Adafruit_Pixie(NUMPIXELS, &pixieSerial);


void setup() { 
  Serial.println("Ready to Pixie!");
  pixieSerial.begin(115200); // pixie baud rate requirement, leave here 
  strip.setBrightness(100);  //adjust to avoid blinding

  Serial.begin(57600);
  FastLED.addLeds<WS2812, NEOPIXEL_PIN, RGB>(leds, NUM_LEDS);
  pinMode(MOTION_PIN, INPUT_PULLUP); 
  FastLED.setBrightness(50);
}

void loop() {
  bool motion = (digitalRead(MOTION_PIN) == LOW);

  if (motion) {
    Serial.println("Motion detected!");

    // Increase brightness
    if (brightness + increment < maxVal) {
      brightness += increment;
    } else {
      brightness = maxVal;
    }

    // Reset timers
    delayTimer.setTime(2500);  
    waiting = false;
    delayExpired = false;
  } 
  else {
    if (!waiting) {
      waiting = true;
      delayExpired = false;
      delayTimer.setTime(2500);  
      Serial.println("No motion: timer started.");
    }

    if (!delayExpired && delayTimer.expired()) {
      delayExpired = true;
      fadeTimer.setTime(100); //first init
      Serial.println("delay expired: starting fade...");
    }

    if (delayExpired) {
      if (fadeTimer.expired()) {  
        if (brightness > minVal + increment) {
          Serial.println("decreasing brightness...");
          brightness -= increment;
          fadeTimer.setTime(10);  // speed of fade-out
        } else if (brightness != minVal) {
          Serial.println("setting brightness to minVal");
          brightness = minVal;
        }
      }
    }
  }

  // Update ws812 LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(0, 0, brightness);
  }

  // Update pixie LEDs
 for (int i = 0; i < NUMPIXELS; i++) {
  strip.setPixelColor(0, 0, 0, brightness);
  }

  FastLED.show();
  strip.show();
}

