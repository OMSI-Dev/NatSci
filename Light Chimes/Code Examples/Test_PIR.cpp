#include <Arduino.h>

const int MOTION_PIN = 10; 

void setup() 
{
  Serial.begin(9600);
  pinMode(MOTION_PIN, INPUT_PULLUP); 
  Serial.println("Setup complete");

}

void loop() 
{
  int proximity = digitalRead(MOTION_PIN);
  if (proximity == LOW) 
  {
    Serial.println("Motion detected!");
  }
  else
  {
    Serial.println("No motion detected!");
  }

  delay(200);
}