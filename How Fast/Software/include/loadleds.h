/*
 * Calico Randall
 * January 26, 2026
 * Testing LED reaction with ToF
 */

#include <Arduino.h>
#include <FastLED.h>

#define LED_STRIP_PIN 7
#define TOTAL_LED_STRIP 15

CRGBArray<TOTAL_LED_STRIP> ledStrip;

void loadLEDs()
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