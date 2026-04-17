
#include <Arduino.h>
#include <Wire.h>

const uint8_t FRIEND_ADDRESS = 0x08;

void scanI2C() {
  Serial.println("\n=== FULL I2C BUS SCAN ===");
  uint8_t found = 0;
  
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      found++;
      Serial.print("  ✓ Device found at 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print(" (");
      Serial.print(addr);
      Serial.println(")");
    }
  }
  
  Serial.println("-------------------------");
  if (found == 0) {
    Serial.println("*** NO DEVICES FOUND ***");
    Serial.println("\nTROUBLESHOOTING:");
    Serial.println("1. WIRING:");
    Serial.println("   Teensy Pin 18 -> M0 Pin 26 (SDA)");
    Serial.println("   Teensy Pin 19 -> M0 Pin 27 (SCL)");
    Serial.println("   Teensy GND -> M0 GND");
    Serial.println("\n2. POWER:");
    Serial.println("   - Is M0 powered? Check its serial output");
    Serial.println("   - See 'Ready - waiting for master' message?");
    Serial.println("\n3. PULL-UPS:");
    Serial.println("   - Try external 4.7kΩ resistors:");
    Serial.println("     SDA -> 3.3V");
    Serial.println("     SCL -> 3.3V");
    Serial.println("\n4. CONTINUITY:");
    Serial.println("   - Use multimeter to verify connections");
  } else {
    Serial.print("SUCCESS! Found ");
    Serial.print(found);
    Serial.println(" device(s)");
  }
  Serial.println("=========================\n");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== TEENSY I2C MASTER TEST ===");
  
  // Enable internal pull-ups on I2C pins
  pinMode(18, INPUT_PULLUP);  // SDA
  pinMode(19, INPUT_PULLUP);  // SCL
  
  Serial.println("SDA: Pin 18 (with pull-up)");
  Serial.println("SCL: Pin 19 (with pull-up)");
  Serial.println();
  
  Wire.begin();           // Start as master
  Wire.setClock(100000);  // 100kHz
  
  Serial.println("I2C Master started");
  Serial.print("Target FRIEND: 0x");
  Serial.println(FRIEND_ADDRESS, HEX);
  
  // Scan for devices
  delay(500);
  scanI2C();
}

void loop() {
  // Request 1 byte from FRIEND
  uint8_t bytesReceived = Wire.requestFrom(FRIEND_ADDRESS, (uint8_t)1);
  
  if (bytesReceived > 0) {
    uint8_t data = Wire.read();
    Serial.print("Received: ");
    Serial.println(data);
  } else {
    Serial.println("ERROR: No response!");
  }
  
  delay(1000);  // Wait 1 second between requests
}
