
#define led1DataPin 16
#define led2DataPin 15
#define led3DataPin 14
#define led4DataPin 13
#define led5DataPin 12

//ADA buttons needs to be defined as RGB
//uncomment for the ADA Rows
//#define RGB
#ifndef RGB
#define NUM_LEDS 44
#else
#define NUM_LEDS 84
#endif

//Switch between RGB || RGBW
#ifndef RGB
  Adafruit_NeoPixel Btn1LEDS(NUM_LEDS, led1DataPin, NEO_GRBW + NEO_KHZ800);
  Adafruit_NeoPixel Btn2LEDS(NUM_LEDS, led2DataPin, NEO_GRBW + NEO_KHZ800);
  Adafruit_NeoPixel Btn3LEDS(NUM_LEDS, led3DataPin, NEO_GRBW + NEO_KHZ800);
  Adafruit_NeoPixel Btn4LEDS(NUM_LEDS, led4DataPin, NEO_GRBW + NEO_KHZ800);
  Adafruit_NeoPixel Btn5LEDS(NUM_LEDS, led5DataPin, NEO_GRBW + NEO_KHZ800);
#else
  Adafruit_NeoPixel Btn1LEDS(NUM_LEDS, led1DataPin, NEO_GRB + NEO_KHZ800);
  Adafruit_NeoPixel Btn2LEDS(NUM_LEDS, led2DataPin, NEO_GRB + NEO_KHZ800);
  Adafruit_NeoPixel Btn3LEDS(NUM_LEDS, led3DataPin, NEO_GRB + NEO_KHZ800);
  Adafruit_NeoPixel Btn4LEDS(NUM_LEDS, led4DataPin, NEO_GRB + NEO_KHZ800);
  Adafruit_NeoPixel Btn5LEDS(NUM_LEDS, led5DataPin, NEO_GRB + NEO_KHZ800);
#endif

//Used to convert data packet to an RGB value
uint8_t red = 0;
uint8_t green = 0;
uint8_t blue = 0;

void rgbValues()
{
  ///convert to packed RGB packet
  uint32_t r1Temp = (data[1] - '0') * 100;
  uint32_t r2Temp = (data[2] - '0') *  10;
  uint32_t  r3Temp = (data[3] - '0');
  
  uint32_t g1Temp = (data[4] - '0') * 100;
  uint32_t g2Temp = (data[5] - '0') *  10;
  uint32_t g3Temp = (data[6] - '0' );

  uint32_t b1Temp = (data[7] - '0') * 100;
  uint32_t b2Temp = (data[8] - '0') * 10;
  uint32_t b3Temp = (data[9] - '0');
 
  red = (r1Temp + r2Temp + r3Temp);
  green = (g1Temp + g2Temp + g3Temp);
  blue = (b1Temp + b2Temp + b3Temp);

}

void clearRGB()
{
  red = 0;
  green = 0;
  blue = 0;
}

void clearLED(uint8_t btnNum)
{
    switch (btnNum)
    {
    case 1:
        
        Btn1LEDS.clear();
        Btn1LEDS.show();
        Serial.println("Cleared button 1");
        break;
    case 2:
        Btn2LEDS.clear();
        Btn2LEDS.show();
        Serial.println("Cleared button 2");
    break;
     case 3:
        Btn3LEDS.clear();
        Btn3LEDS.show();
        Serial.println("Cleared button 3");
    break;
    case 4:
        Btn4LEDS.clear();
        Btn4LEDS.show();
        Serial.println("Cleared button 4");
    break;
    case 5:
        Btn5LEDS.clear();
        Btn5LEDS.show();
        Serial.println("Cleared button 5");
    break;           
    default:
        break;
    }


}