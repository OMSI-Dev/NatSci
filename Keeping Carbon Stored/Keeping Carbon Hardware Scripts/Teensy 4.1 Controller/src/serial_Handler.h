const uint8_t BUTTONDATABUFFER = 2;
uint8_t data1[BUTTONDATABUFFER], data2[BUTTONDATABUFFER], data3[BUTTONDATABUFFER], data4[BUTTONDATABUFFER];
uint8_t data5[BUTTONDATABUFFER], data6[BUTTONDATABUFFER], data7[BUTTONDATABUFFER];

void clearBuffer(uint8_t dataArray[]);
//#define debug

void setSerial1()
{
    Serial1.begin(115200, SERIAL_8E1);

    while(!Serial1) { 
        //Serial.println("Waiting for Serial1 two begin..."); 
    }

    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 1 has started.");
    #endif
}

void setSerial2()
{
    Serial2.begin(115200, SERIAL_8E1);

    while(!Serial2) { 
        //Serial.println("Waiting for Serial 2 two begin..."); 
    }

    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 2 has started.");
    #endif
}

void setSerial3()
{
    Serial3.begin(115200, SERIAL_8E1);

    while(!Serial3) { 
        //Serial.println("Waiting for Serial3 two begin..."); 
    }

    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 3 has started.");
    #endif
}

void setSerial4()
{
    Serial4.begin(115200, SERIAL_8E1);

    while(!Serial4) { 
        //Serial.println("Waiting for Serial4 two begin..."); 
    }

    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 4 has started.");
    #endif
}

void setSerial5()
{
    Serial5.begin(115200, SERIAL_8E1);

    while(!Serial5) { 
        //Serial.println("Waiting for Serial5 two begin...");
    }
    
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 5 has started.");
    #endif
}

void setSerial6()
{
    Serial6.begin(115200, SERIAL_8E1);

    while(!Serial6) {
        //Serial.println("Waiting for Serial6 two begin...");
    }

    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 6 has started.");
    #endif 
}

void setSerial7()
{
    Serial7.begin(115200, SERIAL_8E1);

    while(!Serial7) {
        //Serial.println("Waiting for Serial7 two begin...");
    }

    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 7 has started.");
    #endif
}

// READ FROM ROW A
void readSerial1() {
    if (Serial1.available()) {
        //load buffer
        Serial1.readBytesUntil('\0', data1, BUTTONDATABUFFER);

        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("In readSerial1: A");
        Serial.println(data1[0]);
        clearBuffer(data1);
    }
}

void readSerial2() {
    if (Serial2.available()) {
        //load buffer
        Serial2.readBytesUntil('\n', data2,BUTTONDATABUFFER);


        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("B");
        Serial.println(data2[0]);
        clearBuffer(data2);
    }
}

void readSerial3() {
    if (Serial3.available()) {
        //load buffer
        Serial3.readBytesUntil('\n', data3,BUTTONDATABUFFER);

        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("C");
        Serial.println(data3[0]);
        clearBuffer(data3);
    }
}

void readSerial4() {
    if (Serial4.available()) {
        //load buffer
        Serial4.readBytesUntil('\n', data4,BUTTONDATABUFFER);

        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("D");
        Serial.println(data4[0]);
        clearBuffer(data4);
    }
}

void readSerial5() {
    if (Serial5.available()) {
        //load buffer
        Serial5.readBytesUntil('\n', data5,BUTTONDATABUFFER);

        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("E");
        Serial.println(data5[0]);
        clearBuffer(data5);
    }
}

void readSerial6() {
    if (Serial6.available()) {
        //load buffer
        Serial6.readBytesUntil('\n', data6,BUTTONDATABUFFER);

        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("F");
        Serial.println(data6[0]);
        clearBuffer(data6);
    }
}

void readSerial7() {
    if (Serial7.available()) {
        //load buffer
        Serial7.readBytesUntil('\n', data7,BUTTONDATABUFFER);

        #ifdef debug
        Serial.print("Received button pressed: ");
        Serial.println(data1[0]);
        #endif
        Serial.print("G");
        Serial.println(data7[0]);
        clearBuffer(data7);
    }
}

void clearBuffer(uint8_t dataArray[]) {
  for(int i = 0; i < BUTTONDATABUFFER; i++) {
    dataArray[i] = 0;
  }
}