// Simple SEN0647 TOF Serial Reader
// Wire: TOF_TX -> Teensy Pin7(RX2), TOF_RX -> Pin8(TX2), 5V, GND

#include <Arduino.h>

uint8_t rx_buf[16];
unsigned long lastQuery = 0;
int bufIndex = 0;

void setup() {
  Serial.begin(9600);
  Serial2.begin(921600);
  Serial.println("TOF Distance Reader - Parsing packets...");
}

void loop() {
  // Send query command every 200ms
  if (millis() - lastQuery > 200) {
    uint8_t cmd[8] = {0x57, 0x10, 0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0x00};
    for (int i = 0; i < 7; i++) cmd[7] += cmd[i];
    Serial2.write(cmd, 8);
    lastQuery = millis();
  }
  
  // Read and parse response packets
  while (Serial2.available()) {
    uint8_t b = Serial2.read();
    
    // Look for start of packet: 0x57
    if (bufIndex == 0 && b == 0x57) {
      rx_buf[0] = b;
      bufIndex = 1;
    }
    // Check for second header byte: 0x00
    else if (bufIndex == 1 && b == 0x00) {
      rx_buf[1] = b;
      bufIndex = 2;
    }
    // Collect rest of packet (14 more bytes)
    else if (bufIndex >= 2 && bufIndex < 16) {
      rx_buf[bufIndex] = b;
      bufIndex++;
      
      // Full packet received
      if (bufIndex == 16) {
        // Extract distance from bytes 8, 9, 10
        long dist_raw = ((long)rx_buf[10] << 24) | ((long)rx_buf[9] << 16) | ((long)rx_buf[8] << 8);
        float distance = (dist_raw / 256.0) / 1000.0;
        
        // Extract signal strength from bytes 12, 13
        int signal = (rx_buf[13] << 8) | rx_buf[12];
        
        Serial.print("Distance: ");
        Serial.print(distance, 3);
        Serial.print(" m  |  Signal: ");
        Serial.println(signal);
        
        bufIndex = 0; // Reset for next packet
      }
    }
    else {
      bufIndex = 0; // Reset on bad data
    }
  }
}