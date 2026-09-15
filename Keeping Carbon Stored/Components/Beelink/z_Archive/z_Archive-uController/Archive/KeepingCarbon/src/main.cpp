#include <Arduino.h>
#include <Haxx.h>
#include <Bounce2.h>
#include "pinDefine.h"
#include "pointFunction.h"
#include "buttonFunctions.h"
#include "communication.h"
#include "debug.h"

LedButton ledButtons[5];

uint8_t setMole() {
    uint8_t mole = random(5);
    return mole;
}

uint8_t currentMole = setMole();

void setup() {
    connectCom();

    // not used in main only for boards with attached buttons
    // Need to move to a section file
    // attachLight();
     attachButtons();

    // ledButtons[0] = { &Btn1, &btn1Light };
    // ledButtons[1] = { &Btn2, &btn2Light };
    // ledButtons[2] = { &Btn3, &btn3Light };
    // ledButtons[3] = { &Btn4, &btn4Light };
    // ledButtons[4] = { &Btn5, &btn5Light };

    // btn1Light.off();
    // btn2Light.off();
    // btn3Light.off();
    // btn4Light.off();
    // btn5Light.off();
}

void loop()
{
  gameOn = true;
  if(!gameOn)
  {
    //check for button presses.
    updateButtons();
    //check to see if a difficulty was pressed;
    bool difficulty = checkForDifficulty();
    //if a diffculty was chosen wait for the start button to be pressd
    if(difficulty == true)
    {
      checkForStart();
    }
  } else
  {
    game();
  }
}


void reset()
{
  Serial.println("Game Reset");
  gameOn = false;
  points = 0;
  b = 255;
  currentMole = setMole();
  moleTicks = 700;
  btn1Light.off();
  btn2Light.off();
  btn3Light.off();
  btn4Light.off();
  btn5Light.off();
  fill_solid(pointLight,10,CRGB::Black);
  FastLED.show();

  //stop all timers
  moleTimer.stop();
  moleTicker.stop();
  gameTimer.stop();
  printResetStatus();

}

