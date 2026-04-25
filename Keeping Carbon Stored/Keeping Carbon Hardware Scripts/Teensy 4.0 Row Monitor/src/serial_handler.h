
#define CTS_Pin 7
#define RTS_Pin 8

void setSerial()
{
    //Initialize Serial1 for communication with Teensy 4.1
    //Set for a lower baud rate & a bit correction
    Serial1.begin(9600,SERIAL_8E1);
    Serial1.attachCts(CTS_Pin);
    Serial1.attachRts(RTS_Pin);
    Serial.println("Serial1 initialized for communication with 4.1");
}

void sendSerial()
{

}