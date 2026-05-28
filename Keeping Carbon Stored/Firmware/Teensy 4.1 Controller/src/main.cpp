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
  // F1255000000
  // F1000255000
  // F1000000255
  // F2550000000
  // F3255000000
  // F4255000000
  // F5255000000
  // G1255000000
  // G2255000000
  // G3255000000
  // G4255000000
  // G5255000000
  // E1255000000

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

  #ifdef debug
  while(!Serial);
  Serial.println("Teensy 4.1 (Parent) - Starting up...");
  #endif

  // Initialize Serials for communication with Teensy 4.0 rows
  setSerial1();
  setSerial2();
  setSerial3();
  setSerial4();
  setSerial5();
  // setSerial6();
  // setSerial7();
}

void loop() {
  readSerial1();
  readSerial2();
  readSerial3();
  readSerial4();
  readSerial5();
  //readSerial6();
  //readSerial7();

  if (Serial.available()) { PCData = Serial.readBytesUntil('\0', data, DATABUFFER); }

  switch (data[0])
  {
    case 65:
      // Serial data recieved for Row A.
      // Send to Row A, button number and RGB.
      #ifdef debug
      Serial.print("Sending to Row A: ");
      Serial.write(data + 1, PCData - 1);
      #endif

      Serial1.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 66:
      // Serial data recieved for Row B.
      // Send to Row B, button number and RGB.
      #ifdef debug
      Serial.print("Sending to Row B: ");
      Serial.write(data + 1, PCData - 1);
      #endif

      Serial2.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 67:
      // Serial data recieved for Row C.
      // Send to Row C, button number and RGB.
      #ifdef debug
      Serial.print("Sending to Row C: ");
      Serial.write(data + 1, PCData - 1);
      #endif

      Serial3.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 68:
      // Serial data recieved for Row D.
      // Send to Row D, button number and RGB.
      #ifdef debug
      Serial.print("Sending to Row D: ");
      Serial.write(data + 1, PCData - 1);
      #endif

      Serial4.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 69:
      // Serial data recieved for Row E.
      // Send to Row E, button number and RGB.
       #ifdef debug
      Serial.print("Sending to Row E: ");
      Serial.write(data + 1, PCData - 1);
      Serial.println();
      #endif

      Serial5.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 70:
      // Serial data recieved for Row F. --------ADA--------
      // Send to Row F, button number and RGB.
       #ifdef debug
      Serial.print("Sending to Row F: ");
      Serial.write(data + 1, PCData - 1);
      #endif

      Serial6.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 71:
      // Serial data recieved for Row G. --------ADA--------
      // Send to Row G, button number and RGB.
       #ifdef debug
      Serial.print("Sending to Row G: ");
      Serial.write(data + 1, PCData - 1);
      #endif

      Serial7.write(data + 1, PCData - 1);
      delay(3);
      clearBuffer();
      break;

    case 73:
      // Set all rows to IDLE state.
      Serial1.write(data + 1, PCData - 1);
      Serial2.write(data + 1, PCData - 1);
      Serial3.write(data + 1, PCData - 1);
      Serial4.write(data + 1, PCData - 1);
      Serial5.write(data + 1, PCData - 1);
      Serial6.write(data + 1, PCData - 1);
      Serial7.write(data + 1, PCData - 1);
      clearBuffer();
      break;
      
    default:
      break;
  }
}

void clearBuffer() {
  for(int i = 0; i < DATABUFFER; i++) { data[i] = 0; }
}