

#include <Arduino.h>
#include <Wire.h>

// I2C Address - change if needed
const uint8_t I2C_ADDRESS = 0x08;

uint8_t counter = 0;
unsigned long lastHeartbeat = 0;

// Called when master requests data
void onRequest() {
  Wire.write(counter);
  Serial.print("*** REQUEST RECEIVED! Sent: ");
  Serial.println(counter);
  counter++;
}

void setup() {
  Serial.begin(9600);
  delay(5000);
  
  Serial.println("\n=== M0 I2C SLAVE DIAGNOSTIC ===");
  
  // Enable internal pull-ups on I2C pins
  pinMode(PIN_WIRE_SDA, INPUT_PULLUP);
  pinMode(PIN_WIRE_SCL, INPUT_PULLUP);
  
  Serial.print("SDA Pin: ");
  Serial.println(PIN_WIRE_SDA);
  Serial.print("SCL Pin: ");
  Serial.println(PIN_WIRE_SCL);
  Serial.print("Address: 0x");
  Serial.println(I2C_ADDRESS, HEX);
  
  // Start I2C FRIEND
  Wire.begin(I2C_ADDRESS);
  Wire.onRequest(onRequest);
  
  Serial.println("\n*** I2C SLAVE READY ***");
  Serial.println("Waiting for master requests...");
  Serial.println("\nCONNECTION GUIDE:");
  Serial.print("  M0 Pin ");
  Serial.print(PIN_WIRE_SDA);
  Serial.println(" (SDA) -> Teensy Pin 18");
  Serial.print("  M0 Pin ");
  Serial.print(PIN_WIRE_SCL);
  Serial.println(" (SCL) -> Teensy Pin 19");
  Serial.println("  M0 GND -> Teensy GND");
  Serial.println("\nHeartbeat every 5 sec...\n");
}

void loop() {
  // Heartbeat to show M0 is running
  if (millis() - lastHeartbeat >= 5000) {
    lastHeartbeat = millis();
    Serial.print("[Heartbeat] Waiting... (counter=");
    Serial.print(counter);
    Serial.println(")");
  }
  delay(100);
}
