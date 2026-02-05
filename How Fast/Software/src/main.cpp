/*
 * How Fast - NatSci Hall OMSI
 * source code
 * Calico Rose
 */

#include <leds.cpp>
#include <tofs.cpp>
#include <audio.cpp>

void setup()
{
  setupLEDs();
  setupAudio();
  setupTOFSerial();
}

void loop()
{
  readTOFData();
  printTOFDistance();

  delay(10);

  //uint8_t tofTriggered = tofTriggered();
  //
}