

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <EEPROM.h>

   
const int buttonPin = 2;

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  Serial.begin(9600);
  Serial.println("Pushbutton bounce test:");
}

byte previousState = HIGH;         // what state was the button last time
unsigned int count = 0;            // how many times has it changed to low
unsigned long countAt = 0;         // when count changed
unsigned int countPrinted = 0;     // last count printed

void loop() {
  // Serial.println("Looping...");
  byte buttonState = digitalRead(buttonPin);
  if (buttonState != previousState) {
    if (buttonState == LOW) {
      count = count + 1;
      countAt = millis();
    }
    previousState = buttonState;
  } else {
    if (count != countPrinted) {
      unsigned long nowMillis = millis();
      if (nowMillis - countAt > 100) {
        Serial.print("count: ");
        Serial.println(count);
        countPrinted = count;
      }
    }
  }
}
