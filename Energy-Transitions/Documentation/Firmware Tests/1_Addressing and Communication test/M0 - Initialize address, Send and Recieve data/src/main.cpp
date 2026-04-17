/*
 * TEST 1 - M0 BOARD
 * Initialize I2C address from header pins
 * Send counter data and receive commands from Teensy master
 */

#include <Arduino.h>
#include <FastLED.h>
#include <Wire.h>
#include <i2C_Address.h>

// LED Chain Configuration
const int LED_PIN = 2;
const int NUM_LEDS = 20;

CRGB leds[NUM_LEDS];

uint16_t i2cAddress = 0x08;
volatile uint8_t counter = 0;
volatile uint8_t receivedData = 0;
volatile bool dataReceived = false;
unsigned long lastHeartbeat = 0;

// Called when master requests data from this slave
void onRequest() {
  Wire.write(counter);
  Serial.print("[TX] Sent counter: ");
  Serial.println(counter);
  counter++;
}

// Called when master sends data to this slave
void onReceive(int numBytes) {
  if (numBytes > 0) {
    receivedData = Wire.read();
    dataReceived = true;
    
    // Clear remaining bytes
    while (Wire.available()) {
      Wire.read();
    }
  }
}

void setup() {
  Serial.begin(9600);
  while(!Serial);  // Wait for serial connection
  
  Serial.println("\n========================================");
  Serial.println("   TEST 1 - M0 I2C SLAVE");
  Serial.println("========================================\n");
  
  // Get I2C address from GPIO header pins
  Serial.println("Reading address from GPIO pins...");
  setPins();
  i2cAddress = setAddr();
  
  Serial.print("\n*** My I2C Address: 0x");
  if (i2cAddress < 16) Serial.print("0");
  Serial.print(i2cAddress, HEX);
  Serial.print(" (");
  Serial.print(i2cAddress);
  Serial.println(") ***\n");
  
  // Initialize I2C as slave with callbacks
  Wire.begin(i2cAddress);
  Wire.onRequest(onRequest);
  Wire.onReceive(onReceive);
  
  // Initialize LED strip
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(50);
  FastLED.clear();
  FastLED.show();
  
  Serial.println("I2C slave initialized and ready!");
  Serial.println("Waiting for Teensy master...\n");
}

void loop() {
  // Process received data
  if (dataReceived) {
    dataReceived = false;
    
    Serial.print("[RX] Received command: 0x");
    if (receivedData < 16) Serial.print("0");
    Serial.println(receivedData, HEX);
    
    // Command: 0xFF = LEDs ON (white)
    if (receivedData == 0xFF) {
      fill_solid(leds, NUM_LEDS, CRGB::White);
      Serial.println("  -> LEDs ON");
    }
    // Command: 0x00 = LEDs OFF
    else if (receivedData == 0x00) {
      FastLED.clear();
      Serial.println("  -> LEDs OFF");
    }
    // Command: 0x01-0x0F = Set color hue
    else {
      fill_solid(leds, NUM_LEDS, CHSV(receivedData * 16, 255, 255));
      Serial.print("  -> Set color hue: ");
      Serial.println(receivedData * 16);
    }
    
    FastLED.show();
  }
  
  // Heartbeat to show device is alive
  if (millis() - lastHeartbeat >= 5000) {
    lastHeartbeat = millis();
    Serial.print("[Heartbeat] Address: 0x");
    if (i2cAddress < 16) Serial.print("0");
    Serial.print(i2cAddress, HEX);
    Serial.print(" | Counter: ");
    Serial.println(counter);
  }
  
  delay(10);
}

