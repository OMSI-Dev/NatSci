const uint8_t dataBuffer = 11;
uint8_t data[dataBuffer];

/*
The following pins need to have an inverted RTS Pin using the modified framework.
 XBAR Pins 1, 2, 3, 4, 5, 7, 8, 30, 31, 32, 33
 */

#define CTS_Pin 8 // From RTS of Teensy
#define RTS_Pin 7

void setSerial()
{
    Serial1.begin(115200, SERIAL_8E1);
    // Serial1.attachCts(CTS_Pin);
    // Serial1.attachRtsInverted(RTS_Pin);
    //This needs to be updated after new mainboard is finished. This only affects row 6
    Serial.println("Serial1 initialized for communication with 4.1");
}

void sendSerial(uint8_t buttonNum)
{
    Serial1.write(buttonNum);
    Serial.print("Sending button ");
    Serial.print(buttonNum);
    Serial.println(" to main.");
}

void clearBuffer()
{
    for (uint8_t i = 0; i < 11; i++)
    {
        data[i] = 0;
    }
}

bool checkIfValid()
{
    // FIX 1&2: just check that data[0] is a valid button number
    // and not an empty buffer
    return (data[0] == '1' || data[0] == '2' || 
            data[0] == '3' || data[0] == '4' || data[0] == '5');
}

void readSerial()
{
    if (Serial1.available())
    {
        uint8_t bytesRead = Serial1.readBytesUntil('\0', data, dataBuffer);

        Serial.println("Check if packet is valid.");

        // FIX 3: also validate we got a reasonable number of bytes
        if (bytesRead < 1)
        {
            Serial.println("Bad Packet! - Empty read.");
            clearBuffer();
            return;
        }

        bool validPacket = checkIfValid();

        if (validPacket)
        {
            Serial.print("Button: ");
            Serial.println(data[0] - '0');
            for (uint8_t i = 0; i < bytesRead; i++)
            {
                Serial.print(i);
                Serial.print(":");
                Serial.print(data[i]);
                Serial.print(" ");
            }
            Serial.println();
        }
        else
        {
            Serial.println("Bad Packet! - Clearing buffer.");
            clearBuffer(); // FIX 1: just clear, don't fake data[0] = '1'
        }
    }
}