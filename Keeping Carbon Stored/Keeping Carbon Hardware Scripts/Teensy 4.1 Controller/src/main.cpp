#include <Arduino.h>

void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(1000);
  Serial.println("Teensy 4.1 (Parent) - Starting up...");
  
  // Initialize Serial1 for communication with Teensy 4.0
  Serial1.begin(115200);
  Serial.println("Serial1 initialized for communication with 4.0");
  Serial.println("Ready to receive button data and send LED commands");
}

void loop() {
  // Check for button data from Teensy 4.0
  if (Serial1.available()) {
    String data = Serial1.readStringUntil('\n');
    data.trim();
    
    Serial.print("Received from 4.0: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial1.print("LED:");
        Serial1.println(buttonNum);
        
        Serial.print("Sent LED command to 4.0: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }
  
  delay(10);  // Small delay to prevent overwhelming the serial buffer
}