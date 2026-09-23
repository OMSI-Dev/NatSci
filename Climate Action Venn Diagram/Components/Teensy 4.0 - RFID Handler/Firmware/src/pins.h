/*
Climate Action Venn Diagram
Aaron De Lanty
2/12/2026

Sets pin modes and their default states.

*/

#define ledData1 8
#define ledData2 9
#define ledData3 10

#define NPWNDN1 7 //interest
#define NPWNDN2 5
#define NPWNDN3 6

#define TPI1 3 //Cloud & Topic
#define TPI2 2 //Person & Interest
#define TPI3 4 //House & Group

#define BTN_1_PWM 1
#define langPin 0

#define debugPin 22
#define writePin 23

Bounce2::Button langButton = Bounce2::Button();

void setModePins()
{
    pinMode(debugPin,INPUT_PULLUP);
    pinMode(writePin,INPUT_PULLUP);
}

void setPins()
{
    #ifdef DEBUG    
    Serial.println("*****************************");
    Serial.println("Set LED Pins");
    #endif
    // create output for WS2813B LED strip
    pinMode(ledData1, OUTPUT);
    pinMode(ledData2, OUTPUT);
    pinMode(ledData3, OUTPUT);
    pinMode(13, OUTPUT);

    #ifdef DEBUG    
    Serial.println("Set RFID PWR Pins");
    #endif
    // Set power control of the B1 RFID
    pinMode(NPWNDN1, OUTPUT);
    pinMode(NPWNDN2, OUTPUT);
    pinMode(NPWNDN3, OUTPUT);
    #ifdef DEBUG    
    Serial.println("Turn on RFID PWR Pins");
    #endif

    // Turn set power to low incase of reboot
    digitalWrite(NPWNDN1, LOW);
    digitalWrite(NPWNDN2, LOW);
    digitalWrite(NPWNDN3, LOW);
    delay(500);
    // Turn on all RFID
    digitalWrite(NPWNDN1, HIGH);
    digitalWrite(NPWNDN2, HIGH);
    digitalWrite(NPWNDN3, HIGH);

    #ifdef DEBUG    
    Serial.println("Set TPI Pins");
    #endif

    // Set Tag Presence Indicator
    pinMode(TPI1, INPUT);
    pinMode(TPI2, INPUT);
    pinMode(TPI3, INPUT);
    
    pinMode(BTN_1_PWM, OUTPUT);

    langButton.attach(langPin, INPUT_PULLUP);
    langButton.setPressedState(LOW);
    langButton.interval(5);

    #ifdef DEBUG    
    Serial.println("Set BTN Pins");
    Serial.println("*****************************");
    #endif

}