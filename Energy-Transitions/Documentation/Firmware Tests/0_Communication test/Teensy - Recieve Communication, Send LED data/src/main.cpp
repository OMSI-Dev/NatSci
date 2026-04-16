#include <Arduino.h>
#include <Wire.h>

// MAIN BOARD (Teensy 4.1) - I2C Master
// Sends LED data to connected PILL BOARDS via I2C

// I2C address range for pill boards
const int I2C_BASE_ADDRESS = 0x08;
const int MAX_PILL_BOARDS = 16;

// LED pattern settings
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 500; // Update every 500ms
uint8_t ledState = 0;

void scanI2CDevices() {
  Serial.println("Scanning I2C bus for devices...");
  int devicesFound = 0;
  
  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    byte error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("  Device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      devicesFound++;
    }
  }
  
  if (devicesFound == 0) {
    Serial.println("  No I2C devices found");
  } else {
    Serial.print("  Total devices found: ");
    Serial.println(devicesFound);
  }
  Serial.println();
}

void sendLEDData(uint8_t address, uint8_t data) {
  Wire.beginTransmission(address);
  Wire.write(data);
  byte error = Wire.endTransmission();
  
  if (error == 0) {
    Serial.print("Sent ");
    Serial.print(data);
    Serial.print(" to 0x");
    if (address < 16) Serial.print("0");
    Serial.print(address, HEX);
    Serial.println(" - Success");
  } else {
    Serial.print("Error sending to 0x");
    if (address < 16) Serial.print("0");
    Serial.print(address, HEX);
    Serial.print(" - Code: ");
    Serial.println(error);
  }
}

void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("=== MAIN BOARD (Teensy 4.1) I2C Master ===");
  Serial.println();
  
  // Initialize I2C as master
  Wire.begin();
  Wire.setClock(100000); // 100kHz I2C clock speed
  
  Serial.println("I2C Master initialized");
  
  // Wait a moment for pill boards to initialize
  delay(1000);
  
  // Scan for connected devices
  scanI2CDevices();
  
  Serial.println("Starting LED data transmission...");
  Serial.println();
}

void loop() {
  // Send LED data periodically
  if (millis() - lastUpdate >= updateInterval) {
    lastUpdate = millis();
    
    // Toggle LED state
    ledState = !ledState;
    
    Serial.print("Broadcasting LED State: ");
    Serial.println(ledState ? "ON" : "OFF");
    
    // Send to all possible pill board addresses
    for (int i = 0; i < MAX_PILL_BOARDS; i++) {
      uint8_t address = I2C_BASE_ADDRESS + i;
      sendLEDData(address, ledState);
    }
    
    Serial.println();
  }
}
