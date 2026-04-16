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

  Serial.println("Serial ports initialized:");
  Serial.println("  Serial1 - Row 1");
  Serial.println("  Serial2 - Row 2");
  Serial.println("  Serial3 - Row 3");
  Serial.println("  Serial4 - Row 4");
  Serial.println("  Serial5 - Row 5");
  Serial.println("  Serial6 - Row 6");
  Serial.println("  Serial7 - Row 7");
  Serial.println("Ready to receive button data and send LED commands");
}

void loop() {
  // Check for button data from Teensy 4.0
  if (Serial1.available()) {
    String data = Serial1.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 1 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 1 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial1.print("LED:");
        Serial1.println(buttonNum);
        
        Serial.print("Row 1 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 1 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial2.available()) {
    String data = Serial2.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 2 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 2 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial2.print("LED:");
        Serial2.println(buttonNum);
        
        Serial.print("Row 2 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 2 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial3.available()) {
    String data = Serial3.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 3 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 3 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial3.print("LED:");
        Serial3.println(buttonNum);
        
        Serial.print("Row 3 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 3 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial4.available()) {
    String data = Serial4.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 4 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 4 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial4.print("LED:");
        Serial4.println(buttonNum);
        
        Serial.print("Row 4 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 4 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial5.available()) {
    String data = Serial5.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 5 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 5 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial5.print("LED:");
        Serial5.println(buttonNum);
        
        Serial.print("Row 5 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 5 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial6.available()) {
    String data = Serial6.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 6 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 6 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial6.print("LED:");
        Serial6.println(buttonNum);
        
        Serial.print("Row 6 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 6 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }

    if (Serial7.available()) {
    String data = Serial7.readStringUntil('\n');
    data.trim();
    
    Serial.print("Row 7 - Received: ");
    Serial.println(data);
    
    // Parse button data format: "BTN:X" where X is 1-4
    if (data.startsWith("BTN:")) {
      int buttonNum = data.substring(4).toInt();
      
      if (buttonNum >= 1 && buttonNum <= 4) {
        Serial.print("Row 7 - Button ");
        Serial.print(buttonNum);
        Serial.println(" pressed - Processing...");
        
        // Send LED command back to Teensy 4.0
        Serial7.print("LED:");
        Serial7.println(buttonNum);
        
        Serial.print("Row 7 - Sent LED command: LED:");
        Serial.println(buttonNum);
      } else {
        Serial.print("Row 7 - Invalid button number: ");
        Serial.println(buttonNum);
      }
    }
  }
  
  delay(10);  // Small delay to prevent overwhelming the serial buffer
}