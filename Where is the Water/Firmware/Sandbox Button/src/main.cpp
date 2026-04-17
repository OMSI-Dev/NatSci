/*
 * Where Is The Water
 * Nat Sci Hall - OMSI
 * Calico Rose
 * Purpose: Simulate the up arrow being pressed when
 * the button is pressed.
 *
 */

#include <Arduino.h>
#include <Bounce2.h>

#define DROUGHT_BUTTON_PIN 2
#define KEY KEY_UP

bool prevPressed = false;

Bounce2::Button droughtButton = Bounce2::Button();

void setup()
{
  // Declare explicit pin modes here
  // Usually helpful if not necessary for Teensy specifically
  // Otherwise won't fully open up / connect the pin.
  pinMode(13, OUTPUT);
  pinMode(2, INPUT_PULLUP);
  pinMode(4, INPUT_PULLUP);

  // Button setups
  droughtButton.attach(DROUGHT_BUTTON_PIN, INPUT_PULLUP);
  droughtButton.interval(5);
  droughtButton.setPressedState(LOW);

  // Serial and keyboard starts
  Serial.begin(9600);
  Keyboard.begin();

  // Turn LED on Teensy board on.
  digitalWrite(13, HIGH);
}

void loop()
{
  droughtButton.update();

  // If button is pressed, press the key "up".
  // In the Unity program, this coordinates to clearing the water.
  if (droughtButton.pressed())
  {
    Keyboard.press(KEY);
    delay(20);
    Keyboard.releaseAll();
  }
}
