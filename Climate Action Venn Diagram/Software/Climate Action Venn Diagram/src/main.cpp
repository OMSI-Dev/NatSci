/*
Climate Action Venn Diagram
Aaron De Lanty & MY BOY CLAUDE
2/12/2026

Scan RFID manipulatives across three catagories assign from HEX to String and send over serial to PC.

Resources:
Claude & all the devs before it...developed the backend for sending packets to the B1 RFID Module.

*/

#include <Arduino.h>
#include <Bounce2.h>
#include <Timer.h>
#include <pins.h>

void setup()
{
  setPins();
}

void loop()
{
}
