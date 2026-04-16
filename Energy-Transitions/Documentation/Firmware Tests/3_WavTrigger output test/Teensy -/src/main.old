#include <Arduino.h>

// Serial Test for Teensy 4.1
// This program tests serial communication by echoing received data
// and sending periodic test messages

unsigned long lastMessage = 0;
const unsigned long messageInterval = 1000; // Send message every 1 second
int messageCount = 0;

void setup() 
{
  // Teensy 4.1 USB Serial - baud rate is ignored but specified for compatibility
  Serial.begin(115200);
  
  // Wait for serial port to connect (optional, useful for debugging)
  while (!Serial && millis() < 3000) {
    ; // wait up to 3 seconds for serial port to connect
  }
  
  Serial.println("=== Teensy 4.1 Serial Test ===");
  Serial.println("Board initialized successfully!");
  Serial.println("Type something to test echo...");
  Serial.println();
}

void loop() 
{
  // Echo any received characters
  if (Serial.available() > 0) {
    char incomingByte = Serial.read();
    Serial.print("Echo: ");
    Serial.println(incomingByte);
  }
  
  // Send periodic test message
  if (millis() - lastMessage >= messageInterval) {
    lastMessage = millis();
    messageCount++;
    
    Serial.print("Test message #");
    Serial.print(messageCount);
    Serial.print(" - Uptime: ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds");
  }
}
