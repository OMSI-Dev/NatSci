#include <Arduino.h>
//#include <FastLED.h>
#include <Adafruit_NeoPixel.h>

const uint8_t dataBuffer = 11;
uint8_t data[dataBuffer];

#define btn1DataPin 16
#define btn2DataPin 15
#define btn3DataPin 14
#define btn4DataPin 13
#define btn5DataPin 12

#define NUM_LEDS 44

// CRGB btn1LEDS[NUM_LEDS];
// CRGB btn2LEDS[NUM_LEDS];
// CRGB btn3LEDS[NUM_LEDS];
// CRGB btn4LEDS[NUM_LEDS];
// CRGB btn5LEDS[NUM_LEDS];

Adafruit_NeoPixel Btn1LEDS(NUM_LEDS, btn1DataPin, NEO_GRBW + NEO_KHZ800);

// Button Configuration
#define BUTTON1_PIN 2
#define BUTTON2_PIN 3
#define BUTTON3_PIN 4
#define BUTTON4_PIN 5
#define BUTTON5_PIN 6

uint8_t red = 0;
uint8_t green = 0;
uint8_t blue = 0;

// Button state tracking
// bool lastButtonState[4] = {HIGH, HIGH, HIGH, HIGH};
// bool currentButtonState[4] = {HIGH, HIGH, HIGH, HIGH};
// unsigned long lastDebounceTime[4] = {0, 0, 0, 0};
// const unsigned long debounceDelay = 50;

void setup() {
  // Initialize USB Serial for debugging
  //Serial.begin(115200);
  delay(1000);
  pinMode(13, OUTPUT);
  Serial.println("Teensy 4.0 (Child) - Starting up...");
  
  // Initialize Serial1 for communication with Teensy 4.1
  Serial1.begin(115200);
  Serial.println("Serial1 initialized for communication with 4.1");
  
  // Setup buttons with internal pullup resistors
  pinMode(BUTTON1_PIN, INPUT_PULLUP);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);
  pinMode(BUTTON3_PIN, INPUT_PULLUP);
  pinMode(BUTTON4_PIN, INPUT_PULLUP);
  pinMode(BUTTON5_PIN, INPUT_PULLUP);

  // // Initialize LED strips
  //FastLED.addLeds<WS2812, btn1DataPin, GRB>(btn1LEDS, NUM_LEDS).setRgbw(RgbwDefault());
  // FastLED.addLeds<WS2812, btn2DataPin, GRB>(btn2LEDS, NUM_LEDS).setRgbw(RgbwDefault());
  // FastLED.addLeds<WS2812, btn3DataPin, GRB>(btn3LEDS, NUM_LEDS).setRgbw(RgbwDefault());
  // FastLED.addLeds<WS2812, btn4DataPin, GRB>(btn4LEDS, NUM_LEDS).setRgbw(RgbwDefault());
  // FastLED.addLeds<WS2812, btn5DataPin, GRB>(btn5LEDS, NUM_LEDS).setRgbw(RgbwDefault());

  //prevent the overall powerdraw to 23 Watts
  //FastLED.setMaxPowerInMilliWatts(23000);
  
  // Turn off all LEDs initially
  //fill_solid(btn1LEDS, NUM_LEDS, CRGB::Black);
  // fill_solid(btn2LEDS, NUM_LEDS, CRGB::Black);
  // fill_solid(btn3LEDS, NUM_LEDS, CRGB::Black);
  // fill_solid(btn4LEDS, NUM_LEDS, CRGB::Black);
  // fill_solid(btn5LEDS, NUM_LEDS, CRGB::Black);
  //FastLED.show();

  Btn1LEDS.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  Btn1LEDS.show();            // Turn OFF all pixels ASAP
  Btn1LEDS.setBrightness(200);
 
}

void rgbValues()
{
  //set red values array postions 1 2 3
  //convert ascii to int
  uint8_t r1Temp = (data[1] - '0') * 100;
  uint8_t r2Temp = (data[2] - '0')* 10;

  red = r1Temp + r2Temp + (data[3]- '0');

  Serial.print("R1: ");
  Serial.println(r1Temp);
  Serial.print("R2: ");
  Serial.println(r2Temp); 
  Serial.print("R3: ");
  Serial.println(data[3]- '0');
  Serial.print("Total: ");
  Serial.println(red);
}


void loop() {
  //read incoming messages from 4.1
  //format 1255000000
  if (Serial.available()) 
  {
    Serial.readBytesUntil('\n', data,dataBuffer);
    Serial.println(data[0]);
    rgbValues();
  }

  
  switch (data[0])
  {
  case 49:
    // fill_solid(btn1LEDS, NUM_LEDS, CRGB(red,green,blue));
    Btn1LEDS.fill((red,green,blue),0);
    Btn1LEDS.show();
    Serial.println("Color update for button 1");
    //FastLED.show();
    break;
  
  default:
    break;
  }
  

  for(uint8_t i = 0; i<dataBuffer; i++)
  {
    data[i] = 0;
  }

  
  delay(10);  // Small delay to prevent overwhelming the serial buffer
}

//1255000000