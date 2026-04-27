#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <serial_handler.h>
#include <button_handler.h>
#include <led_Handler.h>

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



void setup() {
  //Initialize USB Serial for debugging
  Serial.begin(9600);
  delay(1000);
  while(!Serial);
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


void loop() {
  //read incoming messages from 4.1
  
  readSerial();
  buttonUpdate();
  rgbValues();

  switch (data[0])
  {

  case 49:
    #ifndef RGB
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn1LEDS.show();
    Serial.println("Color update for button 1");
    clearRGB();
    //Set allow button press state
    buttonStates[0] = true;
    break;

  case 50:
    
    #ifndef RGB
    Btn2LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn2LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn2LEDS.show();
    Serial.println("Color update for button 2");
     clearRGB();
    //Set allow button press state
    buttonStates[1] = true;
    break;

  case 51:
    #ifndef RGB
    Btn3LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn3LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn3LEDS.show();
    Serial.println("Color update for button 3");
     clearRGB();
    //Set allow button press state
    buttonStates[2] = true;
    break;

  case 52:
    
    #ifndef RGB
    Btn4LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn4LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn4LEDS.show();
    Serial.println("Color update for button 4");
     clearRGB();
    //Set allow button press state
    buttonStates[3] = true;
    break;

  case 53:
    
    #ifndef RGB
    Btn5LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn5LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn5LEDS.show();
    Serial.println("Color update for button 5");
     clearRGB();
    //Set allow button press state
    buttonStates[4] = true;
    break;

  default:
    break;
  }
  
}