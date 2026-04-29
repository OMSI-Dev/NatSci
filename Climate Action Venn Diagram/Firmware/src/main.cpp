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

// Flag to pause continuous scanning during manual operations
bool pauseScanning = false;

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
    Serial.println("✓ Pins configured");
    
    // Initialize RFID readers
    startRfidSerial();
    
    Serial.println("\nCommands:");
    Serial.println("  T - Test read tag on Reader 1 (shows UID and pages 4-8)");
    Serial.println("  W - Write tag ID to page 5 of tag on Reader 1");
    Serial.println("\nPlace RFID tags on readers for automatic scanning...");
    Serial.println("-----------------------------------------------\n");
}

void loop()
{
    // Check for manual test command
    if (Serial.available())
    {
        char cmd = Serial.read();
        if (cmd == 't' || cmd == 'T')
        {
            pauseScanning = true;  // Pause continuous scanning
            Serial.println("\n=== MANUAL TAG TEST ===");
            Serial.println("Attempting forced read on Group RFID...");
            
            // Halt any ongoing operations
            groupRFID.halt();
            delay(100);
            
            // Try to get UID and type
            if (groupRFID.getUIDandType())
            {
                Serial.println("✓ Tag detected!");
                Serial.print("Tag Type: ");
                Serial.println(groupRFID.getTagTypeName(groupRFID.getTagType()));
                
                uint8_t uid[10];
                uint8_t uidSize;
                if (groupRFID.getTagUID(uid, uidSize))
                {
                    Serial.print("UID: ");
                    groupRFID.printUID(uid, uidSize);
                }
                
                // Read pages 4-8 to see if there's any data
                Serial.println("\nReading pages 4-8:");
                uint8_t pageData[20]; // 5 pages x 4 bytes
                if (groupRFID.readNTAG215(4, 5, pageData))
                {
                    for (uint8_t i = 0; i < 5; i++)
                    {
                        Serial.print("  Page ");
                        Serial.print(4 + i);
                        Serial.print(": ");
                        for (uint8_t j = 0; j < 4; j++)
                        {
                            if (pageData[i*4 + j] < 0x10) Serial.print("0");
                            Serial.print(pageData[i*4 + j], HEX);
                            Serial.print(" ");
                        }
                        Serial.println();
                    }
                }
            }
            else
            {
                Serial.println("✗ No tag detected");
                Serial.print("Result: ");
                Serial.println(groupRFID.getResultName(groupRFID.getLastResult()));
            }
            Serial.println("======================\n");
            pauseScanning = false;  // Resume continuous scanning
        }
        else if (cmd == 'w' || cmd == 'W')
        {
            pauseScanning = true;  // Pause continuous scanning
            Serial.println("\n=== WRITE TAG ID ===");
            Serial.println("Enter tag ID (hex, 01-24) and press Enter:");
            
            // Wait for user input with newline
            String input = "";
            bool inputComplete = false;
            
            while (!inputComplete)
            {
                if (Serial.available())
                {
                    char c = Serial.read();
                    
                    if (c == '\n' || c == '\r')
                    {
                        inputComplete = true;
                    }
                    else if ((c >= '0' && c <= '9') || (c >= 'A' && c <= 'F') || (c >= 'a' && c <= 'f'))
                    {
                        input += c;
                        Serial.print(c); // Echo the character
                    }
                }
                delay(10);
            }
            Serial.println(); // New line after input
            
            // Flush any remaining characters from serial buffer (e.g., leftover \n after \r)
            while (Serial.available())
            {
                Serial.read();
            }
            
            if (input.length() > 0)
            {
                uint8_t tagID = strtol(input.c_str(), NULL, 16);
                Serial.print("Writing tag ID 0x");
                if (tagID < 0x10) Serial.print("0");
                Serial.print(tagID, HEX);
                Serial.println(" to page 5...");
                
                // Halt any ongoing operations and reset reader
                groupRFID.halt();
                delay(100);
                
                // First, ensure tag is detected
                Serial.println("Detecting tag...");
                if (!groupRFID.getUIDandType())
                {
                    Serial.println("✗ No tag detected! Place tag on antenna and try again.");
                    Serial.print("Result: ");
                    Serial.println(groupRFID.getResultName(groupRFID.getLastResult()));
                    Serial.println("======================\n");
                }
                else
                {
                    Serial.println("✓ Tag detected");
                    delay(50);
                    
                    // Prepare data: write the tag ID at byte 3 of page 5
                    uint8_t pageData[4] = {0x00, 0x00, 0x00, tagID};
                    
                    if (groupRFID.writeNTAG215(5, pageData, 1))
                    {
                        Serial.println("✓ Write successful!");
                        
                        // Verify by reading back
                        delay(100);
                        if (groupRFID.getUIDandType())  // Re-detect tag for reading
                        {
                            uint8_t readBack[4];
                            if (groupRFID.readNTAG215(5, 1, readBack))
                            {
                                Serial.print("Verification - Page 5: ");
                                for (int i = 0; i < 4; i++)
                                {
                                    if (readBack[i] < 0x10) Serial.print("0");
                                    Serial.print(readBack[i], HEX);
                                    Serial.print(" ");
                                }
                                Serial.println();
                                
                                if (readBack[3] == tagID)
                                {
                                    Serial.println("✓ Verification passed!");
                                }
                                else
                                {
                                    Serial.println("✗ Verification failed - data mismatch!");
                                }
                            }
                        }
                    }
                    else
                    {
                        Serial.println("✗ Write failed!");
                        Serial.print("Result: ");
                        Serial.println(groupRFID.getResultName(groupRFID.getLastResult()));
                    }
                    Serial.println("======================\n");
                }
            }
            else
            {
                Serial.println("Invalid input!");
                Serial.println("======================\n");
            }
            pauseScanning = false;  // Resume continuous scanning
        }
    }
    
    // Continuously scan for RFID tags (only if not paused)
    if (!pauseScanning)
    {
        scanForRfid();
    }
    
    // Small delay to prevent overwhelming the serial output
    delay(100);
}
