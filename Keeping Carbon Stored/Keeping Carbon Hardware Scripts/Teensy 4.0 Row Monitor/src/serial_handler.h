const uint8_t dataBuffer = 11;
uint8_t data[dataBuffer];

#define CTS_Pin 8
#define RTS_Pin 7

void setSerial()
{
    //Initialize Serial1 for communication with Teensy 4.1
    //Set for a lower baud rate & a bit correction
    Serial1.begin(115200,SERIAL_8E1);
    Serial1.attachCts(CTS_Pin);
    Serial1.attachRts(RTS_Pin);
    Serial.println("Serial1 initialized for communication with 4.1");
}

void sendSerial(uint8_t buttonNum)
{
    Serial.write(buttonNum);
    Serial.write('\n');
}

void readSerial()
{

if (Serial1.available()) 
  {
    //clear data
    for(uint8_t i = 0; i<dataBuffer; i++)
    {
    data[i] = 0;
    }

    //load buffer
    Serial1.readBytesUntil('\n', data,dataBuffer);
    Serial.print("Button: ");
    Serial.println(data[0]);
    
    for(uint8_t i =0; i<dataBuffer; i++)
    {
      Serial.print(i);
      Serial.print(":");
      Serial.println(data[i]);
    }
  }

}