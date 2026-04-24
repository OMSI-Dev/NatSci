#include <Arduino.h>

//A1255000000
const uint8_t dataBuffer = 12;
uint8_t data[dataBuffer];

uint32_t PCData =0;

void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(1000);
  //Serial.println("Teensy 4.1 (Parent) - Starting up...");
  
  // Initialize Serial1 for communication with Teensy 4.0
  Serial1.begin(9600,SERIAL_8E1);
  Serial2.begin(9600,SERIAL_8E1);
  Serial3.begin(9600,SERIAL_8E1);
  Serial4.begin(9600,SERIAL_8E1);
  Serial5.begin(9600,SERIAL_8E1);
  Serial6.begin(9600,SERIAL_8E1);
  Serial7.begin(9600,SERIAL_8E1);

  //Serial.println("Serial ports initialized:");
  // Serial.println("  Serial1 - Row 1");
  // Serial.println("  Serial2 - Row 2");
  // Serial.println("  Serial3 - Row 3");
  // Serial.println("  Serial4 - Row 4");
  // Serial.println("  Serial5 - Row 5");
  // Serial.println("  Serial6 - Row 6");
  // Serial.println("  Serial7 - Row 7");
  //Serial.println("Ready to receive button data and send LED commands");
}

void loop() {
  //read incoming messages from PC
  //format A1255000000
  //A2000000000
  //A2000255000
  //A2000000255
  //B2000000255
  //D1255000000
  //E1255000000
//E5255000000
  //A1255000000A
  if (Serial.available()) 
  {
    PCData = Serial.readBytesUntil('\n', data,dataBuffer);
  }

  

  delay(100);
  switch (data[0])
  {
    case 65:
      //send to row 1, button and RGB
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      Serial1.write('\n');

      break;
    case 66:
      //send to row 1, button and RGB
      Serial2.write(data + 1, PCData - 1);  // send "1255000000"
      Serial2.write('\n');

      break;
    case 67:
      //send to row 1, button and RGB
      Serial3.write(data + 1, PCData - 1);  // send "1255000000"
      Serial3.write('\n');
      break;
    case 68:
      //send to row 1, button and RGB
      Serial4.write(data + 1, PCData - 1);  // send "1255000000"
      Serial4.write('\n');
      break;
    case 69:
      //send to row 1, button and RGB
      Serial5.write(data + 1, PCData - 1);  // send "1255000000"
      Serial5.write('\n');
      break;
    case 70:
      //send to row 1, button and RGB
      Serial6.write(data + 1, PCData - 1);  // send "1255000000"
      Serial6.write('\n');
      break;
    case 71:
      //send to row 1, button and RGB
      Serial7.write(data + 1, PCData - 1);  // send "1255000000"
      Serial7.write('\n');
      break;
  default:
    break;
  }

  //clear array for next incoming
  for(uint8_t i= 0; i<dataBuffer; i++)
  {
    data[i] = 0;
  }

  //delay(10);  // Small delay to prevent overwhelming the serial buffer
}