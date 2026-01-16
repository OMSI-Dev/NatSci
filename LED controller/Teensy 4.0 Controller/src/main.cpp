/* Teensy 4.0 RGB LED Controller with EEPROM Storage and Animation Mode
 * 
 * Hardware connections:
 * - OLED Display (128x64): SDA > pin 18, SCL > pin 19, VCC > 5V, GND > GND
 * - Rotary Encoder: A1 > pin 15, B1 > pin 14, GND > GND
 * - Buttons S1-S4: pins 2-5 (Presets 1-4)
 * - Button S5 (EDIT): pin 6
 * - Button S6 (SAVE): pin 7
 * - Button S7 (WRITE): pin 8
 * - Button S8 (EXPORT/Animation Toggle): pin 9
 * - LED Indicator: pin 10 (for S8 button)
 * - I2C to ItsyBitsy: Wire1 on pins 16/17 (3.3V bus)
 * - I2C to OLED: Wire on pins 18/19 (3.3V bus)
 * 
 * Button Functions:
 * - S1-S4: Select preset slots (Static RGB or Animation based on mode)
 * - S5 (EDIT): Cycle through R→G→B→Neutral edit modes
 * - S6 (WRITE): Save current RGB to ItsyBitsy EEPROM (persistent)
 * - S7 (EXPORT): Save current RGB to Teensy EEPROM preset slot
 * - S8 (ANIM): Toggle Animation Mode ON/OFF
 * 
 * Edit Mode:
 * - Press EDIT to cycle: Neutral → R (red blinks) → G (green blinks) → B (blue blinks) → Neutral
 * - In R/G/B mode: rotary encoder edits that color channel (0-255)
 * - In Neutral mode: no editing, can send to LED or save to presets
 * 
 * Animation Mode:
 * - When toggled ON: LED indicator lights up, presets become animation slots
 * - OLED displays "Animation Preset X" instead of "Preset X"
 * - Animation sequences not yet implemented
 */

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
