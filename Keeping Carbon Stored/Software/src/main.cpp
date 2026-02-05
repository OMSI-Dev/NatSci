/*
 * Keeping Carbon Stored
 * Calico Rose
 * January 7, 2025
 * Communication with the stomp buttons and the computer.
 * Essentially a communication hub or "router", sending and recieving
 * signals from the buttons and to the computer.
 * References:
 */

#include <Arduino.h>

void setup()
{
  Serial.begin(9600);
  while (!Serial)
  {
  }
  Serial.println("Serial started.");
}

void loop()
{

  if (Serial.available() > 0)
  {
    char incomingByte = Serial.read();
    Serial.print("Recieved: ");
    Serial.println(incomingByte);
  }
}