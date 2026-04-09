#include <Arduino.h>

void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(1000);
  Serial.println("Teensy 4.1 (Parent) - Starting up...");
  
  // Initialize Serial1 for communication with Teensy 4.0
  Serial1.begin(115200);
  Serial2.begin(115200);
  Serial3.begin(115200);
  Serial4.begin(115200);
  Serial5.begin(115200);
  Serial6.begin(115200);
  Serial7.begin(115200);

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

    if (Serial2.available()) {
    String data = Serial2.readStringUntil('\n');
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
        Serial2.print("LED:");
        Serial2.println(buttonNum);
        
        Serial.print("Sent LED command to 4.0: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial3.available()) {
    String data = Serial3.readStringUntil('\n');
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
        Serial3.print("LED:");
        Serial3.println(buttonNum);
        
        Serial.print("Sent LED command to 4.0: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial4.available()) {
    String data = Serial4.readStringUntil('\n');
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
        Serial4.print("LED:");
        Serial4.println(buttonNum);
        
        Serial.print("Sent LED command to 4.0: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial5.available()) {
    String data = Serial5.readStringUntil('\n');
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
        Serial5.print("LED:");
        Serial5.println(buttonNum);
        
        Serial.print("Sent LED command to 4.0: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial6.available()) {
    String data = Serial6.readStringUntil('\n');
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
        Serial6.print("LED:");
        Serial6.println(buttonNum);
        
        Serial.print("Sent LED command to 4.0: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial7.available()) {
    String data = Serial7.readStringUntil('\n');
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
        Serial7.print("LED:");
        Serial7.println(buttonNum);
        
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