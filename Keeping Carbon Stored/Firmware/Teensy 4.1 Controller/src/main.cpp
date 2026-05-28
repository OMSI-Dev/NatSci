#include <Arduino.h>
#include <serial_Handler.h>

const uint8_t DATABUFFER = 12;
uint8_t data[DATABUFFER];
uint16_t PCData = 0;
uint8_t packet[DATABUFFER];

void clearBuffer();

void setup() {
  Serial.begin(115200);
  delay(1000);
  #ifdef debug
  Serial.println("Teensy 4.1 (Parent) - Starting up...");
  #endif
  setSerial1(); setSerial2(); setSerial3(); setSerial4();
  setSerial5(); setSerial6(); setSerial7();
}

void loop() {
  readSerial1(); readSerial2(); readSerial3(); readSerial4();
  readSerial5(); readSerial6(); readSerial7();

  if (Serial.available()) { PCData = Serial.readBytesUntil('\0', data, DATABUFFER); }

  switch (data[0])
  {
    case 65: // Row A
    {
  #ifdef debug
  Serial.print("Sending to Row E: ");
  Serial.write(data + 1, PCData - 1);
  Serial.println();
  #endif

  

  if (data[1] == '1')
  {
    static const uint8_t p1[12] = {'A','1','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p2[12] = {'B','2','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p3[12] = {'C','1','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p4[12] = {'D','2','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p5[12] = {'E','1','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p6[12] = {'F','2','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p7[12] = {'G','1','2','5','5','0','0','0','0','0','0','\0'};

    Serial1.write(p1 + 1, 11);
    Serial2.write(p2 + 1, 11); 
    Serial3.write(p3 + 1, 11); 
    Serial4.write(p4 + 1, 11);
    
    Serial5.write(p5 + 1, 11); 
    
    Serial6.write(p6 + 1, 11); 
    Serial7.write(p7 + 1, 11); 

  }

  if (data[1] == '2')
  {
    static const uint8_t p1[12] = {'A','2','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p2[12] = {'B','1','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p3[12] = {'C','2','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p4[12] = {'D','1','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p5[12] = {'E','2','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p6[12] = {'F','1','2','5','5','0','0','0','0','0','0','\0'};
    static const uint8_t p7[12] = {'G','2','2','5','5','0','0','0','0','0','0','\0'};

    Serial1.write(p1 + 1, 11);
    
    Serial2.write(p2 + 1, 11); 
    
    Serial3.write(p3 + 1, 11);
    
    Serial4.write(p4 + 1, 11);
    Serial5.write(p5 + 1, 11); 
    Serial6.write(p6 + 1, 11);
    
    Serial7.write(p7 + 1, 11); 
  }

  clearBuffer();
  break;

    }

  //   case 66: // Row B
  //   {
  //     #ifdef debug
  //     Serial.print("Sending to Row B: ");
  //     Serial.write(data + 1, PCData - 1);
  //     #endif
  //     if (data[2] == '2' && data[1] == '1')
  //     {
  //       static const uint8_t on[12]  = {'B','1','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '2' && data[1] == '2')
  //     {
  //       static const uint8_t on[12]  = {'B','2','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

      
  //     if (data[2] == '0')
  //     {
  //       static const uint8_t off[12] = {'B','1','0','0','0','0','0','0','0','0','0','\0'};
  //       memcpy(packet, off, 12);
  //     }
  //     Serial2.write(packet + 1, 11);
  //     Serial2.flush(); // FIX 4: was Serial1.write / Serial2.flush mismatch
  //     clearBuffer();
  //     break;
  //   }

  //   case 67: // Row C
  //   {
  //     #ifdef debug
  //     Serial.print("Sending to Row C: ");
  //     Serial.write(data + 1, PCData - 1);
  //     #endif
  //     if (data[2] == '2' && data[1] == '1')
  //     {
  //       static const uint8_t on[12]  = {'C','1','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '2' && data[1] == '2')
  //     {
  //       static const uint8_t on[12]  = {'C','2','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }
  //     if (data[2] == '0')
  //     {
  //       static const uint8_t off[12] = {'C','1','0','0','0','0','0','0','0','0','0','\0'};
  //       memcpy(packet, off, 12);
  //     }
  //     Serial3.write(packet + 1, 11);
  //     Serial3.flush(); // FIX 4: was Serial1.write / Serial3.flush mismatch
  //     clearBuffer();
  //     break;
  //   }

  //   case 68: // Row D
  //   {
  //     if (data[2] == '2')
  //     if (data[2] == '2' && data[1] == '1')
  //     {
  //       static const uint8_t on[12]  = {'D','1','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '2' && data[1] == '2')
  //     {
  //       static const uint8_t on[12]  = {'D','2','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }
  //     if (data[2] == '0')
  //     {
  //       static const uint8_t off[12] = {'D','1','0','0','0','0','0','0','0','0','0','\0'};
  //       memcpy(packet, off, 12);
  //     }
  //     Serial4.write(packet + 1, 11);
  //     Serial4.flush(); // FIX 4: was Serial1.write / Serial4.flush mismatch
  //     clearBuffer();
  //     break;
  //   }

  //   case 69: // Row E
  //   {
  //     #ifdef debug
  //     Serial.print("Sending to Row E: ");
  //     Serial.write(data + 1, PCData - 1);
  //     Serial.println();
  //     #endif
  //     // FIX 3: was = (assignment) instead of == (comparison)
  //     if (data[2] == '2' && data[1] == '1')
  //     {
  //       static const uint8_t on[12]  = {'E','1','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '2' && data[1] == '2')
  //     {
  //       static const uint8_t on[12]  = {'E','2','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }
  //     if (data[2] == '0')
  //     {
  //       static const uint8_t off[12] = {'E','1','0','0','0','0','0','0','0','0','0','\0'};
  //       memcpy(packet, off, 12);
  //     }
  //     Serial5.write(packet + 1, 11);
  //     Serial5.flush();
  //     clearBuffer();
  //     break;
  //   }

  //   case 70: // Row F
  //   {
  //     #ifdef debug
  //     Serial.print("Sending to Row F: ");
  //     Serial.write(data + 1, PCData - 1);
  //     #endif
  //     if (data[2] == '2' && data[1] == '1')
  //     {
  //       static const uint8_t on[12]  = {'F','1','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '2' && data[1] == '2')
  //     {
  //       static const uint8_t on[12]  = {'F','2','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }
  //     if (data[2] == '0')
  //     {
  //       static const uint8_t off[12] = {'F','1','0','0','0','0','0','0','0','0','0','\0'};
  //       memcpy(packet, off, 12);
  //     }
  //     Serial6.write(packet + 1, 11);
  //     Serial6.flush();
  //     clearBuffer();
  //     break;
  //   }

  //   case 71: // Row G
  //   {
  //     #ifdef debug
  //     Serial.print("Sending to Row G: ");
  //     Serial.write(data + 1, PCData - 1);
  //     #endif

  //     if (data[2] == '2' && data[1] == '1')
  //     {
  //       static const uint8_t on[12]  = {'G','1','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '2' && data[1] == '2')
  //     {
  //       static const uint8_t on[12]  = {'G','2','2','5','5','0','0','0','0','0','0','\0'};
  //       memcpy(packet, on, 12);
  //     }

  //     if (data[2] == '0')
  //     {
  //       static const uint8_t off[12] = {'G','1','0','0','0','0','0','0','0','0','0','\0'};
  //       memcpy(packet, off, 12);
  //     }
      
  //     Serial7.write(packet + 1, 11);
  //     Serial7.flush();
  //     clearBuffer();
  //     break;
  //   }

    case 73: // 'I' — Set all rows to IDLE
    {
      static const uint8_t idle[12] = {'X','1','0','0','0','0','0','0','0','0','0','\0'};
      uint8_t tmp[12];
      // Send IDLE to all rows, updating the row letter for each
      const char rows[] = {'A','B','C','D','E','F','G'};
      HardwareSerial* serials[] = {&Serial1,&Serial2,&Serial3,&Serial4,&Serial5,&Serial6,&Serial7};
      for (int i = 0; i < 7; i++) {
        memcpy(tmp, idle, 12);
        tmp[0] = rows[i];
        serials[i]->write(tmp + 1, 11);
        serials[i]->flush();
      }
      clearBuffer();
      break;
    }
    default:
    break;
  }
}

void clearBuffer() {
  for (int i = 0; i < DATABUFFER; i++) { data[i] = 0; }
}