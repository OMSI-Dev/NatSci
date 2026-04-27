const uint8_t buttonDataBuffer = 2;
uint8_t data1[buttonDataBuffer];

#define debug

void setSerial1()
{
    Serial1.begin(115200,SERIAL_8E1);
    // Serial1.attachRts(6);
    // Serial1.attachCts(2);
    #ifdef debug
    Serial.println("Serial 1 has started.");
    #endif
}

void readSerial1()
{

    if (Serial1.available()) 
  {
    //clear data
    // for(uint8_t i = 0; i<buttonDataBuffer; i++)
    // {
    // data1[i] = 0;
    // }

    //load buffer
    Serial1.readBytesUntil('\n', data1,buttonDataBuffer);


    #ifdef debug
    Serial.print("Received button pressed: ");
    Serial.println(data1[0]);
    #endif
    Serial.print("A");
    Serial.println(data1[0]);}
    
}