/*
Climate Action Venn Diagram - Simplified Test Version
Handles reading RFID tags for testing purposes.
*/

#include <RFID_B1.h>

#define startPage 5
#define bytesPerPage 4
#define numPagesToRead 1

#define TPI1 2
#define TPI2 3
#define TPI3 4

uint16_t rfidTimeout = 5000;

RFID_B1 groupRFID(Serial3);    // Pins 14(TX3)/15(RX3)
RFID_B1 interestRFID(Serial4); // Pins 16(RX4)/17(TX4)
RFID_B1 topicRFID(Serial5);    // Pins 20(TX5)/21(RX5)

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
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C};

uint8_t knownTagsInterest[12] =
    {
        0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18};

uint8_t knownTagsTopic[12] =
    {
        0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24};

/**
 * Reads tag from specified RFID reader
 * @param RFID 1 = group, 2 = interest, 3 = topic
 * @return Tag byte value if found, 0 if not found
 */
u_int8_t getTag(uint8_t RFID = 1)
{
    u_int8_t knownByte = 0;

    switch (RFID)
    {
    case 1:
        Serial.println("  Calling readNTAG215...");
        if (groupRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
            Serial.println("  ✓ Read successful!");
            Serial.print("  Data buffer: ");
            groupRFID.printBuffer(specificData, sizeof(specificData));
            
            for (uint8_t i = 0; i < sizeof(knownTagsGroup); i++)
            {
                if (knownTagsGroup[i] == specificData[3])
                {
                    knownByte = specificData[3];
                    currentGroupTag = specificData[3];
                    Serial.println("  -> Matched known group tag!");
                    break;
                }
            }
            if (knownByte == 0)
            {
                Serial.print("  -> Tag byte 0x");
                Serial.print(specificData[3], HEX);
                Serial.println(" not in known group tags list");
            }
        }
        else
        {
            Serial.println("  ✗ Read failed (readNTAG215 returned false)");
        }
        groupRFID.halt();
        break;
        
    case 2:
        if (interestRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
            Serial.println("Interest RFID read:");
            interestRFID.printBuffer(specificData, sizeof(specificData));
            
            for (uint8_t i = 0; i < sizeof(knownTagsInterest); i++)
            {
                if (knownTagsInterest[i] == specificData[3])
                {
                    knownByte = specificData[3];
                    currentInterestTag = specificData[3];
                    Serial.println("  -> Matched known interest tag!");
                    break;
                }
            }
        }
        interestRFID.halt();
        break;
        
    case 3:
        if (topicRFID.readNTAG215(startPage, numPagesToRead, specificData))
        {
            Serial.println("Topic RFID read:");
            topicRFID.printBuffer(specificData, sizeof(specificData));
            
            for (uint8_t i = 0; i < sizeof(knownTagsTopic); i++)
            {
                if (knownTagsTopic[i] == specificData[3])
                {
                    knownByte = specificData[3];
                    currentTopicTag = specificData[3];
                    Serial.println("  -> Matched known topic tag!");
                    break;
                }
            }
        }
        topicRFID.halt();
        break;
    default:
        break;
    }

    return knownByte;
}

/**
 * Check if tag is detected and recognized
 */
bool referenceKnownTags(uint8_t RFID)
{
    uint8_t tagID = getTag(RFID);
    return (tagID != 0);
}

/**
 * Check if tag is present on reader
 */
bool checkTPI(uint8_t pin)
{
    // B1 Module returns a low signal for detecting a tag.
    // Flipping the bool so the logic is easier to follow.
    return !digitalRead(pin);
}

/**
 * Initialize all RFID serial connections
 */
void startRfidSerial()
{
    Serial.println("\n=== Initializing RFID Readers ===");
    
    groupRFID.begin(9600);
    Serial.print("Initializing Group RFID on Serial3 (pins 14/15)... ");
    delay(200);
    if (groupRFID.dummyCommand())
    {
        Serial.println("✓ Connected");
    }
    else
    {
        Serial.println("✗ FAILED");
    }
    
    interestRFID.begin(9600);
    Serial.print("Initializing Interest RFID on Serial4 (pins 16/17)... ");
    delay(200);
    if (interestRFID.dummyCommand())
    {
        Serial.println("✓ Connected");
    }
    else
    {
        Serial.println("✗ FAILED");
    }
    
    topicRFID.begin(9600);
    Serial.print("Initializing Topic RFID on Serial5 (pins 20/21)... ");
    delay(200);
    if (topicRFID.dummyCommand())
    {
        Serial.println("✓ Connected");
    }
    else
    {
        Serial.println("✗ FAILED");
    }
    
    Serial.println("\n=== Ready to scan tags ===");
    Serial.println("TPI Pins: 2 (Group), 3 (Interest), 4 (Topic)");
    Serial.println("nPWRDN Pins: 5 (Group), 11 (Interest), 6 (Topic)");
    Serial.println("-----------------------------------------------\n");
}

/**
 * Scan all three RFID readers for tags
 */
void scanForRfid()
{
    static unsigned long lastDebugTime = 0;
    static unsigned long lastScanTime = 0;
    static bool lastTPI1State = true;
    static bool lastTPI2State = true;
    
    // Print TPI status every 5 seconds for debugging
    if (millis() - lastDebugTime > 5000)
    {
        lastDebugTime = millis();
        Serial.print("TPI Status - Pin2:");
        Serial.print(digitalRead(TPI1) ? "HIGH" : "LOW");
        Serial.print(" Pin3:");
        Serial.print(digitalRead(TPI2) ? "HIGH" : "LOW");
        Serial.print(" Pin4:");
        Serial.println(digitalRead(TPI3) ? "HIGH" : "LOW");
    }
    
    // Monitor TPI changes in real-time
    bool currentTPI1 = digitalRead(TPI1);
    if (currentTPI1 != lastTPI1State)
    {
        lastTPI1State = currentTPI1;
        Serial.print(">>> TPI1 changed to: ");
        Serial.println(currentTPI1 ? "HIGH (no tag)" : "LOW (tag present!)");
    }
    
    bool currentTPI2 = digitalRead(TPI2);
    if (currentTPI2 != lastTPI2State)
    {
        lastTPI2State = currentTPI2;
        Serial.print(">>> TPI2 changed to: ");
        Serial.println(currentTPI2 ? "HIGH (no tag)" : "LOW (tag present!)");
    }
    
    // Poll for tags every 500ms (don't rely solely on TPI)
    if (millis() - lastScanTime > 500)
    {
        lastScanTime = millis();
        
        // Check Group RFID (Reader 1) - active polling
        if (groupRFID.getUIDandType())
        {
            Serial.println("\n[Reader 1 - Group] Tag detected!");
            
            // Read the tag data
            if (groupRFID.readNTAG215(startPage, numPagesToRead, specificData))
            {
                Serial.print("  Data: ");
                groupRFID.printBuffer(specificData, sizeof(specificData));
                
                // Check if it matches a known tag
                for (uint8_t i = 0; i < sizeof(knownTagsGroup); i++)
                {
                    if (knownTagsGroup[i] == specificData[3])
                    {
                        currentGroupTag = specificData[3];
                        Serial.print("  -> Matched group tag 0x");
                        if (currentGroupTag < 0x10) Serial.print("0");
                        Serial.println(currentGroupTag, HEX);
                        sendTag(currentGroupTag, 1);
                        break;
                    }
                }
            }
            groupRFID.halt();
            delay(1000); // Wait before next scan to avoid spam
        }
        
        // Check Interest RFID (Reader 2) - active polling
        if (interestRFID.getUIDandType())
        {
            Serial.println("\n[Reader 2 - Interest] Tag detected!");
            
            // Read the tag data
            if (interestRFID.readNTAG215(startPage, numPagesToRead, specificData))
            {
                Serial.print("  Data: ");
                interestRFID.printBuffer(specificData, sizeof(specificData));
                
                // Check if it matches a known tag
                for (uint8_t i = 0; i < sizeof(knownTagsInterest); i++)
                {
                    if (knownTagsInterest[i] == specificData[3])
                    {
                        currentInterestTag = specificData[3];
                        Serial.print("  -> Matched interest tag 0x");
                        if (currentInterestTag < 0x10) Serial.print("0");
                        Serial.println(currentInterestTag, HEX);
                        sendTag(currentInterestTag, 2);
                        break;
                    }
                }
            }
            interestRFID.halt();
            delay(1000); // Wait before next scan to avoid spam
        }
        
        // Check Topic RFID (Reader 3) - active polling
        if (topicRFID.getUIDandType())
        {
            Serial.println("\n[Reader 3 - Topic] Tag detected!");
            
            // Read the tag data
            if (topicRFID.readNTAG215(startPage, numPagesToRead, specificData))
            {
                Serial.print("  Data: ");
                topicRFID.printBuffer(specificData, sizeof(specificData));
                
                // Check if it matches a known tag
                for (uint8_t i = 0; i < sizeof(knownTagsTopic); i++)
                {
                    if (knownTagsTopic[i] == specificData[3])
                    {
                        currentTopicTag = specificData[3];
                        Serial.print("  -> Matched topic tag 0x");
                        if (currentTopicTag < 0x10) Serial.print("0");
                        Serial.println(currentTopicTag, HEX);
                        sendTag(currentTopicTag, 3);
                        break;
                    }
                }
            }
            topicRFID.halt();
            delay(1000); // Wait before next scan to avoid spam
        }
    }
}
