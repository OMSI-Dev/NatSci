#include <Arduino.h>
#include <FastLED.h>
#include <Wire.h>

const uint8_t LED_PIN = 2;
const uint8_t ONBOARD_LED = 13;
const uint8_t NUM_LEDS = 20;

const uint8_t HEADER_PIN_A = 3;
const uint8_t HEADER_PIN_B = 4;
const uint8_t HEADER_PIN_C = 5;
const uint8_t HEADER_PIN_D = 7;

const uint8_t I2C_BASE_ADDRESS = 0x08;

CRGB leds[NUM_LEDS];

uint8_t myI2CAddress = 0;
volatile uint8_t ledState = 0;
volatile bool newDataReceived = false;

uint8_t readAddressOffset() {
  uint8_t offset = 0;
  if (digitalRead(HEADER_PIN_A)) offset |= 0x01;
  if (digitalRead(HEADER_PIN_B)) offset |= 0x02;
  if (digitalRead(HEADER_PIN_C)) offset |= 0x04;
  if (digitalRead(HEADER_PIN_D)) offset |= 0x08;
  return offset;
}

void setAllLeds(const CRGB &color) {
  fill_solid(leds, NUM_LEDS, color);
  FastLED.show();
}

void receiveEvent(int numBytes) {
  if (numBytes <= 0) return;

  ledState = Wire.read();
  while (Wire.available()) {
    Wire.read();
  }
  newDataReceived = true;
}

void setup() {
  Serial.begin(115200);

  pinMode(ONBOARD_LED, OUTPUT);
  digitalWrite(ONBOARD_LED, LOW);

  pinMode(HEADER_PIN_A, INPUT_PULLDOWN);
  pinMode(HEADER_PIN_B, INPUT_PULLDOWN);
  pinMode(HEADER_PIN_C, INPUT_PULLDOWN);
  pinMode(HEADER_PIN_D, INPUT_PULLDOWN);
  delay(20);

  myI2CAddress = I2C_BASE_ADDRESS + readAddressOffset();

  pinMode(PIN_WIRE_SDA, INPUT_PULLUP);
  pinMode(PIN_WIRE_SCL, INPUT_PULLUP);
  Wire.begin(myI2CAddress);
  Wire.onReceive(receiveEvent);

  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(50);
  FastLED.clear();
  FastLED.show();

  Serial.print("I2C address: 0x");
  Serial.println(myI2CAddress, HEX);
}

void loop() {
  if (newDataReceived) {
    newDataReceived = false;

    digitalWrite(ONBOARD_LED, ledState ? HIGH : LOW);

    if (ledState) {
      setAllLeds(CRGB::White);
    } else {
      FastLED.clear();
      FastLED.show();
    }
  }

  delay(5);
}
