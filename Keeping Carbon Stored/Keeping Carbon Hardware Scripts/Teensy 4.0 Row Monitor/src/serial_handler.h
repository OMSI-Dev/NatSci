const uint8_t dataBuffer = 11;
uint8_t data[dataBuffer];

#define CTS_Pin 8 //From RTS of Teensy
#define RTS_Pin 7 

void setSerial()
{
    //Initialize Serial1 for communication with Teensy 4.1
    //Set for a lower baud rate & a bit correction
    Serial1.begin(115400,SERIAL_8E1);
    // Serial1.attachCts(CTS_Pin);
    // Serial1.attachRts(RTS_Pin);
    Serial.println("Serial1 initialized for communication with 4.1");
}

void sendSerial(uint8_t buttonNum)
{
    Serial1.write(buttonNum);
    Serial.print("Sending button number to main: ");
    Serial.println(buttonNum);
}

void clearBuffer()
{
    for(uint8_t i = 0; i<=dataBuffer-2; i++)
    {
        data[i] = 0;
    }
}

bool checkIfValid()
{
    for(uint8_t i = 0; i<=dataBuffer-2; i++)
    {
        if(data[i] ==  '\0')
        {
            return false;
        }
        else
        {
            return true;
        }
    }
    return false;    
}

void readSerial()
{
    if (Serial1.available()) 
    {
        //load buffer
        Serial1.readBytesUntil('\0', data,dataBuffer);
        
        Serial.println("Check if packet is valid.");
        bool validPacket = checkIfValid();

        if(validPacket)
        {
            Serial.print("Button: ");
            Serial.println(data[0]);

            for(uint8_t i=0; i<=dataBuffer-2; i++)
            {
                Serial.print(i);
                Serial.print(":");
                Serial.println(data[i]);
            }
        }
        else
        {
            Serial.println("Bad Packet! - Clearing buffer.");
            clearBuffer();
        }
    
        //Serial1.clear();

       
    }


}