
/*
LED handler, handles all the led functions.

Aaron
8/18/26
*/

#define NUM_LEDS 25
CRGB house[NUM_LEDS];
CRGB person[NUM_LEDS];
CRGB cloud[NUM_LEDS];

void ledTest();

void setLED()
{
    FastLED.addLeds<WS2812, ledData1>(house, NUM_LEDS);
    FastLED.addLeds<WS2812, ledData2>(person, NUM_LEDS);
    FastLED.addLeds<WS2812, ledData3>(cloud, NUM_LEDS);

    ledTest();

    Serial.println("Leds Set and Tested");
}

void ledTest()
{
    digitalWrite(13, HIGH);
    fill_solid(house, NUM_LEDS, CRGB::Red);
    fill_solid(cloud, NUM_LEDS, CRGB::Red);
    fill_solid(person, NUM_LEDS, CRGB::Red);
    FastLED.show();
    delay(1000);

    digitalWrite(13, LOW);
    fill_solid(house, NUM_LEDS, CRGB::Blue);
    fill_solid(cloud, NUM_LEDS, CRGB::Blue);
    fill_solid(person, NUM_LEDS, CRGB::Blue);
    FastLED.show();
    delay(1000);

    digitalWrite(13, HIGH);
    fill_solid(house, NUM_LEDS, CRGB::Green);
    fill_solid(cloud, NUM_LEDS, CRGB::Green);
    fill_solid(person, NUM_LEDS, CRGB::Green);
    FastLED.show();
    delay(1000);

    digitalWrite(13, LOW);
    FastLED.clear(1);
    FastLED.show();
    delay(1000);
}