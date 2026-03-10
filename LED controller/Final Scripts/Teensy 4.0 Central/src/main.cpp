/*
Connect to Trinket via SDA/SCL pins 16 and 17. 
Send LED data to Trinket to display on WS2812B LED strip.
*/

#include <Arduino.h>
#include <Wire.h>

#define I2C_ADDRESS 0x08  // Address of the ItsyBitsy peripheral
#define NUM_LEDS 800       // Number of LEDs on the strip

uint8_t ledData[NUM_LEDS * 3];  // RGB data for all LEDs

void sendLEDData() {
  Wire1.beginTransmission(I2C_ADDRESS);
  Wire1.write(ledData, NUM_LEDS * 3);  // Send all LED data
  Wire1.endTransmission();
}

void setLEDColor(int ledIndex, uint8_t r, uint8_t g, uint8_t b) {
  if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
    ledData[ledIndex * 3] = r;
    ledData[ledIndex * 3 + 1] = g;
    ledData[ledIndex * 3 + 2] = b;
  }
}

void setAllLEDs(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_LEDS; i++) {
    setLEDColor(i, r, g, b);
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Initialize I2C as central on Wire1 (pins 17=SDA, 16=SCL)
  Wire1.begin();
  Wire1.setClock(100000);  // 100kHz I2C speed
  
  // Initialize LED data to off
  memset(ledData, 0, sizeof(ledData));
  
  delay(100);  // Give peripheral time to initialize
}

void loop() {
  // Example: Cycle through colors
  
  // Red
  setAllLEDs(255, 0, 0);
  sendLEDData();
  delay(1000);
  
  // Green
  setAllLEDs(0, 255, 0);
  sendLEDData();
  delay(1000);
  
  // Blue
  setAllLEDs(0, 0, 255);
  sendLEDData();
  delay(1000);
  
  // White
  setAllLEDs(255, 255, 255);
  sendLEDData();
  delay(1000);
  
  // Rainbow effect
  static uint8_t hue = 0;
  for (int i = 0; i < 256; i++) {
    for (int led = 0; led < NUM_LEDS; led++) {
      uint8_t ledHue = hue + (led * 256 / NUM_LEDS);
      // Simple HSV to RGB conversion for rainbow effect
      uint8_t r, g, b;
      if (ledHue < 85) {
        r = ledHue * 3;
        g = 255 - ledHue * 3;
        b = 0;
      } else if (ledHue < 170) {
        ledHue -= 85;
        r = 255 - ledHue * 3;
        g = 0;
        b = ledHue * 3;
      } else {
        ledHue -= 170;
        r = 0;
        g = ledHue * 3;
        b = 255 - ledHue * 3;
      }
      setLEDColor(led, r, g, b);
    }
    sendLEDData();
    hue++;
    delay(20);
  }
  
  // Color wipe
  for (int led = 0; led < NUM_LEDS; led++) {
    setLEDColor(led, 255, 0, 128);  // Purple
    sendLEDData();
    delay(100);
  }
  
  delay(500);
}