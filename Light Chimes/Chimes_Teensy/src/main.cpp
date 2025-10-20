#include <FastLED.h>
#include <Arduino.h>
#include <Pulse.h>
#include <Timer.h>

const int MOTION_PIN = 10; 

#define NUM_LEDS 6
#define DATA_PIN 11
#define CLOCK_PIN 8
#define LAMP_PIN 9

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

void setup() { 
  Serial.begin(57600);
  Serial.println("resetting");
  FastLED.addLeds<WS2812, DATA_PIN, RGB>(leds, NUM_LEDS);
  pinMode(MOTION_PIN, INPUT_PULLUP); 
  FastLED.setBrightness(50);
  pinMode(9, OUTPUT);
  digitalWrite(9,LOW);
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
      digitalWrite(9,HIGH);
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
      fadeTimer.setTime(100);  //initalize
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
          digitalWrite(9,HIGH);

        }
      }
    }
  }

  // Update LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(0, 0, brightness);
  }
  FastLED.show();
}

