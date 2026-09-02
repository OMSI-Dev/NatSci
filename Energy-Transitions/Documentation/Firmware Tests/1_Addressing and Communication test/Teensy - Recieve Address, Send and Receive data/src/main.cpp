/*
 * TEST 1 - TEENSY BOARD
 * Monitor I2C bus for M0 addresses
 * Wait for 2x M0 boards to initialize
 * Maintain active communication with both devices
 */

#include <Arduino.h>
#include <Wire.h>

// I2C Configuration
const uint8_t I2C_BASE_ADDRESS = 0x08;
const uint8_t MAX_M0_DEVICES = 10;
const uint8_t REQUIRED_M0_DEVICES = 2;  // Wait for 2 M0 boards

// Device tracking
uint8_t detectedAddresses[MAX_M0_DEVICES];
uint8_t numDetectedDevices = 0;
bool systemReady = false;

// Timing
unsigned long lastScan = 0;
unsigned long lastComm = 0;
const unsigned long scanInterval = 3000;    // Scan every 3 seconds
const unsigned long commInterval = 1000;    // Communicate every 1 second

// Forward declarations
void scanForM0Devices();
void communicateWithDevices();
void printStatus();

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("\n========================================");
  Serial.println("   TEST 1 - TEENSY I2C MASTER");
  Serial.println("========================================\n");
  
  Serial.println("I2C Configuration:");
  Serial.println("  SDA: Pin 18");
  Serial.println("  SCL: Pin 19");
  Serial.println("  Speed: 100 kHz\n");
  
  // Initialize I2C as master
  Wire.begin();
  Wire.setClock(100000);
  
  Serial.println("I2C Master initialized\n");
  Serial.print("Waiting for ");
  Serial.print(REQUIRED_M0_DEVICES);
  Serial.println(" M0 devices to connect...\n");
  
  delay(500);
}

void scanForM0Devices() {
  Serial.println("--- Scanning for M0 Devices ---");
  
  numDetectedDevices = 0;
  
  // Scan the M0 address range (0x08-0x11)
  for (uint8_t addr = I2C_BASE_ADDRESS; addr < (I2C_BASE_ADDRESS + MAX_M0_DEVICES); addr++) {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      // Device found!
      detectedAddresses[numDetectedDevices] = addr;
      numDetectedDevices++;
      
      Serial.print("  ✓ M0 found at 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      
      // Request counter value to verify communication
      uint8_t bytesReceived = Wire.requestFrom(addr, (uint8_t)1);
      if (bytesReceived > 0) {
        uint8_t counter = Wire.read();
        Serial.print(" (counter: ");
        Serial.print(counter);
        Serial.println(")");
      } else {
        Serial.println(" (no data)");
      }
    }
    
    delay(5);
  }
  
  Serial.print("\nDevices found: ");
  Serial.print(numDetectedDevices);
  Serial.print(" / ");
  Serial.println(REQUIRED_M0_DEVICES);
  
  if (numDetectedDevices >= REQUIRED_M0_DEVICES && !systemReady) {
    systemReady = true;
    Serial.println("\n*** SYSTEM READY ***");
    Serial.println("Beginning active communication...\n");
  } else if (numDetectedDevices < REQUIRED_M0_DEVICES) {
    Serial.println("Waiting for more devices...\n");
  }
  
  Serial.println("-------------------------------\n");
}

void communicateWithDevices() {
  if (!systemReady) return;
  
  static uint8_t testData = 0;
  
  Serial.println("--- Active Communication ---");
  
  for (uint8_t i = 0; i < numDetectedDevices; i++) {
    uint8_t addr = detectedAddresses[i];
    
    // Request data from M0
    uint8_t bytesReceived = Wire.requestFrom(addr, (uint8_t)1);
    
    if (bytesReceived > 0) {
      uint8_t counter = Wire.read();
      Serial.print("[RX from 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print("] Counter: ");
      Serial.println(counter);
    }
    
    // Send test data to M0
    Wire.beginTransmission(addr);
    Wire.write(testData);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("[TX to 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print("] Data: 0x");
      if (testData < 16) Serial.print("0");
      Serial.print(testData, HEX);
      Serial.print(" (");
      Serial.print(testData);
      Serial.println(")");
    } else {
      Serial.print("[ERROR] Failed to send to 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print(" - Error code: ");
      Serial.println(error);
    }
    
    delay(50);
  }
  
  // Increment test data for next cycle
  testData++;
  if (testData > 255) testData = 0;
  
  Serial.println("----------------------------\n");
}

void printStatus() {
  Serial.println("\n=== SYSTEM STATUS ===");
  Serial.print("Devices detected: ");
  Serial.println(numDetectedDevices);
  Serial.print("System ready: ");
  Serial.println(systemReady ? "YES" : "NO");
  
  if (numDetectedDevices > 0) {
    Serial.println("\nActive addresses:");
    for (uint8_t i = 0; i < numDetectedDevices; i++) {
      Serial.print("  Device ");
      Serial.print(i + 1);
      Serial.print(": 0x");
      if (detectedAddresses[i] < 16) Serial.print("0");
      Serial.println(detectedAddresses[i], HEX);
    }
  }
  Serial.println("=====================\n");
}

void loop() {
  // Scan for devices periodically
  if (millis() - lastScan >= scanInterval) {
    lastScan = millis();
    scanForM0Devices();
  }
  
  // Communicate with devices when system is ready
  if (systemReady && (millis() - lastComm >= commInterval)) {
    lastComm = millis();
    communicateWithDevices();
  }
  
  // Check for serial commands
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    switch(cmd) {
      case 's':
      case 'S':
        Serial.println("\nManual scan requested...");
        scanForM0Devices();
        break;
        
      case 'i':
      case 'I':
        printStatus();
        break;
        
      case '?':
      case 'h':
      case 'H':
        Serial.println("\n=== COMMANDS ===");
        Serial.println("s - Scan for M0 devices");
        Serial.println("i - Show system status");
        Serial.println("h - Show this help");
        Serial.println("================\n");
        break;
    }
    
    // Clear serial buffer
    while (Serial.available()) Serial.read();
  }
  
  delay(10);
}
