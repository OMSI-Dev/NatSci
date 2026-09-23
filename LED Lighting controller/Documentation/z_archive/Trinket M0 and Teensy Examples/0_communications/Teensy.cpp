#include <Wire.h>

#define TRINKET_ADDRESS 0x10

void setup() {
  Serial.begin(9600);
  Wire1.begin();  // Initialize I2C on pins 16/17
  delay(1000);
  
  Serial.println("Teensy I2C Sender Ready");
  Serial.println("Sending test data to Trinket every 2 seconds...");
}

void loop() {
  Serial.println("Sending data to Trinket...");
  
  Wire1.beginTransmission(TRINKET_ADDRESS);
  Wire1.write(255);  // Send 3 bytes
  Wire1.write(0);
  Wire1.write(0);
  byte error = Wire1.endTransmission();
  
  if (error == 0) {
    Serial.println("✓ Success! Data sent.");
  } else if (error == 1) {
    Serial.println("✗ Error 1: Data too long");
  } else if (error == 2) {
    Serial.println("✗ Error 2: NACK on address (Trinket not responding)");
  } else if (error == 3) {
    Serial.println("✗ Error 3: NACK on data");
  } else if (error == 4) {
    Serial.println("✗ Error 4: Other error");
  }
  
  Serial.println("---");
  delay(2000);  // Send every 2 seconds
}