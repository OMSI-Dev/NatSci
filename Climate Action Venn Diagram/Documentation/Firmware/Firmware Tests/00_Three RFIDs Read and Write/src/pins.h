/*
Climate Action Venn Diagram
Aaron De Lanty
2/12/2026

Sets pin modes and their default states.

*/

#define ledData1 10

#define NPWNDN1 5
#define NPWNDN2 11
#define NPWNDN3 6

#define TPI1 2
#define TPI2 3
#define TPI3 4

#define BTN_1_PWM 1

void setPins()
{
    // create output for WS2813B LED strip
    pinMode(ledData1, OUTPUT);

    // Set power control of the B1 RFID
    pinMode(NPWNDN1, OUTPUT);
    pinMode(NPWNDN2, OUTPUT);
    pinMode(NPWNDN3, OUTPUT);

    // Turn on all RFID
    digitalWrite(NPWNDN1, HIGH);
    digitalWrite(NPWNDN2, HIGH);
    digitalWrite(NPWNDN3, HIGH);

    // Set Tag Presence Indicator
    pinMode(TPI1, INPUT_PULLUP);
    pinMode(TPI2, INPUT_PULLUP);
    pinMode(TPI3, INPUT_PULLUP);

    // Set PWM for language button
    pinMode(BTN_1_PWM, OUTPUT);
}