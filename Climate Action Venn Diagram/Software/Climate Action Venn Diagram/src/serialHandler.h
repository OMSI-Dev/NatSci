

/**
 * 
 * Sends a found tag to software to
 * 
 * 
 */
void sendTag(uint8_t currentTag, uint8_t category)
{
    Serial.print(category);
    Serial.print(currentTag);
    Serial.print('/n');
}