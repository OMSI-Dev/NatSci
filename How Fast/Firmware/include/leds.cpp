/*
 * Calico Rose
 * January 2026
 * LED reaction to ToF
 */

#include <Arduino.h>
#include <FastLED.h>

// *********************** UPPER LED RINGS ***********************
// Declare the data pin, the number of LEDs in each ring,
// and the total number of LEDs across all the upper LED rings.
// Will probably just be one #define that works for sectioning all,
// because they should all be the same amount. ie #define UPPER_RING_SECTION or RING_SECTION
// as the lower ones should use the same amount per section as well.
// Then to access a specific section, it would be ie RING_SECTION*2.
#define LED_UPPER_RING_PIN 0
#define UPPER_RING0 10
#define UPPER_RING1 10
#define UPPER_RING2 10
#define UPPER_RING3 10
#define UPPER_RING4 10
#define UPPER_RING5 10
#define UPPER_RING6 10
#define UPPER_RING7 10
#define UPPER_RING8 10
#define UPPER_RING9 10
#define TOTAL_UPPER_LED (UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4 + UPPER_RING5 + UPPER_RING6 + UPPER_RING7 + UPPER_RING8 + UPPER_RING9)

// Define the array of LEDs for the upper LED rings.
CRGBArray<TOTAL_UPPER_LED> ledUpperRings;

CRGB *topRing0 = &ledUpperRings[0];
CRGB *topRing1 = &ledUpperRings[UPPER_RING0];
CRGB *topRing2 = &ledUpperRings[UPPER_RING0 + UPPER_RING1];
CRGB *topRing3 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2];
CRGB *topRing4 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3];
CRGB *topRing5 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4];
CRGB *topRing6 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4 + UPPER_RING5];
CRGB *topRing7 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4 + UPPER_RING5 + UPPER_RING6];
CRGB *topRing8 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4 + UPPER_RING5 + UPPER_RING6 + UPPER_RING7];
CRGB *topRing9 = &ledUpperRings[UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4 + UPPER_RING5 + UPPER_RING6 + UPPER_RING7 + UPPER_RING8];

// *********************** LOWER LED RINGS ***********************
// Declare the data pin, the number of LEDs in each ring,
// and the total number of LEDs across all the upper LED rings.
// Will probably just be one #define that works for sectioning all,
// because they should all be the same amount. ie #define UPPER_RING_SECTION or RING_SECTION
// as the lower ones should use the same amount per section as well.
// Then to access a specific section, it would be ie RING_SECTION*2.
#define LED_LOW_RING_PIN 0
#define LOW_RING0 10
#define LOW_RING1 10
#define LOW_RING2 10
#define LOW_RING3 10
#define LOW_RING4 10
#define LOW_RING5 10
#define LOW_RING6 10
#define LOW_RING7 10
#define LOW_RING8 10
#define LOW_RING9 10
#define TOTAL_LOWER_LED (LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4 + LOW_RING5 + LOW_RING6 + LOW_RING7 + LOW_RING8 + LOW_RING9)

// Define the array of LEDs for the red graph strip.
CRGBArray<TOTAL_LOWER_LED> ledLowerRings;

CRGB *lowRing0 = &ledLowerRings[0];
CRGB *lowRing1 = &ledLowerRings[LOW_RING0];
CRGB *lowRing2 = &ledLowerRings[LOW_RING0 + LOW_RING1];
CRGB *lowRing3 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2];
CRGB *lowRing4 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3];
CRGB *lowRing5 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4];
CRGB *lowRing6 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4 + LOW_RING5];
CRGB *lowRing7 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4 + LOW_RING5 + LOW_RING6];
CRGB *lowRing8 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4 + LOW_RING5 + LOW_RING6 + LOW_RING7];
CRGB *lowRing9 = &ledLowerRings[LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4 + LOW_RING5 + LOW_RING6 + LOW_RING7 + LOW_RING8];

// *********************** LED STRIP (GRAPH) ***********************
// Declare the LED strip data pin and amount of LEDs in each section along with the total.
// This stip is the big red graph strip.
#define LED_STRIP_PIN 7
#define NUM_STRIP_SECTION0 10
#define NUM_STRIP_SECTION1 10
#define NUM_STRIP_SECTION2 10
#define NUM_STRIP_SECTION3 10
#define NUM_STRIP_SECTION4 10
#define NUM_STRIP_SECTION5 10
#define NUM_STRIP_SECTION6 10
#define NUM_STRIP_SECTION7 10
#define NUM_STRIP_SECTION8 10
#define NUM_STRIP_SECTION9 10
#define TOTAL_LED_STRIP (NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3 + NUM_STRIP_SECTION4 + NUM_STRIP_SECTION5 + NUM_STRIP_SECTION6 + NUM_STRIP_SECTION7 + NUM_STRIP_SECTION8 + NUM_STRIP_SECTION9)

// Define the array of LEDs for the red graph strip.
CRGBArray<TOTAL_LED_STRIP> ledStrip;

CRGB *section0Array = &ledStrip[0];
CRGB *section1Array = &ledStrip[NUM_STRIP_SECTION0];
CRGB *section2Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1];
CRGB *section3Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2];
CRGB *section4Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3];
CRGB *section5Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3 + NUM_STRIP_SECTION4];
CRGB *section6Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3 + NUM_STRIP_SECTION4 + NUM_STRIP_SECTION5];
CRGB *section7Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3 + NUM_STRIP_SECTION4 + NUM_STRIP_SECTION5 + NUM_STRIP_SECTION6];
CRGB *section8Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3 + NUM_STRIP_SECTION4 + NUM_STRIP_SECTION5 + NUM_STRIP_SECTION6 + NUM_STRIP_SECTION7];
CRGB *section9Array = &ledStrip[NUM_STRIP_SECTION0 + NUM_STRIP_SECTION1 + NUM_STRIP_SECTION2 + NUM_STRIP_SECTION3 + NUM_STRIP_SECTION4 + NUM_STRIP_SECTION5 + NUM_STRIP_SECTION6 + NUM_STRIP_SECTION7 + NUM_STRIP_SECTION8];

// Declare functions.
void defaultRingColor();
void lightLEDSection(uint8_t section);
void resetGraphLights();
int gameFinishedLightsRainbow(int countdown);
int gameFinishedLightsBreathing(int countdown);

void setupLEDs()
{
    FastLED.addLeds<NEOPIXEL, LED_STRIP_PIN>(ledStrip, TOTAL_LED_STRIP);
    FastLED.addLeds<NEOPIXEL, LED_UPPER_RING_PIN>(ledUpperRings, TOTAL_UPPER_LED);
    FastLED.addLeds<NEOPIXEL, LED_LOW_RING_PIN>(ledLowerRings, TOTAL_LOWER_LED);

    FastLED.setBrightness(255);

    fill_solid(ledStrip, TOTAL_LED_STRIP, CRGB::Black);
    fill_solid(ledUpperRings, TOTAL_UPPER_LED, CRGB::Black);
    fill_solid(ledLowerRings, TOTAL_LOWER_LED, CRGB::Black);
    FastLED.show();

    Serial.begin(9600);

    defaultRingColor();
}

// Turn the ring LEDS all the same color, defaulted as white.
void defaultRingColor()
{
    fill_solid(ledUpperRings, TOTAL_UPPER_LED, CRGB::White);
    fill_solid(ledLowerRings, TOTAL_LOWER_LED, CRGB::White);
    FastLED.show();
}

void lightLEDSection(uint8_t section)
{
    if (section == 0)
    {
        fill_solid(section0Array, NUM_STRIP_SECTION0, CRGB::Red);
    }
    else if (section == 1)
    {
        fill_solid(section1Array, NUM_STRIP_SECTION1, CRGB::Red);
    }
    else if (section == 2)
    {
        fill_solid(section2Array, NUM_STRIP_SECTION2, CRGB::Red);
    }
    else if (section == 3)
    {
        fill_solid(section3Array, NUM_STRIP_SECTION3, CRGB::Red);
    }
    else if (section == 4)
    {
        fill_solid(section4Array, NUM_STRIP_SECTION4, CRGB::Red);
    }
    else if (section == 5)
    {
        fill_solid(section5Array, NUM_STRIP_SECTION5, CRGB::Red);
    }
    else if (section == 6)
    {
        fill_solid(section6Array, NUM_STRIP_SECTION6, CRGB::Red);
    }
    else if (section == 7)
    {
        fill_solid(section7Array, NUM_STRIP_SECTION7, CRGB::Red);
    }
    else if (section == 8)
    {
        fill_solid(section8Array, NUM_STRIP_SECTION8, CRGB::Red);
    }
    else if (section == 9)
    {
        fill_solid(section9Array, NUM_STRIP_SECTION9, CRGB::Red);
    }
    FastLED.show();
}

void resetGraphLights()
{
    fill_solid(ledStrip, TOTAL_LED_STRIP, CRGB::Black);
    FastLED.show();
}

// Sequence to celebrate finishing. Rainbow sequence.
// Countdown variable dictates how many times it will chase.
int gameFinishedLightsRainbow(int countdown)
{
    if (countdown == 0)
    {
        return 0;
    }

    for (uint8_t i = 0; i < TOTAL_LED_STRIP; i++)
    {
        uint8_t hueVal = i;
        map(hueVal, 0, TOTAL_LED_STRIP, 0, 255);
        ledStrip[i] = CHSV(hueVal, 255, (beatsin8(35, 100, 200, 0, 0)));
        delay(50);
    }

    for (uint8_t i = 0; i < TOTAL_LED_STRIP; i++)
    {
        ledStrip[i] = CRGB::Black;
        delay(20);
    }
    return gameFinishedLightsRainbow(countdown - 1);
}

// Sequence to celebrate finishing. Red "breathing."
// Countdown variable dictates how many times it will "breathe."
int gameFinishedLightsBreathing(int countdown)
{
    if (countdown == 0)
    {
        return 0;
    }

    // Make all half bright first.
    for (uint8_t i = 0; i < TOTAL_LED_STRIP; i++)
    {
        ledStrip[i] = CHSV(0, 255, 128);
        delay(25);
    }

    for (uint8_t i = 0; i < TOTAL_LED_STRIP; i++)
    {
        ledStrip[i] = CHSV(0, 255, 255);
        delay(50);
    }

    return gameFinishedLightsBreathing(countdown - 1);
}