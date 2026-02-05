/*
 * Calico Rose
 * January 2026
 * LED reaction to ToF
 */

#include <Arduino.h>
#include <FastLED.h>

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
#define LED_UPPER_RING_TOTAL (UPPER_RING0 + UPPER_RING1 + UPPER_RING2 + UPPER_RING3 + UPPER_RING4 + UPPER_RING5 + UPPER_RING6 + UPPER_RING7 + UPPER_RING8 + UPPER_RING9)

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
#define LED_LOW_RING_TOTAL (LOW_RING0 + LOW_RING1 + LOW_RING2 + LOW_RING3 + LOW_RING4 + LOW_RING5 + LOW_RING6 + LOW_RING7 + LOW_RING8 + LOW_RING9)

// Declare the LED strip data pin and amount of LEDs in each section along with the total.
// This stip is the big red graph strip.
#define LED_STRIP_PIN 7
#define LED_SECTION0 10
#define LED_SECTION1 10
#define LED_SECTION2 10
#define LED_SECTION3 10
#define LED_SECTION4 10
#define LED_SECTION5 10
#define LED_SECTION6 10
#define LED_SECTION7 10
#define LED_SECTION8 10
#define LED_SECTION9 10
#define TOTAL_LED_STRIP (LED_SECTION0 + LED_SECTION1 + LED_SECTION2 + LED_SECTION3 + LED_SECTION4 + LED_SECTION5 + LED_SECTION6 + LED_SECTION7 + LED_SECTION8 + LED_SECTION9)

// Define the array of LEDs for the red graph strip.
CRGBArray<TOTAL_LED_STRIP> ledStrip;

// CRGB *section0Array = &ledStrip[0];
// CRGB *section1Array = &ledStrip[LED_SECTION0]

void setupLEDs()
{
    FastLED.addLeds<NEOPIXEL, LED_STRIP_PIN>(ledStrip, TOTAL_LED_STRIP);
    FastLED.setBrightness(255);
    fill_solid(ledStrip, TOTAL_LED_STRIP, CRGB::Black);
    FastLED.show();

    Serial.begin(9600);
}

void turnRed()
{
    fill_solid(ledStrip, TOTAL_LED_STRIP, CRGB::Red);
    FastLED.show();
}

void turnGreen()
{
    fill_solid(ledStrip, TOTAL_LED_STRIP, CRGB::Green);
    FastLED.show();
}

void turnBlack()
{
    fill_solid(ledStrip, TOTAL_LED_STRIP, CRGB::Black);
    FastLED.show();
}