
void attachButtons() {
    // Attach Pins
    startBtn.attach(18);
    easyBtn.attach(19);
    medBtn.attach(20);
    hardBtn.attach(21);

    startBtn.interval(5);
    easyBtn.interval(5);
    medBtn.interval(5);
    hardBtn.interval(5);

    startBtn.setPressedState(LOW);
    easyBtn.setPressedState(LOW);
    medBtn.setPressedState(LOW);
    hardBtn.setPressedState(LOW);

    // Set pinMode
    pinMode(16, INPUT_PULLUP);
    pinMode(17, INPUT_PULLUP);
    pinMode(18, INPUT_PULLUP);
    pinMode(19, INPUT_PULLUP);
    pinMode(20, INPUT_PULLUP);
    pinMode(21, INPUT_PULLUP);
    pinMode(22, INPUT_PULLUP);
    pinMode(23, INPUT_PULLUP);
}



void updateButtons()
{
  startBtn.update();
  easyBtn.update();
  medBtn.update();
  hardBtn.update();
}

bool checkForDifficulty()
{
  //Easy Mode
  if(easyBtn.pressed())
  {
    easy = true;
    med = false;
    hard = false;
    moleTime = easyTime;
    return easy;
  }
  //Medium Mode
  if(medBtn.pressed())
  {
    easy = false;
    med = true;
    hard = false;
    moleTime = medTime;
    return med;
  }
  //Hard mode
  if(hardBtn.pressed())
  {
    easy = false;
    med = false;
    hard = true;
    moleTime = hardTime;
    return hard;
  }
  return;
}

void checkForStart()
{
  if(startBtn.pressed())
  {
    //send settings to sections
    //@:{moleTime} = this is how long a mole's light will stay on before it reports a miss
    section1.println('@:' + moleTime);
    section2.println('@:' + moleTime);
    section3.println('@:' + moleTime);
    
    //send to PC to start the game
    PC.println("S");

    //Set game flag to on
    gameOn = true;

  }
}



//used only in section code. move to section code.
void attachLight() {
    btn1Light.attach(6);
    btn2Light.attach(4);
    btn3Light.attach(5);
    btn4Light.attach(3);
    btn5Light.attach(2); // last parameter sets the brightness to full
    FastLED.addLeds<WS2811, 7>(pointLight,10);
}


struct LedButton {
    Bounce2::Button* button;
    Haxx<1>* led;
    CRGB color;

    bool isLedOn() 
      {
        return led->isOn();
      }

    void setColor()
    {
      uint8_t gamble = random(100);
      if(gamble > 75)
      {
      led->centerFill(0,255,0);
      }else
      {
      led->centerFill(255,0,b);  
      }

    }

    void toggleLed() {
        if (isLedOn()) 
        {
            led->off();
        }
    }
    
    void off()
    {
      led->off();
    }
    //check if button press is correct
    //strike if not
    void update() {

        button->update();
        if(isLedOn())
        {
          if (button->fell()) 
          {
              toggleLed();
              setPoints(true);
          }
        }else{
          if (button->fell()) 
          {
              setPoints(false);
              led->red();
          }

        }    
    }

};