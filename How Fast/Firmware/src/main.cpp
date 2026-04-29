/*
 * How Fast - NatSci Hall OMSI
 * source code
 * Calico Rose
 */

#include <leds.cpp>
#include <tofs.cpp>
//#include <audio.cpp>

void resetSections();
bool allSectionsComplete();

bool sectionsCompleted[TOTAL_TOFS];

long unsigned int timeout = 30000;
int lastInteract;

void setup()
{
  setupLEDs();
  //setupAudio();
  setupTOFSerial();

  for (uint8_t i = 0; i < TOTAL_TOFS; i++)
  {
    sectionsCompleted[i] = false;
  }
}

void loop()
{
  readTOFData();
  printTOFDistance();
  delay(1000);

  uint8_t tofDone = tofTriggered();

  if (tofDone != -1)
  {
    if (!sectionsCompleted[tofDone])
    {
      Serial.print("ToF ");
      Serial.print(tofDone);
      Serial.print(" completed: ");
      sectionsCompleted[tofDone] = true;
      Serial.println(sectionsCompleted[tofDone]);
    }
    lastInteract = millis();
  }

  // If no interaction after time defined in timout variable,
  // reset the LED strip graph to black and reset the bool
  // array holding which sections have been completed to
  // all false.
  if (millis() - lastInteract > timeout)
  {
    resetSections();
    resetGraphLights();
  }

  // If all sections have been completed, do completion
  // celebration then reset for new "gameplay."
  if (allSectionsComplete())
  {
    // TO ADD - LED ANIMATION WITH DELAY
    gameFinishedLightsRainbow(3);
    gameFinishedLightsBreathing(3);
    resetSections();
    resetGraphLights();
  }

  // uint8_t tofTriggered = tofTriggered();
  //
}

void resetSections()
{
  for (uint8_t i = 0; i < TOTAL_TOFS; i++)
  {
    sectionsCompleted[i] = false;
  }
}

// Returns true if all bools in the array are true AKA
// if all sections have been completed.
bool allSectionsComplete()
{
  uint8_t i;
  for (i = 0; i < TOTAL_TOFS; i++)
  {
    if (!sectionsCompleted[i])
    {
      return false;
    }
  }
  return (i == TOTAL_TOFS);
}