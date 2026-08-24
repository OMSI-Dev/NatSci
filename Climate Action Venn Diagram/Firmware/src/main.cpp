/*
Climate Action Venn Diagram - Simplified Test Version
Aaron De Lanty

This simplified version is for testing RFID tag reading.
It will continuously scan all three RFID readers and display results.
*/

#include <Arduino.h>
#include "pins.h"
#include "serialHandler.h"
#include "rfidHandler.h"
#include <FastLED.h>
#include <leds.h>
#include "tests.h"
#include <Timer.h>

// Flag to pause continuous scanning during manual operations
bool pauseScanning = false;

MoToTimer debug;

MoToTimer rescanGroupTimer, emptySlotGroupTimer;

MoToTimer rescanTopicTimer, emptySlotTopicTimer;

MoToTimer rescanInterestTimer, emptySlotInterestTimer;

bool groupPresence = 0, groupDetected = 0,groupTPI=0;
bool topicPresence = 0, topicDetected = 0,topicTPI=0;
bool interestPresence = 0, interestDetected = 0,interestTPI=0;

uint8_t previousGroupID=200, currentGroupID = 201;
uint8_t previousTopicID=202, currentTopicID = 203;
uint8_t previousInterestID=204, currentInterestID = 205;

uint16_t emptySlotTime = 250, rescanTime = 10000;

void groupCheck(); //House
void groupCheckSet(); //House
void groupCheckScan(); //House

void topicCheck(); //Cloud
void interestCheck(); //person

void setup()
{
    // Initialize serial communication
    Serial.begin(115200);
    while (!Serial)
    {
        ; // Wait for serial port to connect
    }

    Serial.println("\n\n");
    Serial.println("===============================================");
    Serial.println("  Climate Action Venn Diagram - RFID Test");
    Serial.println("===============================================");

    // Setup pin modes
    setPins();
    Serial.println("!!! Pins configured");

    // Initialize RFID readers
    startRfidSerial();

    Serial.println("\nCommands:");
    Serial.println("  T - Test read tag on Reader 1 (shows UID and pages 4-8)");
    Serial.println("  W - Write tag ID to page 5 of tag on Reader 1");
    Serial.println("\nPlace RFID tags on readers for automatic scanning...");
    Serial.println("-----------------------------------------------\n");

    // Set LEDS
    setLED();

    groupRFID.stopPolling();
    topicRFID.stopPolling();
    interestRFID.stopPolling();
    delay(50);
    groupPresence = resumeGroupPresenceWatch();
    topicPresence = resumeTopicPresenceWatch();
    interestPresence = resumeInterestPresenceWatch();
}

void loop()
{
    // if(!debug.running())
    // {
    //     Serial.print("Group Dectected: ");
    //     Serial.println(groupDetected);
    //     Serial.print("GroupTPI: ");
    //     Serial.println(groupTPI);
    //     Serial.println("---------------");        
    //     Serial.print("Topic Dectected: ");
    //     Serial.println(topicDetected);
    //     Serial.print("Topic TPI: ");
    //     Serial.println(topicTPI);
    //     Serial.println("---------------");  
    //     Serial.println("==============================");
    //     debug.setTime(2000);
    // }

    groupCheck();
    topicCheck();
    interestCheck();

}


void groupCheck()
{
        //Group Check
    if(groupPresence)
    {
        groupTPI = !digitalRead(TPI3);
        Serial.print("Group: ");
        Serial.println(groupTPI);
        if(groupTPI)
        {
            emptySlotGroupTimer.setTime(emptySlotTime);
        }
    }

    if(!groupDetected && !groupTPI)
    {
        scanLED(3);
    }

    if(groupTPI && !groupDetected)
    {
        Serial.println("Tag Detected!");
        groupDetected = true;
        groupRFID.stopPolling();
        currentGroupID = getGroupData();
        
        if(currentGroupID != previousGroupID)
        {
            previousGroupID = currentGroupID;
            Serial.println("Set LEDs to confirmed");
            confirmLED(3);
            rescanGroupTimer.setTime(rescanTime);
        }
        groupPresence = resumeGroupPresenceWatch();
        emptySlotGroupTimer.setTime(emptySlotTime);
    }


    if(!groupTPI && groupDetected && !emptySlotGroupTimer.running())
    {
        Serial.println("Group Slot is probably empty.");
        groupDetected = false;
        previousGroupID = 0;
        emptySlotGroupTimer.setTime(emptySlotTime);
    }

}

void topicCheck()
{
        //Group Check
    if(topicPresence)
    {
        topicTPI = !digitalRead(TPI2);
        Serial.print("Topic: ");
        Serial.println(topicTPI);   

        if(topicTPI)
        {
            emptySlotTopicTimer.setTime(emptySlotTime);
        }
    }

    if(!topicDetected && !topicTPI)
    {
        scanLED(2);
    }

    if(topicTPI && !topicDetected)
    {
        Serial.println("Tag Detected!");
        topicDetected = true;
        topicRFID.stopPolling();
        currentTopicID = getTopicData();
        
        if(currentTopicID != previousTopicID)
        {
            previousTopicID = currentTopicID;
            Serial.println("Set LEDs to confirmed");
            confirmLED(2);
            rescanTopicTimer.setTime(rescanTime);
        }
        topicPresence = resumeTopicPresenceWatch();
        emptySlotTopicTimer.setTime(emptySlotTime);
    }


    if(!topicTPI && topicDetected && !emptySlotTopicTimer.running())
    {
        Serial.println("Group Slot is probably empty.");
        topicDetected = false;
        previousTopicID = 0;
        emptySlotTopicTimer.setTime(emptySlotTime);
    }    

}


void interestCheck()
{
        //Group Check
    if(interestPresence)
    {
        interestTPI = !digitalRead(TPI1);
        Serial.print("Interest: ");
        Serial.println(interestTPI);
        if(interestTPI)
        {
            emptySlotInterestTimer.setTime(emptySlotTime);
        }
    }

    if(!interestDetected && !interestTPI)
    {
        scanLED(1);
    }

    if(interestTPI && !interestDetected)
    {
        Serial.println("Tag Detected!");
        interestDetected = true;
        interestRFID.stopPolling();
        currentInterestID = getInterestData();
        
        if(currentInterestID != previousInterestID)
        {
            previousInterestID = currentInterestID;
            Serial.println("Set LEDs to confirmed");
            confirmLED(1);
            rescanInterestTimer.setTime(rescanTime);
        }
        interestPresence = resumeInterestPresenceWatch();
        emptySlotInterestTimer.setTime(emptySlotTime);
    }

    //check to see if it is the same ID as before
    if(!interestTPI && interestDetected && !emptySlotInterestTimer.running())
    {
        Serial.println("Interest Slot is probably empty.");
        interestDetected = false;
        previousInterestID = 0;
        emptySlotInterestTimer.setTime(emptySlotTime);
    }   

}


//    // Check for manual test command
//     if (Serial.available())
//     {
//         char cmd = Serial.read();
//         if (cmd == 't' || cmd == 'T')
//         {
//             pauseScanning = true; // Pause continuous scanning
//             Serial.println("\n=== MANUAL TAG TEST ===");
//             Serial.println("Attempting forced read on Group RFID...");

//             // Halt any ongoing operations
//             groupRFID.halt();

//             // Try to get UID and type
//             if (groupRFID.getUIDandType())
//             {
//                 Serial.println("✓ Tag detected!");
//                 Serial.print("Tag Type: ");
//                 Serial.println(groupRFID.getTagTypeName(groupRFID.getTagType()));

//                 uint8_t uid[10];
//                 uint8_t uidSize;
//                 if (groupRFID.getTagUID(uid, uidSize))
//                 {
//                     Serial.print("UID: ");
//                     groupRFID.printUID(uid, uidSize);
//                 }

//                 // Read pages 4-8 to see if there's any data
//                 Serial.println("\nReading pages 4-8:");
//                 uint8_t pageData[20]; // 5 pages x 4 bytes
//                 if (groupRFID.readNTAG215(4, 5, pageData))
//                 {
//                     for (uint8_t i = 0; i < 5; i++)
//                     {
//                         Serial.print("  Page ");
//                         Serial.print(4 + i);
//                         Serial.print(": ");
//                         for (uint8_t j = 0; j < 4; j++)
//                         {
//                             if (pageData[i * 4 + j] < 0x10)
//                                 Serial.print("0");
//                             Serial.print(pageData[i * 4 + j], HEX);
//                             Serial.print(" ");
//                         }
//                         Serial.println();
//                     }
//                 }
//             }
//             else
//             {
//                 Serial.println("✗ No tag detected");
//                 Serial.print("Result: ");
//                 Serial.println(groupRFID.getResultName(groupRFID.getLastResult()));
//             }
//             Serial.println("======================\n");
//             pauseScanning = false; // Resume continuous scanning
//         }
//         else if (cmd == 'w' || cmd == 'W')
//         {
//             pauseScanning = true; // Pause continuous scanning
//             Serial.println("\n=== WRITE TAG ID ===");
//             Serial.println("Enter tag ID (hex, 01-24) and press Enter:");

//             // Wait for user input with newline
//             String input = "";
//             bool inputComplete = false;

//             while (!inputComplete)
//             {
//                 if (Serial.available())
//                 {
//                     char c = Serial.read();

//                     if (c == '\n' || c == '\r')
//                     {
//                         inputComplete = true;
//                     }
//                     else if ((c >= '0' && c <= '9') || (c >= 'A' && c <= 'F') || (c >= 'a' && c <= 'f'))
//                     {
//                         input += c;
//                         Serial.print(c); // Echo the character
//                     }
//                 }

//             }
//             Serial.println(); // New line after input

//             // Flush any remaining characters from serial buffer (e.g., leftover \n after \r)
//             while (Serial.available())
//             {
//                 Serial.read();
//             }

//             if (input.length() > 0)
//             {
//                 uint8_t tagID = strtol(input.c_str(), NULL, 16);
//                 Serial.print("Writing tag ID 0x");
//                 if (tagID < 0x10)
//                     Serial.print("0");
//                 Serial.print(tagID, HEX);
//                 Serial.println(" to page 5...");

//                 // Halt any ongoing operations and reset reader
//                 groupRFID.halt();


//                 // First, ensure tag is detected
//                 Serial.println("Detecting tag...");
//                 if (!groupRFID.getUIDandType())
//                 {
//                     Serial.println("✗ No tag detected! Place tag on antenna and try again.");
//                     Serial.print("Result: ");
//                     Serial.println(groupRFID.getResultName(groupRFID.getLastResult()));
//                     Serial.println("======================\n");
//                 }
//                 else
//                 {
//                     Serial.println("✓ Tag detected");


//                     // Prepare data: write the tag ID at byte 3 of page 5
//                     uint8_t pageData[4] = {0x00, 0x00, 0x00, tagID};

//                     if (groupRFID.writeNTAG215(5, pageData, 1))
//                     {
//                         Serial.println("✓ Write successful!");

//                         // Verify by reading back

//                         if (groupRFID.getUIDandType()) // Re-detect tag for reading
//                         {
//                             uint8_t readBack[4];
//                             if (groupRFID.readNTAG215(5, 1, readBack))
//                             {
//                                 Serial.print("Verification - Page 5: ");
//                                 for (int i = 0; i < 4; i++)
//                                 {
//                                     if (readBack[i] < 0x10)
//                                         Serial.print("0");
//                                     Serial.print(readBack[i], HEX);
//                                     Serial.print(" ");
//                                 }
//                                 Serial.println();

//                                 if (readBack[3] == tagID)
//                                 {
//                                     Serial.println("✓ Verification passed!");
//                                 }
//                                 else
//                                 {
//                                     Serial.println("✗ Verification failed - data mismatch!");
//                                 }
//                             }
//                         }
//                     }
//                     else
//                     {
//                         Serial.println("✗ Write failed!");
//                         Serial.print("Result: ");
//                         Serial.println(groupRFID.getResultName(groupRFID.getLastResult()));
//                     }
//                     Serial.println("======================\n");
//                 }
//             }
//             else
//             {
//                 Serial.println("Invalid input!");
//                 Serial.println("======================\n");
//             }
//             pauseScanning = false; // Resume continuous scanning
//         }
//     }

//     // Continuously scan for RFID tags (only if not paused)
//     if (!pauseScanning)
//     {
//         scanForRfid();
//     }

//     //Small delay to prevent overwhelming the serial output
// }
