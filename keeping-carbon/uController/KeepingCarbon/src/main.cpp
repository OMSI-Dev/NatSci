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
    //Connect to the PC
    Serial.begin(115200);
    //Connect to each section
    section1.begin(115200);
    section2.begin(115200);
    section3.begin(115200);

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

/*
void loop() 
{

  startBtn.update();

  if(!gameOn && startBtn.isPressed())
  {
    gameOn = !gameOn;
    Serial.println("Game On");
    gameTimer.setTime(60000);
    removeMole.setTime(removeTick);
  }

  if(points >= 20){Serial.println("Resetting");}

  if(!gameTimer.running() && gameOn)
  {
    Serial.println("Game Over");
    gameOn = false;    
    reset();
  }

  if(gameOn)
  {
    
    u_int64_t tempTime = gameTimer.getRemain();


    if((tempTime/10000) != lastUpdate )
    {
      if(b>=20)
      {
        b = b-50;
      }
      lastUpdate = tempTime/10000;
    }

    for (int i = 0; i < 5; i++) 
    {
        ledButtons[i].update();
    }

    if (!moleTimer.running()) 
    {
        //Serial.println("Set mole");
        currentMole = setMole();
        if(!ledButtons[currentMole].isLedOn())
        {
          ledButtons[currentMole].setColor();
          lastMole = currentMole;
        }
        moleTimer.setTime(moleTicks);
        removeMole.setTime(removeTick);
    }

    if(!removeMole.running())
    {
      ledButtons[lastMole].off(); 
      Serial.print("Remove Mole:");
      Serial.println(lastMole);    
    }

    if(!moleTicker.running() && moleTicks != 100)
    {      
      moleTicker.setTime(2000);
      moleTicks = moleTicks-150;
      removeTick = removeTick - 125;
    }
    

  } 

}
*/

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

