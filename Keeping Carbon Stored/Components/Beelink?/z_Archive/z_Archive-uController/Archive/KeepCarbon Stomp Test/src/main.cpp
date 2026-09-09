#include <Arduino.h>
#include <Bounce2.h>
#include <Timer.h>
#include <FastLED.h>

#define numLed 60*4
#define ledPin 2
#define swPin 3

MoToTimer blockTimer,hueTimer;

Bounce2::Button testButton = Bounce2::Button();

CRGB testRing[numLed];

u_int8_t pressCount = 0, maxEffects = 12, hue = 0;

void setup() 
{
  testButton.attach(swPin, INPUT_PULLUP);
  testButton.setPressedState(LOW);
  testButton.interval(5);

  FastLED.addLeds<NEOPIXEL,ledPin>(testRing, 0, numLed);

}

void loop() 
{
  testButton.update();

  if(!hueTimer.running())
  {
    hue++;
    if(hue == 250){hue = 0;}
    hueTimer.setTime(150);
  }

  if(testButton.isPressed() && !blockTimer.running())
  {
    pressCount++;
    if(pressCount > maxEffects){pressCount = 0;}
    blockTimer.setTime(350);
  }

  switch (pressCount)
  {
  case 0:
    fill_solid(testRing,numLed,CRGB(255/4,0,0));
    FastLED.show();
    break;
  case 1:
    fill_solid(testRing,numLed,CRGB(255/3,0,0));
    FastLED.show();
    break;
  case 2:
    fill_solid(testRing,numLed,CRGB(255/2,0,0));
    FastLED.show();
    break;
  case 3:
    fill_solid(testRing,numLed,CRGB(255,0,0));
    FastLED.show();
    break;    
//Green
  case 4:
    fill_solid(testRing,numLed,CRGB(0,255/4,0));
    FastLED.show();
    break;
  case 5:
    fill_solid(testRing,numLed,CRGB(0,255/3,0));
    FastLED.show();
    break;
  case 6:
    fill_solid(testRing,numLed,CRGB(0,255/2,0));
    FastLED.show();
    break;
  case 7:
    fill_solid(testRing,numLed,CRGB(0,255,0));
    FastLED.show();
    break; 
//blue
  case 8:
    fill_solid(testRing,numLed,CRGB(0,0,255/4));
    FastLED.show();
    break;
  case 9:
    fill_solid(testRing,numLed,CRGB(0,0,255/3));
    FastLED.show();
    break;
  case 10:
    fill_solid(testRing,numLed,CRGB(0,0,255/2));
    FastLED.show();
    break;
  case 11:
    fill_solid(testRing,numLed,CRGB(0,0,255));
    FastLED.show();
    break;
  case 12:
    fill_rainbow(testRing,numLed,hue);
    FastLED.show();
    break;     
  case 13:
    fill_solid(testRing,numLed,CRGB::Black);
    FastLED.show();
    break;   
  }


}

