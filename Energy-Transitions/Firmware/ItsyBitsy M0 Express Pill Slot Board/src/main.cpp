#include <Arduino.h>
#include <FastLED.h>
#include <Wire.h>
#include <i2C_Address.h>

// LED Chain Configuration
const int LED_PIN = 2;        // Data pin for LED chain
const int NUM_LEDS = 20;      // Number of LEDs in the chain

// Define the array of LEDs
CRGB leds[NUM_LEDS];

uint16_t i2cAddress = 0x08;

void setup() 
{
    Serial.begin(9600);
    //only use for debugging.
    while(!Serial);

    Serial.println("Checking I2C Address...");
    //set address pins before polling them.
    setPins();
    i2cAddress = setAddr();
    Wire.begin(i2cAddress);

    Serial.print("My address is: ");
    Serial.println(i2cAddress);

}

void loop() 
{

}

