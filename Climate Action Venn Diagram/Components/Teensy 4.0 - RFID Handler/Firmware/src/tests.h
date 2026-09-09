
bool debugMode, writeMode;

void checkModePins()
{
        delay(50);
        debugMode = !digitalRead(debugPin);
        delay(50);
        writeMode = !digitalRead(writePin);

}