/*
Climate Impacts
Aaron De Lanty
2/18/2026

Read button presses to play 2 sets of audio English and Spanish.

The audio is being channel split using a Tsunami board.

*/

#include <Arduino.h>
#include <pins.h>
#include <Bounce2.h>
#include <AudioControl.h>
#include <buttons.h>

void setup()
{
    setPins();
    attachButtons();
    startAudioPlayer();
    Serial.begin(9600);
    pinMode(13, OUTPUT);
    digitalWrite(13, HIGH);
}

void loop()
{
    buttonUpdate();
    buttonPress();
}