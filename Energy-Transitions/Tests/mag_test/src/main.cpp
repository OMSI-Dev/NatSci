#include <Arduino.h>
#include <define.h>

u_int16_t sen1Temp;
u_int16_t sen2Temp;
u_int16_t sen3Temp;

void setup()
{

  FastLED.addLeds<NEOPIXEL, ledPin>(senLight, numLeds);

  pinMode(ledPin, OUTPUT);
  pinMode(sen1, INPUT);
  pinMode(sen2, INPUT);
  pinMode(sen3, INPUT);
  analogReadResolution(12);
  Serial.begin(9600);
  while (!Serial)
    ;
}

void updateLights()
{
  if (sen1Temp >= 2500)
  {
    senLight[1] = CRGB::Red;
  }
  else if (sen1Temp <= 1500)
  {
    senLight[1] = CRGB::Green;
  }
  else if (sen1Temp > 1500 && sen1Temp < 2500)
  {
    senLight[1] = CRGB::Black;
  }

  if (sen2Temp >= 2500)
  {
    senLight[0] = CRGB::Red;
  }
  else if (sen2Temp <= 1500)
  {
    senLight[0] = CRGB::Green;
  }
  else if (sen2Temp > 1500 && sen2Temp < 2500)
  {
    senLight[0] = CRGB::Black;
  }

  if (sen3Temp >= 2500)
  {
    senLight[2] = CRGB::Red;
  }
  else if (sen3Temp <= 1500)
  {
    senLight[2] = CRGB::Green;
  }
  else if (sen3Temp > 1500 && sen3Temp < 2500)
  {
    senLight[2] = CRGB::Black;
  }
  FastLED.show();
}

void loop()
{

  if (!readTime.running())
  {
    sen1Temp = analogRead(sen1);
    sen2Temp = analogRead(sen2);
    sen3Temp = analogRead(sen3);
    readTime.setTime(300);

    Serial.print("Sensor 1: ");
    Serial.println(sen1Temp);

    // Serial.print("Sensor 2: ");
    // Serial.println(sen2Temp);

    // Serial.print("Sensor 3: ");
    // Serial.println(sen3Temp);
  }

  updateLights();
}
