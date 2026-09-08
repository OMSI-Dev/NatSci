/*
Climate Action Venn Diagram - Simplified Test Version
Aaron De Lanty

This simplified version is for testing RFID tag reading.
It will continuously scan all three RFID readers and display results.
*/

#include <Arduino.h>
#include "pins.h"
#include "tests.h"
#include <FastLED.h>
#include <leds.h>
#include "serialHandler.h"
#include "rfidHandler.h"
#include "write.h"

#include <Timer.h>


MoToTimer debugTimer;

MoToTimer rescanGroupTimer, emptySlotGroupTimer;

MoToTimer rescanTopicTimer, emptySlotTopicTimer;

MoToTimer rescanInterestTimer, emptySlotInterestTimer;

bool groupPresence = 0, groupDetected = 0,groupTPI=0;
bool topicPresence = 0, topicDetected = 0,topicTPI=0;
bool interestPresence = 0, interestDetected = 0,interestTPI=0;

uint8_t previousGroupID=200, currentGroupID = 201;
uint8_t previousTopicID=202, currentTopicID = 203;
uint8_t previousInterestID=204, currentInterestID = 205;

uint16_t emptySlotTime = 350, rescanTime = 10000;

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
    


    // Setup pin modes
    setPins();

    //check for special hardware pins
    checkModePins();

    if(debugMode){    
    Serial.println("!!! Pins configured");
    }

    // Initialize RFID readers
    startRfidSerial();

    if(debugMode){ 
    Serial.println("\nCommands:");
    Serial.println("  T - Test read tag on Reader 1 (shows UID and pages 4-8)");
    Serial.println("  W - Write tag ID to page 5 of tag on Reader 1");
    Serial.println("\nPlace RFID tags on readers for automatic scanning...");
    Serial.println("-----------------------------------------------\n");
    }

    // Set LEDS
    setLED();

    groupRFID.stopPolling();
    topicRFID.stopPolling();
    interestRFID.stopPolling();

    delay(50);
    groupPresence = resumeGroupPresenceWatch();
    topicPresence = resumeTopicPresenceWatch();
    interestPresence = resumeInterestPresenceWatch();
    //writeMode = 1;
    //debugMode = 1;
}

void loop()
{
    if(writeMode) {
        if(!debugTimer.running())
        {
            Serial.println("Press 'w' to continue...");
            debugTimer.setTime(5000);
        }
        writeTag();
    }else
    {
        groupCheck();
        topicCheck();
        interestCheck();
        //single update for all LEDs
        FastLED.show();
    }



}


void groupCheck()
{
        //Group Check
    if(groupPresence)
    {
        groupTPI = !digitalRead(TPI3);
        if(debugMode){
        //Serial.print("Group: ");
        //Serial.println(groupTPI);
        }
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
        if(debugMode){
        Serial.println("Tag Detected!");
        }
        groupDetected = true;
        groupRFID.stopPolling();
        currentGroupID = getGroupData();
        
        if(currentGroupID != previousGroupID && currentGroupID != 0)
        {
            previousGroupID = currentGroupID;
            if(debugMode){
            Serial.println("Set LEDs to confirmed");
            }
            confirmLED(3);
            rescanGroupTimer.setTime(rescanTime);
        }
        groupPresence = resumeGroupPresenceWatch();
        emptySlotGroupTimer.setTime(emptySlotTime);
    }


    if(!groupTPI && groupDetected && !emptySlotGroupTimer.running())
    {
        if(debugMode){
        Serial.println("Group Slot is probably empty.");
        }
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
        if(debugMode){        
        Serial.print("Topic: ");
        Serial.println(topicTPI);   
        }
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
        if(debugMode){
        Serial.println("Tag Detected!");
        }
        topicDetected = true;
        topicRFID.stopPolling();
        currentTopicID = getTopicData();
        
        if(currentTopicID != previousTopicID)
        {
            previousTopicID = currentTopicID;
            if(debugMode){
            Serial.println("Set LEDs to confirmed");
            }
            confirmLED(2);
            rescanTopicTimer.setTime(rescanTime);
        }
        topicPresence = resumeTopicPresenceWatch();
        emptySlotTopicTimer.setTime(emptySlotTime);
    }


    if(!topicTPI && topicDetected && !emptySlotTopicTimer.running())
    {
        if(debugMode){
        Serial.println("Group Slot is probably empty.");
        }
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
        if(debugMode){
        Serial.print("Interest: ");
        Serial.println(interestTPI);
        }
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
        if(debugMode){
        Serial.println("Tag Detected!");
        }
        interestDetected = true;
        interestRFID.stopPolling();
        currentInterestID = getInterestData();
        
        if(currentInterestID != previousInterestID)
        {
            previousInterestID = currentInterestID;
            if(debugMode){
            Serial.println("Set LEDs to confirmed");
            }
            confirmLED(1);
            rescanInterestTimer.setTime(rescanTime);
        }
        interestPresence = resumeInterestPresenceWatch();
        emptySlotInterestTimer.setTime(emptySlotTime);
    }

    //check to see if it is the same ID as before
    if(!interestTPI && interestDetected && !emptySlotInterestTimer.running())
    {
        if(debugMode){
        Serial.println("Interest Slot is probably empty.");
        }
        interestDetected = false;
        previousInterestID = 0;
        emptySlotInterestTimer.setTime(emptySlotTime);
    }   

}
