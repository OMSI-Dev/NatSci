#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <serial_handler.h>
#include <button_handler.h>


const uint8_t dataBuffer = 11;
uint8_t data[dataBuffer];

#define led1DataPin 16
#define led2DataPin 15
#define led3DataPin 14
#define led4DataPin 13
#define led5DataPin 12

//ADA buttons needs to be defined as RGB
//uncomment for the ADA Rows
#define RGB
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


void setup() {
  //Initialize USB Serial for debugging
  Serial.begin(9600);
  delay(1000);
  Serial.println("Teensy 4.0 (Child) - Starting up...");
  setSerial();
  setPins();
  
  Btn1LEDS.begin();
  Btn2LEDS.begin(); 
  Btn3LEDS.begin(); 
  Btn4LEDS.begin(); 
  Btn5LEDS.begin(); 

  Btn1LEDS.show(); 
  Btn2LEDS.show(); 
  Btn3LEDS.show(); 
  Btn4LEDS.show(); 
  Btn5LEDS.show();  

  #ifndef RGB
  Btn1LEDS.setBrightness(200);
  Btn2LEDS.setBrightness(200);
  Btn3LEDS.setBrightness(200);
  Btn4LEDS.setBrightness(200);
  Btn5LEDS.setBrightness(200);
  #else
  Btn1LEDS.setBrightness(100);
  Btn2LEDS.setBrightness(100);
  Btn3LEDS.setBrightness(100);
  Btn4LEDS.setBrightness(100);
  Btn5LEDS.setBrightness(100);
  #endif


 
}

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

void loop() {
  //read incoming messages from 4.1
  
  if (Serial1.available()) 
  {
    Serial1.readBytesUntil('\n', data,dataBuffer);
    Serial.print("Button: ");
    Serial.println(data[0]);
    
    for(uint8_t i =0; i<dataBuffer; i++)
    {
      Serial.print(i);
      Serial.print(":");
      Serial.println(data[i]);
    }
  }

  
  switch (data[0])
  {

  case 49:
    // fill_solid(btn1LEDS, NUM_LEDS, CRGB(red,green,blue));
    rgbValues();
    //Btn1LEDS.fill(255000000);
    #ifndef RGB
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn1LEDS.show();
    Serial.println("Color update for button 1");
    clearRGB();
    //FastLED.show();

    break;

  case 50:
    rgbValues();
    #ifndef RGB
    Btn2LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn2LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn2LEDS.show();
    Serial.println("Color update for button 2");
     clearRGB();
    //FastLED.show();
    break;

  case 51:
    // fill_solid(btn1LEDS, NUM_LEDS, CRGB(red,green,blue));
    rgbValues();
    //Btn1LEDS.fill(255000000);
    #ifndef RGB
    Btn3LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn3LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn3LEDS.show();
    Serial.println("Color update for button 3");
     clearRGB();
    //FastLED.show();
    break;

  case 52:
    rgbValues();
    #ifndef RGB
    Btn4LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn4LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn4LEDS.show();
    Serial.println("Color update for button 4");
     clearRGB();
    //FastLED.show();
    break;

  case 53:
    rgbValues();
    #ifndef RGB
    Btn5LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn5LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn5LEDS.show();
    Serial.println("Color update for button 5");
     clearRGB();
    //FastLED.show();
    break;

  default:
    break;
  }
  
  for(uint8_t i = 0; i<dataBuffer; i++)
  {
  data[i] = 0;
  }
  
  //delay(100);  // Small delay to prevent overwhelming the serial buffer
  
}

//1255000000
//1000255000
//1000000255

//2255000000

//3255000000

//4255000000

//5255000000