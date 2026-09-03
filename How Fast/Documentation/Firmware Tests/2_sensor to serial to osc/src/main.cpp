

#include <Arduino.h>

// ===== CONFIGURATION =====
#define NUM_SENSORS 2  // Change this to test 1-8 sensors
// =========================

struct TOFSensor {
  HardwareSerial* serial;
  uint8_t rx_buf[16];
  int bufIndex;
  unsigned long lastQuery;
  int sensorID;
  
  TOFSensor(HardwareSerial* ser, int id) 
    : serial(ser), bufIndex(0), lastQuery(0), sensorID(id) {}
  
  void begin() {
    serial->begin(921600);
  }
  
  void query() {
    if (millis() - lastQuery > 200) {
      uint8_t cmd[8] = {0x57, 0x10, 0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0x00};
      for (int i = 0; i < 7; i++) cmd[7] += cmd[i];
      serial->write(cmd, 8);
      lastQuery = millis();
    }
  }
  
  void readAndProcess() {
    while (serial->available()) {
      uint8_t b = serial->read();
      
      if (bufIndex == 0 && b == 0x57) {
        rx_buf[0] = b;
        bufIndex = 1;
      }
      else if (bufIndex == 1 && b == 0x00) {
        rx_buf[1] = b;
        bufIndex = 2;
      }
      else if (bufIndex >= 2 && bufIndex < 16) {
        rx_buf[bufIndex] = b;
        bufIndex++;
        
        if (bufIndex == 16) {
          long dist_raw = ((long)rx_buf[10] << 24) | ((long)rx_buf[9] << 16) | ((long)rx_buf[8] << 8);
          float distance = (dist_raw / 256.0) / 1000.0;
          
          Serial.print(sensorID);
          Serial.print(":");
          Serial.println(distance, 3);
          
          bufIndex = 0;
        }
      }
      else {
        bufIndex = 0;
      }
    }
  }
};

// Initialize sensors (Serial2-Serial8 available on Teensy)
TOFSensor* sensors[8];

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);
  
  // Initialize requested number of sensors
  if (NUM_SENSORS >= 1) { sensors[0] = new TOFSensor(&Serial2, 1); sensors[0]->begin(); }
  if (NUM_SENSORS >= 2) { sensors[1] = new TOFSensor(&Serial3, 2); sensors[1]->begin(); }
  if (NUM_SENSORS >= 3) { sensors[2] = new TOFSensor(&Serial4, 3); sensors[2]->begin(); }
  if (NUM_SENSORS >= 4) { sensors[3] = new TOFSensor(&Serial5, 4); sensors[3]->begin(); }
  if (NUM_SENSORS >= 5) { sensors[4] = new TOFSensor(&Serial6, 5); sensors[4]->begin(); }
  if (NUM_SENSORS >= 6) { sensors[5] = new TOFSensor(&Serial7, 6); sensors[5]->begin(); }
  // if (NUM_SENSORS >= 7) { sensors[6] = new TOFSensor(&Serial8, 7); sensors[6]->begin(); }
  if (NUM_SENSORS >= 8) { sensors[7] = new TOFSensor(&Serial1, 8); sensors[7]->begin(); }
  
  Serial.print("TOF Distance Reader - ");
  Serial.print(NUM_SENSORS);
  Serial.println(" sensor(s) active");
}

void loop() {
  for (int i = 0; i < NUM_SENSORS; i++) {
    sensors[i]->query();
    sensors[i]->readAndProcess();
  }
}