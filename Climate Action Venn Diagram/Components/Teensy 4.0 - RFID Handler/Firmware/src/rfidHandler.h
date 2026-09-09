/*
Climate Action Venn Diagram - Simplified Test Version
Handles reading RFID tags for testing purposes.
*/

#include <RFID_B1.h>

#define startPage 5
#define bytesPerPage 4
#define numPagesToRead 1

uint16_t rfidTimeout = 5000;

RFID_B1 interestRFID(Serial3);    // Pins 14(TX3)/15(RX3) TPI Pin: 3
RFID_B1 topicRFID(Serial4); // Pins 16(RX4)/17(TX4) TPI Pin: 2
RFID_B1 groupRFID(Serial5);    // Pins 20(TX5)/21(RX5) TPI Pin: 4

uint8_t specificData[bytesPerPage * numPagesToRead];

uint8_t currentGroupTag, currentInterestTag, currentTopicTag;

/*
Values stored as a hex byte
1-12 for interst
13-24 for topics
25-36 for groups
*/

uint8_t knownTagsInterest[12] =
    {
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C};

const uint8_t knownTagsTopic[12] =
    {
        0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18};

const uint8_t knownTagsGroup[12] =
    {
        0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24};

/**
 * Initialize all RFID serial connections
 */
void startRfidSerial()
{           
    if(debugMode){ 
    Serial.println("\n=== Initializing RFID Readers ===");
    }
    groupRFID.begin(9600);
    if(debugMode){ 
    Serial.print("Initializing Group RFID on Serial3 (pins 14/15)... ");
    }
    delay(200);
    if (groupRFID.dummyCommand())
    {   
                if(debugMode){ 
        Serial.println("✓ Connected");
        }
    }
    else
    {
                if(debugMode){ 
        Serial.println("✗ FAILED");
        }
    }
    
    interestRFID.begin(9600);
            if(debugMode){ 
    Serial.print("Initializing Interest RFID on Serial4 (pins 16/17)... ");
    }
    delay(200);
    if (interestRFID.dummyCommand())
    {
                if(debugMode){ 
        Serial.println("✓ Connected");
        }
    }
    else
    {
                if(debugMode){ 
        Serial.println("✗ FAILED");
        }
    }
    
    topicRFID.begin(9600);
            if(debugMode){ 
    Serial.print("Initializing Topic RFID on Serial5 (pins 20/21)... ");
    }
    delay(200);
    if (topicRFID.dummyCommand())
    {
                if(debugMode){ 
        Serial.println("✓ Connected");
        }
    }
    else
    {
                if(debugMode){ 
        Serial.println("✗ FAILED");
        }
    }
        
}

uint8_t getGroupData()
{
    if (groupRFID.getUIDandType())
    {
        // Read the tag data
        if (groupRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
            if(debugMode){
            Serial.print("Group Tag Read: ");
            groupRFID.printBuffer(specificData, sizeof(specificData));
            }
            // Check if it matches a known tag
            for( uint8_t i = 0; i < sizeof(knownTagsGroup); i++)
            {
                if(debugMode){
                Serial.println("Checking tag against:");
                Serial.println(knownTagsGroup[i]);
                }
                if (knownTagsGroup[i] == specificData[3])
                {
                    currentGroupTag = specificData[3];
                    if(debugMode){
                    Serial.print("  -> Matched group tag 0x");
        
                    if (currentGroupTag < 0x10) Serial.print("0");
                    Serial.println(currentGroupTag, HEX);
                    }
                    sendTag(currentGroupTag, 3);
                    return currentGroupTag;
                }      
            }

        }
        
    }
    return currentGroupTag=0;
}

uint8_t getTopicData()
{
    if (topicRFID.getUIDandType())
    {
        // Read the tag data
        if (topicRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
            if(debugMode){            
            Serial.print("Topic Data: ");
            topicRFID.printBuffer(specificData, sizeof(specificData));
            }
            // Check if it matches a known tag
            for( uint8_t i = 0; i < sizeof(knownTagsTopic); i++)
            {
                if (knownTagsTopic[i] == specificData[3])
                {
                    currentTopicTag = specificData[3];
                    if(debugMode){
                    Serial.print("  -> Matched group tag 0x");
                    
                    if (currentTopicTag < 0x10) Serial.print("0");
                    Serial.println(currentTopicTag, HEX);
                    }
                    sendTag(currentTopicTag, 2);
                }
            }
        }
        
    }
    return currentTopicTag;
}


uint8_t getInterestData()
{
    if (interestRFID.getUIDandType())
    {
        // Read the tag data
        if (interestRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
                        if(debugMode){
            Serial.print("Interest Data: ");
            interestRFID.printBuffer(specificData, sizeof(specificData));
                        }
            // Check if it matches a known tag
            for( uint8_t i = 0; i < sizeof(knownTagsInterest); i++)
            {
                if (knownTagsInterest[i] == specificData[3])
                {
                    currentInterestTag = specificData[3];
                    if(debugMode){
                    Serial.print("  -> Matched group tag 0x");
                    
                    if (currentInterestTag < 0x10) Serial.print("0");
                    Serial.println(currentInterestTag, HEX);
                    }
                    sendTag(currentInterestTag, 1);
                }
            }
        }
        
    }
    return currentInterestTag;
}


/*
Presence watch to turn on polling on the RFID B1's
*/

bool resumeGroupPresenceWatch() {
    for (uint8_t attempt = 0; attempt < 3; attempt++) {
        if (groupRFID.startPresenceWatch(1)) {
                    if(debugMode){ 
            Serial.println("Started Group Presence Watch.");
            }
            return true;
        }
                if(debugMode){ 
        Serial.println("startPresenceWatch for group failed, retrying...");
        }
    }
            if(debugMode){ 
    Serial.println("!!! startPresenceWatch for group failed after 3 attempts - presence sensing is down");
    }
    return false;
}

bool resumeTopicPresenceWatch() {
    for (uint8_t attempt = 0; attempt < 3; attempt++) {
        if (topicRFID.startPresenceWatch(1)) {
                    if(debugMode){ 
            Serial.println("Started Topic Presence Watch.");
            }
            return true;
        }
                if(debugMode){ 
        Serial.println("startPresenceWatch for Topic failed, retrying...");
        }
    }
            if(debugMode){ 
    Serial.println("!!! startPresenceWatch for Topic failed after 3 attempts - presence sensing is down");
    }
    return false;
}

bool resumeInterestPresenceWatch() {
    for (uint8_t attempt = 0; attempt < 3; attempt++) {
        if (interestRFID.startPresenceWatch(1)) {
                    if(debugMode){ 
            Serial.println("Started Interest Presence Watch.");
            }
            return true;
        }
                if(debugMode){ 
        Serial.println("startPresenceWatch for Interest failed, retrying...");
        }
    }
            if(debugMode){ 
    Serial.println("!!! startPresenceWatch for Interest failed after 3 attempts - presence sensing is down");
    }
    return false;
}