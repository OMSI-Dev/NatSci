/*
Climate Action Venn Diagram - Simplified Test Version
Sends tag data over serial for testing
*/

void sendTag(uint8_t currentTag, uint8_t category)
{
    Serial.print(category);
    Serial.print(":0x");
    Serial.print(currentTag, HEX);
    Serial.println();
}