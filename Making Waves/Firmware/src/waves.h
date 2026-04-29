#include <Arduino.h>
#include <Bounce2.h>
#include <Timer.h>
#include <FastLED.h>
#include <Pulse.h>

MoToTimer btnLock,heart, lightFade;

#define aPin 17
#define bPin 18
#define cPin 19
#define langPin 20
#define selectPin 21


#define aPWM 0
#define bPWM 1
#define cPWM 2
#define langPWM 3
#define selectPWM 4

#define A KEY_A
#define B KEY_B
#define C KEY_C
#define S KEY_S
#define lang KEY_L

Bounce2::Button aButton = Bounce2::Button();
Bounce2::Button bButton = Bounce2::Button();
Bounce2::Button cButton = Bounce2::Button();
Bounce2::Button selectButton = Bounce2::Button();
Bounce2::Button langButton = Bounce2::Button();

uint8_t incomingByte,choice;

bool on, attractor = true,startLight,questionLights,trackballLights;


CRGBArray<12> trackBall;

Pulse startFade;
 

void trackballAnimation();
void heartbeat();

void setup() 
{
  FastLED.addLeds<WS2812B, 5, GRB>(trackBall, 12).setCorrection(TypicalSMD5050); 

  pinMode(aPin, INPUT_PULLUP);
  pinMode(bPin, INPUT_PULLUP);
  pinMode(cPin, INPUT_PULLUP);
  pinMode(selectPin, INPUT_PULLUP);
  pinMode(langPin, INPUT_PULLUP);

  pinMode(13, OUTPUT);
  pinMode(aPWM, OUTPUT);
  pinMode(bPWM, OUTPUT);
  pinMode(cPWM, OUTPUT);
  pinMode(langPWM, OUTPUT);

  //pulse object
  startFade.attach(selectPWM);
  startFade.setIncrement(5);
  startFade.setRate(35);

  //will be high until loop starts
  digitalWrite(aPWM, HIGH);
  digitalWrite(bPWM, HIGH);
  digitalWrite(cPWM, HIGH);
  digitalWrite(selectPWM, HIGH);
  digitalWrite(langPWM, HIGH);

  aButton.attach(aPin, INPUT_PULLUP);
  bButton.attach(bPin, INPUT_PULLUP);
  cButton.attach(cPin, INPUT_PULLUP);
  selectButton.attach(selectPin, INPUT_PULLUP);
  langButton.attach(langPin, INPUT_PULLUP);

  aButton.setPressedState(LOW);
  bButton.setPressedState(LOW);
  cButton.setPressedState(LOW);
  selectButton.setPressedState(LOW);
  langButton.setPressedState(LOW);

  aButton.interval(5);
  bButton.interval(5);
  cButton.interval(5);
  selectButton.interval(5);
  langButton.interval(5);

  Keyboard.begin();

  Serial.begin(115200);
}

void heartbeat()
{
  if(!heart.running())
  {
    on = !on;
    digitalWrite(13, on);
    heart.setTime(500);
  }
}

void serialCheck()
{
  if(Serial.available())
  {
    incomingByte = Serial.read();

  }

  if (incomingByte == 'A'){attractor = true;};
  if (incomingByte == 'G'){attractor = false;};

  if (incomingByte == 'S'){startLight = true;};
  if (incomingByte == 's'){startLight = false;};

  if (incomingByte == 'Q'){questionLights = true;};
  if (incomingByte == 'q'){questionLights = false;};

  if (incomingByte == 'T'){trackballLights = false;};
  if (incomingByte == 't'){trackballLights = true;};

}

void setLights()
{
  //turn on or off all question lights based on incoming serial
  if(questionLights)
  {
    digitalWrite(aPWM, HIGH);
    digitalWrite(bPWM, HIGH);
    digitalWrite(cPWM, HIGH);
  }else{
    digitalWrite(aPWM, LOW);
    digitalWrite(bPWM, LOW);
    digitalWrite(cPWM, LOW);
  }

  //can be used later for lighting up lights as they show onscreen 
  switch (choice)
  {
  case 1:
    digitalWrite(aPWM, HIGH);
    digitalWrite(bPWM, LOW);
    digitalWrite(cPWM, LOW);
    break;
  case 2:
    digitalWrite(aPWM, HIGH);
    digitalWrite(bPWM, HIGH);
    digitalWrite(cPWM, LOW);
    break;
  case 3:
    digitalWrite(aPWM, HIGH);
    digitalWrite(bPWM, HIGH);
    digitalWrite(cPWM, HIGH);
    break;

  default:
    break;
  }

  if (startLight)
  {
    startFade.update(1);
  }
  else
  {
    startFade.update(0);
  }

  if(!trackballLights)
  {
    fill_solid(trackBall,12,CRGB::Black);
  }else{
    
    fill_solid(trackBall,12,CRGB::Blue);
  }
    
    FastLED.show();
}

// void trackballAnimation()
// {
//   if(!lightFade.running())
//   {
//     trackBall.fadeToBlackBy(26);
//   }
//     fill_solid(trackBall,12,CRGB::Blue);
//     FastLED.show();
// }

void handleKeypress()
{
  
  if(aButton.pressed() && !btnLock.running())
  {
    btnLock.setTime(50);
    Keyboard.press(A);
    Serial.println("Key A pressed");
  }

  if(bButton.pressed() && !btnLock.running())
  {
    btnLock.setTime(50);
   Keyboard.press(B);
   Serial.println("Key B pressed");
  }

  if(cButton.pressed() && !btnLock.running())
  {
    btnLock.setTime(50);
    Keyboard.press(C);
    Serial.println("Key C pressed");
  }

  if(selectButton.pressed() && !btnLock.running())
  {
    btnLock.setTime(50);
    Keyboard.press(S);
    Serial.println("Key S (Select) pressed");
  }

  if(langButton.pressed() && !btnLock.running())
  {
    btnLock.setTime(50);
   Keyboard.press(lang);
   Serial.println("Key L (Lang) pressed");
  }

  if(!btnLock.running())
  {
    Keyboard.releaseAll();
  }
}

//Not implamented yet, will add later
void attractLights()
{
  // if(attractor)
  // {
  //   startFade.update(1);
  // }
  // else
  // {
  //   startFade.update(0);
  // }
}

void checkButtons()
{
  heartbeat();
  aButton.update();
  bButton.update();
  cButton.update();
  selectButton.update();
  langButton.update();
}

void loop() 
{
  checkButtons();
  serialCheck();
  setLights();
  handleKeypress();
  attractLights();
}
