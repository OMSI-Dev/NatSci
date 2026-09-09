// Flag to pause continuous scanning during manual operations
bool pauseScanning = false;

void writeGroup();
void writeTopic();
void writeInterest();

void writeTag()
{
        if (Serial.available())
        {
            char cmd = Serial.read();
            if (cmd == 'w' || cmd == 'W')
            {
                pauseScanning = true; // Pause continuous scanning
                Serial.println("\n=== WRITE RFID ID ===");
                Serial.println("Enter RFID Number (1-3) and press Enter:");
                Serial.println("Interest:1 | Topic: 2 | Group: 3");

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
                        else if ((c >= '0' && c <= '9'))
                        {
                            input += c;
                            Serial.print(c); // Echo the character
                        }
                    }

                }

                Serial.println(); // New line after input

                // Flush any remaining characters from serial buffer (e.g., leftover \n after \r)
                while (Serial.available())
                {
                    Serial.read();
                }
                uint16_t rfidNum = strtol(input.c_str(), NULL, 16);


                switch (rfidNum)
                {
                case 1:
                    writeInterest();
                    break;
                case 2:
                    writeTopic();
                    break;
                case 3:
                    writeGroup();
                    break;                                    
                default:
                    break;
                }

                pauseScanning = false; // Resume continuous scanning
            }
        }
    

}


void writeGroup()
{
    confirmLED(3);
    FastLED.show();
    Serial.println("\n=== WRITE TAG ID ===");
    Serial.print("Enter Group Number (");
    Serial.print(knownTagsGroup[0]);
    Serial.print("-");
    Serial.print(knownTagsGroup[11]);
    Serial.println(") and press Enter:");

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

    }

    if (input.length() > 0)
    {
        uint8_t tagID = input.toInt();

        Serial.print("Writing tag ID 0x");
        if (tagID < 0x10)
            Serial.print("0");
        Serial.print(tagID, HEX);
        Serial.println(" to page 5...");

        // Halt any ongoing operations and reset reader
        groupRFID.halt();


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


            // Prepare data: write the tag ID at byte 3 of page 5
            uint8_t pageData[4] = {0x00, 0x00, 0x00, tagID};

            if (groupRFID.writeNTAG215(5, pageData, 1))
            {
                Serial.println("✓ Write successful!");

                // Verify by reading back

                if (groupRFID.getUIDandType()) // Re-detect tag for reading
                {
                    uint8_t readBack[4];
                    if (groupRFID.readNTAG215(5, 1, readBack))
                    {
                        Serial.print("Verification - Page 5: ");
                        for (int i = 0; i < 4; i++)
                        {
                            if (readBack[i] < 0x10)
                                Serial.print("0");
                            Serial.print(readBack[i], HEX);
                            Serial.print(" ");
                        }
                        Serial.println();

                        if (readBack[3] == tagID)
                        {
                            Serial.println("✓ Verification passed!");
                            groupRFID.lock();
    
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
    confirmLED(4);
    FastLED.show();
}

void writeTopic()
{
    confirmLED(2);
    FastLED.show();
    FastLED.show();
    Serial.println("\n=== WRITE TAG ID ===");
    Serial.print("Enter Topic Number (");
    Serial.print(knownTagsTopic[0]);
    Serial.print("-");
    Serial.print(knownTagsTopic[11]);
    Serial.println(") and press Enter:");

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

    }

    if (input.length() > 0)
    {
        uint8_t tagID = input.toInt();
        Serial.print("Writing tag ID 0x");
        if (tagID < 0x10)
            Serial.print("0");
        Serial.print(tagID, HEX);
        Serial.println(" to page 5...");

        // Halt any ongoing operations and reset reader
        topicRFID.halt();


        // First, ensure tag is detected
        Serial.println("Detecting tag...");
        if (!topicRFID.getUIDandType())
        {
            Serial.println("✗ No tag detected! Place tag on antenna and try again.");
            Serial.print("Result: ");
            Serial.println(topicRFID.getResultName(topicRFID.getLastResult()));
            Serial.println("======================\n");
        }
        else
        {
            Serial.println("✓ Tag detected");


            // Prepare data: write the tag ID at byte 3 of page 5
            uint8_t pageData[4] = {0x00, 0x00, 0x00, tagID};

            if (topicRFID.writeNTAG215(5, pageData, 1))
            {
                Serial.println("✓ Write successful!");

                // Verify by reading back

                if (topicRFID.getUIDandType()) // Re-detect tag for reading
                {
                    uint8_t readBack[4];
                    if (topicRFID.readNTAG215(5, 1, readBack))
                    {
                        Serial.print("Verification - Page 5: ");
                        for (int i = 0; i < 4; i++)
                        {
                            if (readBack[i] < 0x10)
                                Serial.print("0");
                            Serial.print(readBack[i], HEX);
                            Serial.print(" ");
                        }
                        Serial.println();

                        if (readBack[3] == tagID)
                        {
                            Serial.println("✓ Verification passed!");
                            topicRFID.lock();
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
                Serial.println(topicRFID.getResultName(topicRFID.getLastResult()));
            }
            Serial.println("======================\n");
        }
    }
    else
    {
        Serial.println("Invalid input!");
        Serial.println("======================\n");
    }
    confirmLED(4);
    FastLED.show();
}

void writeInterest()
{
    confirmLED(1);
    FastLED.show();
    Serial.println("\n=== WRITE TAG ID ===");
    Serial.print("Enter Interest Number (");
    Serial.print(knownTagsInterest[0]);
    Serial.print("-");
    Serial.print(knownTagsInterest[11]);
    Serial.println(") and press Enter:");

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

    }

    if (input.length() > 0)
    {
        uint8_t tagID = input.toInt();
        Serial.print("Writing tag ID 0x");
        if (tagID < 0x10)
            Serial.print("0");
        Serial.print(tagID, HEX);
        Serial.println(" to page 5...");

        // Halt any ongoing operations and reset reader
        interestRFID.halt();


        // First, ensure tag is detected
        Serial.println("Detecting tag...");
        if (!interestRFID.getUIDandType())
        {
            Serial.println("✗ No tag detected! Place tag on antenna and try again.");
            Serial.print("Result: ");
            Serial.println(interestRFID.getResultName(interestRFID.getLastResult()));
            Serial.println("======================\n");
        }
        else
        {
            Serial.println("✓ Tag detected");


            // Prepare data: write the tag ID at byte 3 of page 5
            uint8_t pageData[4] = {0x00, 0x00, 0x00, tagID};

            if (interestRFID.writeNTAG215(5, pageData, 1))
            {
                Serial.println("✓ Write successful!");

                // Verify by reading back

                if (interestRFID.getUIDandType()) // Re-detect tag for reading
                {
                    uint8_t readBack[4];
                    if (interestRFID.readNTAG215(5, 1, readBack))
                    {
                        Serial.print("Verification - Page 5: ");
                        for (int i = 0; i < 4; i++)
                        {
                            if (readBack[i] < 0x10)
                                Serial.print("0");
                            Serial.print(readBack[i], HEX);
                            Serial.print(" ");
                        }
                        Serial.println();

                        if (readBack[3] == tagID)
                        {
                            Serial.println("✓ Verification passed!");
                            interestRFID.lock();
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
                Serial.println(interestRFID.getResultName(interestRFID.getLastResult()));
            }
            Serial.println("======================\n");
        }
    }
    else
    {
        Serial.println("Invalid input!");
        Serial.println("======================\n");
    }
    confirmLED(4);
    FastLED.show();

    
}