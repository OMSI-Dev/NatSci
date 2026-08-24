/*
Climate Action Venn Diagram
Aaron De Lanty
2/12/2026

Sets pin modes and their default states.

*/

#define ledData1 8
#define ledData2 9
#define ledData3 10

#define NPWNDN1 5
#define NPWNDN2 6
#define NPWNDN3 7

#define TPI1 3 //Cloud & Topic
#define TPI2 2 //Person & Interest
#define TPI3 4 //House & Group

#define BTN_1_PWM 1

void setPins()
{
    Serial.println("*****************************");
    Serial.println("Set LED Pins");
    // create output for WS2813B LED strip
    pinMode(ledData1, OUTPUT);
    pinMode(ledData2, OUTPUT);
    pinMode(ledData3, OUTPUT);
    pinMode(13, OUTPUT);

    Serial.println("Set RFID PWR Pins");
    // Set power control of the B1 RFID
    pinMode(NPWNDN1, OUTPUT);
    pinMode(NPWNDN2, OUTPUT);
    pinMode(NPWNDN3, OUTPUT);

    Serial.println("Turn on RFID PWR Pins");
    // Turn on all RFID
    digitalWrite(NPWNDN1, HIGH);
    digitalWrite(NPWNDN2, HIGH);
    digitalWrite(NPWNDN3, HIGH);

    Serial.println("Set TPI Pins");
    // Set Tag Presence Indicator
    pinMode(TPI1, INPUT);
    pinMode(TPI2, INPUT);
    pinMode(TPI3, INPUT);

    Serial.println("Set BTN Pins");
    // Set PWM for language button
    pinMode(BTN_1_PWM, OUTPUT);
    Serial.println("*****************************");

}