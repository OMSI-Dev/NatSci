
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
    FastLED.addLeds<WS2812, ledData1,GRB>(person, NUM_LEDS);
    FastLED.addLeds<WS2812, ledData2,GRB>(cloud, NUM_LEDS);
    FastLED.addLeds<WS2812, ledData3,GRB>(house, NUM_LEDS);

    // Test RGB
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

void confirmLED(u_int8_t RFID_NUM)
{
    switch (RFID_NUM)
    {
    case 1:
        fill_solid(person,NUM_LEDS, CRGB::DarkOrange);
        FastLED.show();
        break;
    case 2:
        fill_solid(cloud,NUM_LEDS, CRGB::Blue);
        FastLED.show();
        break;        
    case 3:
        fill_solid(house,NUM_LEDS, CRGB::DeepPink1);
        FastLED.show();
        break;    
    default:
        break;
    }
}

void scanLED(uint8_t RFID_NUM)
{

    if(RFID_NUM == 1) 
    {   
        uint8_t brightness = beatsin8(16);  // 12 BPM
        fill_solid(person,NUM_LEDS,CRGB::White);
        fadeToBlackBy(person,NUM_LEDS,(255 - brightness));
        FastLED.show();

    }

    if(RFID_NUM == 2) 
    {   
        uint8_t brightness = beatsin8(16);  // 12 BPM
        fill_solid(cloud,NUM_LEDS,CRGB::White);
        fadeToBlackBy(cloud,NUM_LEDS,(255 - brightness));
        FastLED.show();
    }

    if(RFID_NUM == 3) 
    {   
        uint8_t brightness = beatsin8(16);  // 12 BPM
        // Set all LEDs to color with varying brightness
        fill_solid(house,NUM_LEDS,CRGB::White);
        fadeToBlackBy(house,NUM_LEDS,(255 - brightness));
        FastLED.show();
    }

}