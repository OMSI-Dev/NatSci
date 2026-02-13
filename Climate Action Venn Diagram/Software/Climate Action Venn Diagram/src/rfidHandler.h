
/*
Climate Action Venn Diagram
Aaron De Lanty

Handles reading and parsing each RFID.
*/

#include <RFID_B1.h>

#define startPage 5
#define bytesPerPage 4
#define numPagesToRead 1

#define TPI1 2
#define TPI2 3
#define TPI3 4

RFID_B1 communityRFID(Serial4);
RFID_B1 interestRFID(Serial3);
RFID_B1 hobbyRFID(Serial5);

bool checkTPI(uint8_t pin)
{
    bool tempTPI = digitalRead(pin);

    return tempTPI;
}

void startRfidSerial()
{
    communityRFID.begin(9600);
    interestRFID.begin(9600);
    hobbyRFID.begin(9600);

    // We need to wait for all of the Uart signals to connect before moving on.
    if (communityRFID.waitForReady(5000))
    {
        Serial.println("Connected to Community.");
    }
    else
    {
        Serial.println("Did not connect to Community.");
    }

    if (interestRFID.waitForReady(5000))
    {
        Serial.println("Connected to Interest.");
    }
    else
    {
        Serial.println("Did not connect to Interest.");
    }

    if (hobbyRFID.waitForReady(5000))
    {
        Serial.println("Connected to Hobby.");
    }
    else
    {
        Serial.println("Did not connect to Hobby.");
    }
}

void scanForRfid()
{

    if(checkTPI();
}