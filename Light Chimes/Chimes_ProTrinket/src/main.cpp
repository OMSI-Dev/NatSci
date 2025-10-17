#include <Arduino.h>

/* 
PIR sensor
red > 5V-12V (9V reccommended)
white to GND 
black > alarm  (GPIO)
*/

const int MOTION_PIN = 8; // Pin connected to motion detector
// const int LED_PIN = 13; // LED pin - active-high

void setup() 
{
  Serial.begin(9600);
  // The PIR sensor's output signal is an open-collector, 
  // so a pull-up resistor is required:
  pinMode(MOTION_PIN, INPUT_PULLUP);
  // pinMode(LED_PIN, OUTPUT);
  Serial.println("Setup complete");

}

void loop() 
{
  Serial.println("loop");

  int proximity = digitalRead(MOTION_PIN);
  if (proximity == LOW) // If the sensor's output goes low, motion is detected
  {
    // digitalWrite(LED_PIN, HIGH);
    Serial.println("Motion detected!");
  }
  else
  {
    // digitalWrite(LED_PIN, LOW);
    Serial.println("No motion detected!");

  }

  delay(200);
}