/*
 * TEST 1 - M0 BOARD
 * Initialize I2C address from header pins
 * Send counter data and receive commands from Teensy master
 */

#include <Arduino.h>
#include <Wire.h>
#include <i2C_Address.h>
#include <Adafruit_DotStar.h>

// Onboard DotStar LED (ItsyBitsy M0)
#define DATAPIN    41
#define CLOCKPIN   40
#define NUMPIXELS  1
Adafruit_DotStar strip(NUMPIXELS, DATAPIN, CLOCKPIN, DOTSTAR_BRG);

uint16_t i2cAddress = 0x08;
volatile uint8_t counter = 0;
volatile bool communicationActive = false;
unsigned long lastHeartbeat = 0;
unsigned long lastBlink = 0;
bool ledState = false;

// Called when master requests data from this slave
void onRequest() {
  Wire.write(counter);
  Serial.print("[TX] Sent counter: ");
  Serial.println(counter);
  counter++;
  
  // Mark communication as active
  if (!communicationActive) {
    communicationActive = true;
    strip.setPixelColor(0, 0, 255, 0);  // Solid green
    strip.show();
    Serial.println("*** I2C Communication Active - LED Green ***");
  }
}

// Called when master sends data to this slave
void onReceive(int numBytes) {
  if (numBytes > 0) {
    uint8_t receivedData = Wire.read();
    
    Serial.print("[RX] Received data: 0x");
    if (receivedData < 16) Serial.print("0");
    Serial.print(receivedData, HEX);
    Serial.print(" (");
    Serial.print(receivedData);
    Serial.println(")");
    
    // Mark communication as active
    if (!communicationActive) {
      communicationActive = true;
      strip.setPixelColor(0, 0, 255, 0);  // Solid green
      strip.show();
      Serial.println("*** I2C Communication Active - LED Green ***");
    }
    
    // Clear remaining bytes
    while (Wire.available()) {
      Wire.read();
    }
  }
}

void setup() {
  Serial.begin(9600);
  // while(!Serial);  // Wait for serial connection
  
  // Initialize onboard LED
  strip.begin();
  strip.setBrightness(50);
  strip.show();  // Initialize all pixels to 'off'
  
  Serial.println("\n========================================");
  Serial.println("   TEST 1 - M0 I2C SLAVE");
  Serial.println("========================================\n");
  
  Serial.println("Initializing... (LED flashing red)");
  
  // Flash red LED during initialization
  for (int i = 0; i < 6; i++) {
    strip.setPixelColor(0, 255, 0, 0);  // Red
    strip.show();
    delay(150);
    strip.setPixelColor(0, 0, 0, 0);    // Off
    strip.show();
    delay(150);
  }
  
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
  
  // Keep LED red while waiting for communication
  strip.setPixelColor(0, 255, 0, 0);  // Red
  strip.show();
  
  Serial.println("I2C slave initialized and ready!");
  Serial.println("Waiting for Teensy master...");
  Serial.println("LED: RED (waiting) -> GREEN (active)\n");
}

void loop() {
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

