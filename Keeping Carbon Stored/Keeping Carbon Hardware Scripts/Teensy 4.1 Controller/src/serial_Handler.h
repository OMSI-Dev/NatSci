const uint8_t buttonDataBuffer = 2;
uint8_t data1[buttonDataBuffer];
uint8_t data2[buttonDataBuffer];
uint8_t data3[buttonDataBuffer];
uint8_t data4[buttonDataBuffer];
uint8_t data5[buttonDataBuffer];
uint8_t data6[buttonDataBuffer];
uint8_t data7[buttonDataBuffer];

//#define debug

void setSerial1()
{
    Serial1.begin(38400,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 1 has started.");
    #endif
}
void setSerial2()
{
    Serial2.begin(38400,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 2 has started.");
    #endif
}
void setSerial3()
{
    Serial3.begin(38400, SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 3 has started.");
    #endif
}
void setSerial4()
{
    Serial4.begin(38400,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 4 has started.");
    #endif
}

void setSerial5()
{
    Serial5.begin(38400,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 5 has started.");
    #endif
}

void setSerial6()
{
    Serial6.begin(38400,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 6 has started.");
    #endif 
}

void setSerial7()
{
    Serial7.begin(38400,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 7 has started.");
    #endif
}


void readSerial1()
{

    if (Serial1.available()) 
  {
    //load buffer
    Serial1.readBytesUntil('\n', data1,buttonDataBuffer);

    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("A");
    Serial.println(data1[0]);}

}

void readSerial2()
{

    if (Serial2.available()) 
  {
    //load buffer
    Serial2.readBytesUntil('\n', data2,buttonDataBuffer);


    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("B");
    Serial.println(data2[0]);}

}

void readSerial3()
{

    if (Serial3.available()) 
  {
    //load buffer
    Serial3.readBytesUntil('\n', data3,buttonDataBuffer);

    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("C");
    Serial.println(data3[0]);}

}

void readSerial4()
{

    if (Serial4.available()) 
  {
    //load buffer
    Serial4.readBytesUntil('\n', data4,buttonDataBuffer);


    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("D");
    Serial.println(data4[0]);}

}

void readSerial5()
{

  if (Serial5.available()) 
  {
    //load buffer
    Serial5.readBytesUntil('\n', data5,buttonDataBuffer);


    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("E");
    Serial.println(data5[0]);}

}

void readSerial6()
{

  if (Serial6.available()) 
  {
    //load buffer
    Serial6.readBytesUntil('\n', data6,buttonDataBuffer);


    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("F");
    Serial.println(data6[0]);}

}

void readSerial7()
{

  if (Serial7.available()) 
  {
    //load buffer
    Serial7.readBytesUntil('\n', data7,buttonDataBuffer);


    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("G");
    Serial.println(data7[0]);}

}