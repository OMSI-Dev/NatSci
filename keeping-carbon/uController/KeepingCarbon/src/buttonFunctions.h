

void attachLight() {
    btn1Light.attach(6);
    btn2Light.attach(4);
    btn3Light.attach(5);
    btn4Light.attach(3);
    btn5Light.attach(2); // last parameter sets the brightness to full
    FastLED.addLeds<WS2811, 7>(pointLight,10);
}

void attachButtons() {
    // Attach Pins
    // Btn1.attach(19);
    // Btn2.attach(18);
    // Btn3.attach(21);
    Btn4.attach(22);
    Btn5.attach(23);
    Btn6.attach(17);
    Btn7.attach(16);
    startBtn.attach(18);
    easyBtn.attach(19);
    medBtn.attach(20);
    hardBtn.attach(21);

    // Set Interval
    // Btn1.interval(5);
    // Btn2.interval(5);
    // Btn3.interval(5);
    Btn4.interval(5);
    Btn5.interval(5);
    Btn6.interval(5);
    Btn7.interval(5);
    startBtn.interval(5);

    // Set Pressed state
    // Btn1.setPressedState(LOW);
    // Btn2.setPressedState(LOW);
    // Btn3.setPressedState(LOW);
    Btn4.setPressedState(LOW);
    Btn5.setPressedState(LOW);
    Btn6.setPressedState(LOW);
    Btn7.setPressedState(LOW);
    startBtn.setPressedState(LOW);

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

//used only in section code. move to section code.
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
    Serial.println("S");

    //Set game flag to on
    gameOn = true;

  }
}