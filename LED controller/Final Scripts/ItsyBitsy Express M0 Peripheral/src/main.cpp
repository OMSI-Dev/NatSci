/* 
Connect to Teensy via SDA/SCL pins.
Recieve LED data from Teensy to display on WS2812B LED strip.
Only display data from the Teensy. Do not display anything if data is not being recieved.
 */

#include <Arduino.h>
#include <FastLED.h>
#include <Wire.h>

#define LED_PIN 5
#define NUM_LEDS 800  // Adjust this to match your LED strip length
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
#define I2C_ADDRESS 0x08  // I2C peripheral address

CRGB leds[NUM_LEDS];
volatile bool dataReceived = false;
volatile uint8_t receivedData[NUM_LEDS * 3];  // RGB data for all LEDs
volatile uint8_t dataIndex = 0;

// I2C receive event handler
void receiveEvent(int numBytes) {
  dataIndex = 0;
  
  // Read all available bytes
  while (Wire.available() && dataIndex < NUM_LEDS * 3) {
    receivedData[dataIndex++] = Wire.read();
  }
  
  // Only mark as received if we got the expected amount of data
  if (dataIndex == NUM_LEDS * 3) {
    dataReceived = true;
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Initialize I2C as peripheral
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
  
  // Initialize LED strip
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(255);  // Full brightness (0-255)
  FastLED.clear();
  FastLED.show();
}

void loop() {
  // Only update LEDs when data is received from Teensy
  if (dataReceived) {
    // Update LED strip with received data
    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i].r = receivedData[i * 3];
      leds[i].g = receivedData[i * 3 + 1];
      leds[i].b = receivedData[i * 3 + 2];
    }
    FastLED.show();
    dataReceived = false;
  }
  
  delay(10);  // Short delay to prevent tight loop
} 