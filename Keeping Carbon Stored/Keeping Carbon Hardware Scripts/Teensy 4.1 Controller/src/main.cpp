// Examples to send for testing:
  // A2000000000
  // A2000255000
  // A2000000255
  // B2000000255
  // D1255000000
  // E1255000000
  // E5255000000
  // A1255000000
  // A1000255000
  // II000000000

#include <Arduino.h>
#include <serial_Handler.h>

const uint8_t DATABUFFER = 12;
uint8_t data[DATABUFFER];

uint16_t PCData = 0;

void clearBuffer();

void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(1000);

  //Serial.println("Teensy 4.1 (Parent) - Starting up...");
  // Initialize Serials for communication with Teensy 4.0 rows
  setSerial1();
  setSerial2();
  setSerial3();
  setSerial4();
  setSerial5();
  setSerial6();
  setSerial7();
}

void loop() {
  readSerial1();
  readSerial2();
  readSerial3();
  readSerial4();
  readSerial5();
  readSerial6();
  readSerial7();

  if (Serial.available()) 
  {
    PCData = Serial.readBytesUntil('\0', data, DATABUFFER);
    //Serial.print(PCData);
  }

  switch (data[0])
  {
    case 65:
      // Serial data recieved for Row A
      // Send to Row A, button and RGB
      //Serial.print("Sending: ");
      //Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      /*data[1] = '2';
      //Serial.print("Sending: ");
      //Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '3';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '4';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '5';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '1';
      data[2] = '0';
      data[3] = '0';
      data[4] = '0';
      data[5] = '2';
      data[6] = '5';
      data[7] = '5';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '2';
      //Serial.print("Sending: ");
      //Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '3';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '4';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3);

      data[1] = '5';
      Serial.print("Sending: ");
      Serial.write(data + 1, PCData - 1);
      Serial1.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial1.flush();
      delay(3); */

      clearBuffer();

      #ifdef debug
      Serial.println("Sending to row 1");
      #endif
      break;
    case 66:
      //send to row 2, button and RGB
      Serial2.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      //Serial2.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial2.write('\n');
      //Serial2.flush();
      //clearBuffer();
      #ifdef debug
      Serial.println("Sending to row 2");
      #endif
      break;
    case 67:
      //send to row 3, button and RGB
      Serial3.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      //Serial3.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial3.write('\n');
      //Serial3.flush();
      //clearBuffer();
      #ifdef debug
      Serial.println("Sending to row 3");
      #endif
      break;
    case 68:
      //send to row 4, button and RGB
      Serial4.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      //Serial4.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial4.write('\n');
      //Serial4.flush();
      //clearBuffer();
      #ifdef debug
      Serial.println("Sending to row 4");
      #endif
      break;
    case 69:
      //send to row 5, button and RGB
      Serial5.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      //Serial5.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial5.write('\n');
      //Serial5.flush();
      //clearBuffer();
      #ifdef debug
      Serial.println("Sending to row 5");
      #endif
      break;
    case 70:
      //send to row 6, button and RGB
      //Serial6.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial6.write('\n');
      //Serial6.flush();
      //clearBuffer();
      #ifdef debug
      Serial.println("Sending to row 6");
      #endif
      break;
    case 71:
      //send to row 7, button and RGB
      //Serial7.write(data + 1, PCData - 1);  // send "1255000000"
      //Serial7.write('\n');
      //Serial7.flush();
      //clearBuffer();
      #ifdef debug
      Serial.println("Sending to row 7");
      #endif
      break;
    case 73:
      Serial1.write(data + 1, PCData - 1);  
      //Serial1.write('\n');
      Serial2.write(data + 1, PCData - 1);  
      //Serial2.write('\n');
      Serial3.write(data + 1, PCData - 1);  
      //Serial3.write('\n');
      Serial4.write(data + 1, PCData - 1);  
      //Serial4.write('\n');
      Serial5.write(data + 1, PCData - 1);  
      //Serial5.write('\n');
      Serial6.write(data + 1, PCData - 1);  
      //Serial6.write('\n');
      Serial7.write(data + 1, PCData - 1);  
      //Serial7.write('\n');     
      clearBuffer(); 
      break;
    default:
      break;
  }
}

void clearBuffer() {
  for(int i = 0; i < DATABUFFER; i++) {
    data[i] = 0;
  }
}