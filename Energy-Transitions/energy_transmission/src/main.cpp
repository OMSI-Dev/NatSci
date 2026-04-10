#include <Arduino.h>
#include <fastled.h>
#include <Timer.h>

MoToTimer stepTimer, attractBlink,attractSolid;

CRGB attract[12];
CRGB energy[10];

#define attractpin 18
#define energypin 19
#define stepTime 2000

uint8_t stepPos;
uint8_t shift;

bool stopBlink;

void setup() 
{
FastLED.addLeds<WS2812B, attractpin, GRB>(attract, 12).setCorrection(TypicalSMD5050);
FastLED.addLeds<WS2812B, energypin, GRB>(energy, 10).setCorrection(TypicalSMD5050);
FastLED.setBrightness(175);
Serial.begin(9600);
}

void stepThroughEnergy()
{
 if(!stepTimer.running())
 {
  stepPos++;
  if(stepPos == 3){stepPos = 0;}
  stepTimer.setTime(stepTime);
  Serial.println(stepPos);
 }

  switch (stepPos)
  {
  case 0:
    fill_solid(energy,10,CRGB::Red);

    break;
  case 1:
    fill_solid(energy,10,CRGB::Yellow);
    break;
  case 2:
    fill_solid(energy,10,CRGB::Green);
    break;      
  default:
    break;
  }


}

void attractorBlink ()
{
      if(!attractBlink.running() && !stopBlink)
      {
        shift = random(75,125);
        int tempTime = random(75,100);
        attractBlink.setTime(tempTime);
      }
      if(!stopBlink)
      {
        fill_solid(attract, 12, CHSV(255,0,shift));
      }else
      {
       fill_solid(attract, 12, CHSV(255,0,255));
      }

      if(!attractSolid.running())
      {
        stopBlink = !stopBlink;
        attractSolid.setTime(6000);
      }

}

void loop() 
{
  stepThroughEnergy();
  attractorBlink();
  FastLED.show();
}
