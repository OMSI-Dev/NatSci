/* Trinket M0 LED Unit
 * 
 * Receives RGB color data via I2C from Teensy controller
 * I2C Address: 0x10
 * 
 * Hardware:
 * - LED Strip: Data pin connected to Pin 4
 * - I2C: SDA/SCL for communication with Teensy
 */

#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#define I2C_ADDRESS 0x10
#define LED_PIN 4
#define NUM_LEDS 30  // Adjust this to match your LED strip length

// LED strip object
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// RGB color storage
volatile uint8_t redValue = 0;
volatile uint8_t greenValue = 0;
volatile uint8_t blueValue = 0;
volatile bool newColorReceived = false;

void receiveEvent(int bytes) {
  if(bytes >= 3) {
    // Read RGB values
    redValue = Wire.read();
    greenValue = Wire.read();
    blueValue = Wire.read();
    
    // Clear any remaining bytes
    while(Wire.available()) {
      Wire.read();
    }
    
    newColorReceived = true;
    
    // Blink built-in LED to confirm reception
    digitalWrite(LED_BUILTIN, HIGH);
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  // 3 fast blinks on startup to show we're alive
  for(int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
  
  // Initialize LED strip
  strip.begin();
  strip.clear();
  strip.show();  // Initialize all pixels to 'off'
  strip.setBrightness(255);  // Full brightness (0-255)
  
  // Initialize I2C as slave
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
}

void loop() {
  if(newColorReceived) {
    newColorReceived = false;
    
    // Set all LEDs to the received RGB color
    uint32_t color = strip.Color(redValue, greenValue, blueValue);
    strip.fill(color);
    strip.show();
    
    // Brief blink to confirm update
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);
  }
  
  // Add small delay
  delay(10);
}