/*
  Pixie requires 5V logic, will not work with Teensy without logic converter
  This example executes an animation cycle of rgb rainbow 
*/

#include "Adafruit_Pixie.h"

#include "SoftwareSerial.h"
#define PIXIEPIN  6 // GPIO
SoftwareSerial pixieSerial(-1, PIXIEPIN);

#define NUMPIXELS 1 
Adafruit_Pixie strip = Adafruit_Pixie(NUMPIXELS, &pixieSerial);

uint32_t Wheel(byte WheelPos) {
  if(WheelPos < 85) {
   return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
  } else if(WheelPos < 170) {
   WheelPos -= 85;
   return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } else {
   WheelPos -= 170;
   return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
}

void rainbowCycle(uint8_t wait) {
  uint16_t i, j;

  for(j=0; j<256*5; j++) { // 5 cycles of all colors on wheel
    for(i=0; i< NUMPIXELS; i++) {
      strip.setPixelColor(i, Wheel(((i * 256 / strip.numPixels()) + j) & 255));
    }
    strip.show();
    delay(wait);
  }
}

void setup() {
  int i;

  Serial.begin(9600);
  Serial.println("Ready to Pixie!");

  pixieSerial.begin(115200); // Pixie REQUIRES this baud rate

  strip.setBrightness(200);  // Adjust as necessary to avoid blinding

  Serial.println("Red!");
  for(i=0; i< NUMPIXELS; i++)
    strip.setPixelColor(i, 255, 0, 0);
  strip.show();
  delay(300);

  Serial.println("Green!");
  for(i=0; i< NUMPIXELS; i++)
    strip.setPixelColor(i, 0, 255, 0);
  strip.show();
  delay(300);

  Serial.println("Blue!");
  for(i=0; i< NUMPIXELS; i++)
    strip.setPixelColor(i, 0, 0, 255);
  strip.show();
  delay(300);
}

void loop() {
  Serial.println("Rainbow!");
  rainbowCycle(10);
}



