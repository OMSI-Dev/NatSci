
bool debugMode, writeMode;

void checkModePins()
{
    debugMode = digitalRead(debugPin);
    delay(50);
    writeMode = digitalRead(writePin);

}