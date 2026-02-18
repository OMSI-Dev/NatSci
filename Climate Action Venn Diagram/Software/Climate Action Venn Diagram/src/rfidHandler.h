
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

uint16_t rfidTimeout = 5000;

RFID_B1 groupRFID(Serial4);
RFID_B1 interestRFID(Serial3);
RFID_B1 topicRFID(Serial5);

uint8_t specificData[bytesPerPage * numPagesToRead];

uint8_t currentGroupTag, currentInterestTag, currentTopicTag;

/*
Values stored as a hex byte
1-12 for groups
13-24 for interest
25-36 for topics
*/
uint8_t knownTagsGroup[12] =
    {
        '01', '02', '03', '04', '05', '06', '07', '08', '09', '0A', '0B', '0C'};

uint8_t knownTagsInterest[12] =
    {
        '0D', '0E', '0F', '10', '11', '12', '13', '14', '15', '16', '17', '18'};

uint8_t knownTagsInterest[12] =
    {
        '19', '1A', '1B', '1C', '1D', '1E', '1F', '20', '21', '22', '23', '24'};

/**
 * Grabs requested tag
 *
 *@brief Get the current tag for the defined reader
 *
 *@param RFID 1 = group, 2 = interest, 3 = topic
 *@return
 */

u_int8_t getTag(uint8_t RFID = 1)
{
    u_int8_t knownByte = 0;

    switch (RFID)
    {
    case 1:
        if (groupRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
            groupRFID.printBuffer(specificData, sizeof(specificData));
        }
        groupRFID.halt();

        // Import Byte on RFID is the 4th byte of the page
        for (uint8_t i = 0; i < sizeof(knownTagsGroup); i++)
        {
            if (knownTagsGroup[i] == specificData[3])
            {
                knownByte = specificData[3];
                currentGroupTag = specificData[3];
            }
        }
        break;
    case 2:
        /* code */
        break;
    case 3:
        /* code */
        break;
    default:
        break;
    }

    if (knownByte != 0)
    {
        return 0;
    }
    else
    {
        return knownByte;
    }
}

/*
@brief Compare scanned ID and compare to list of known values
*/
bool referenceKnownTags(uint8_t RFID)
{
    uint8_t tagID = getTag(RFID);

    if (tagID != 0)
    {
        return true;
    }
    else
    {
        return false;
    }
}

bool checkTPI(uint8_t pin)
{
    // B1 Module returns a low signal for detecting a tag.
    // Flipping the bool so the logic is easier to follow.
    bool tempTPI = !digitalRead(pin);

    return tempTPI;
}

void startRfidSerial()
{
    groupRFID.begin(9600);
    interestRFID.begin(9600);
    topicRFID.begin(9600);

    // We need to wait for all of the Uart signals to connect before moving on.
    if (groupRFID.waitForReady(rfidTimeout))
    {
        Serial.println("Connected to Community.");
    }
    else
    {
        Serial.println("Did not connect to Community.");
    }

    if (interestRFID.waitForReady(rfidTimeout))
    {
        Serial.println("Connected to Interest.");
    }
    else
    {
        Serial.println("Did not connect to Interest.");
    }

    if (topicRFID.waitForReady(rfidTimeout))
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

    if (checkTPI(TPI1))
    {
        if (referenceKnownTags(1))
        {
            sendTag(currentGroupTag);
        }
    }

    if (checkTPI(TPI2))
    {
    }

    if (checkTPI(TPI3))
    {
    }
}