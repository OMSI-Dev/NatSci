#include <Arduino.h>
#include <Bounce2.h>
#include <Timer.h>

MoToTimer btnLock,heart;

#define newPin 17
#define langPin 20

#define newPWM 0
#define langPWM 3

#define newIdea KEY_UP
#define lang KEY_L

Bounce2::Button newButton = Bounce2::Button();
Bounce2::Button langButton = Bounce2::Button();

bool on;

void setup() {
pinMode(newPin, INPUT_PULLUP);
pinMode(langPin, INPUT_PULLUP);
pinMode(13, OUTPUT);
pinMode(newPWM, OUTPUT);
pinMode(langPWM, OUTPUT);

//set high for now
digitalWrite(newPWM, HIGH);
digitalWrite(langPWM, HIGH);

newButton.attach(newPin, INPUT_PULLUP);
langButton.attach(langPin, INPUT_PULLUP);

newButton.setPressedState(LOW);
langButton.setPressedState(LOW);

newButton.interval(5);
langButton.interval(5);

Keyboard.begin();
Serial.begin(9600);
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

void loop() {
heartbeat();
newButton.update();
langButton.update();

if(newButton.pressed() && !btnLock.running())
{
  btnLock.setTime(50);
  Keyboard.press(newIdea);
  Serial.println("Key UP pressed");
}

if(langButton.pressed() && !btnLock.running())
{
  btnLock.setTime(50);
  Keyboard.press(lang);
  Serial.println("Key L (Language) pressed"); 
}

if(!btnLock.running())
{
  Keyboard.releaseAll();
}


}
