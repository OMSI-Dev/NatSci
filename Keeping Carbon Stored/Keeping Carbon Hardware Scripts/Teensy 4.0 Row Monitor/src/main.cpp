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

Adafruit_NeoPixel Btn1LEDS(NUM_LEDS, btn1DataPin, NEO_GRBW + NEO_KHZ800);
Adafruit_NeoPixel Btn2LEDS(NUM_LEDS, btn2DataPin, NEO_GRBW + NEO_KHZ800);
Adafruit_NeoPixel Btn3LEDS(NUM_LEDS, btn3DataPin, NEO_GRBW + NEO_KHZ800);
Adafruit_NeoPixel Btn4LEDS(NUM_LEDS, btn4DataPin, NEO_GRBW + NEO_KHZ800);
Adafruit_NeoPixel Btn5LEDS(NUM_LEDS, btn5DataPin, NEO_GRBW + NEO_KHZ800);

uint8_t red = 0;
uint8_t green = 0;
uint8_t blue = 0;

// Button Configuration
#define BUTTON1_PIN 2
#define BUTTON2_PIN 3
#define BUTTON3_PIN 4
#define BUTTON4_PIN 5
#define BUTTON5_PIN 6


void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(9600);
  while(!Serial);
  delay(1000);
  //pinMode(13, OUTPUT);
  Serial.println("Teensy 4.0 (Child) - Starting up...");
  
  // Initialize Serial1 for communication with Teensy 4.1
  Serial1.begin(9600,SERIAL_8E1);
  Serial.println("Serial1 initialized for communication with 4.1");
  
  // // Setup buttons with internal pullup resistors
  pinMode(BUTTON1_PIN, INPUT_PULLUP);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);
  pinMode(BUTTON3_PIN, INPUT_PULLUP);
  pinMode(BUTTON4_PIN, INPUT_PULLUP);
  pinMode(BUTTON5_PIN, INPUT_PULLUP);

  Btn1LEDS.begin();
  Btn2LEDS.begin(); 
  Btn3LEDS.begin(); 
  Btn4LEDS.begin(); 
  Btn5LEDS.begin(); 

  Btn1LEDS.show(); 
  Btn2LEDS.show(); 
  Btn3LEDS.show(); 
  Btn4LEDS.show(); 
  Btn5LEDS.show();  

  Btn1LEDS.setBrightness(200);
  Btn2LEDS.setBrightness(200);
  Btn3LEDS.setBrightness(200);
  Btn4LEDS.setBrightness(200);
  Btn5LEDS.setBrightness(200);


 
}

void rgbValues()
{
  ///convert to packed RGB packet
  uint32_t r1Temp = (data[1] - '0') * 100;
  uint32_t r2Temp = (data[2] - '0') *  10;
  uint32_t  r3Temp = (data[3] - '0');
  
  uint32_t g1Temp = (data[4] - '0') * 100;
  uint32_t g2Temp = (data[5] - '0') *  10;
  uint32_t g3Temp = (data[6] - '0' );

  uint32_t b1Temp = (data[7] - '0') * 100;
  uint32_t b2Temp = (data[8] - '0') * 10;
  uint32_t b3Temp = (data[9] - '0');
 
  red = (r1Temp + r2Temp + r3Temp);
  green = (g1Temp + g2Temp + g3Temp);
  blue = (b1Temp + b2Temp + b3Temp);

}

void clearRGB()
{
  red = 0;
  green = 0;
  blue = 0;
}

void loop() {
  //read incoming messages from 4.1
  //format 1255000000
  
  if (Serial1.available()) 
  {
    Serial1.readBytesUntil('\n', data,dataBuffer);
    Serial.print("Button: ");
    Serial.println(data[0]);
    
    for(uint8_t i =0; i<dataBuffer; i++)
    {
      Serial.print(i);
      Serial.print(":");
      Serial.println(data[i]);
    }
    Serial.println();
   // Serial1.clear();
  }

  /*
  switch (data[0])
  {

  case 49:
    // fill_solid(btn1LEDS, NUM_LEDS, CRGB(red,green,blue));
    rgbValues();
    //Btn1LEDS.fill(255000000);
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    Btn1LEDS.show();
    Serial.println("Color update for button 1");
    clearRGB();
    //FastLED.show();

    break;

  case 50:
    rgbValues();
    Btn2LEDS.fill(Btn2LEDS.Color(red, green, blue, 0));
    Btn2LEDS.show();
    Serial.println("Color update for button 2");
     clearRGB();
    //FastLED.show();
    break;

  case 51:
    // fill_solid(btn1LEDS, NUM_LEDS, CRGB(red,green,blue));
    rgbValues();
    //Btn1LEDS.fill(255000000);
    Btn3LEDS.fill(Btn3LEDS.Color(red, green, blue, 0));
    Btn3LEDS.show();
    Serial.println("Color update for button 3");
     clearRGB();
    //FastLED.show();
    break;

  case 52:
    rgbValues();
    Btn4LEDS.fill(Btn4LEDS.Color(red, green, blue, 0));
    Btn4LEDS.show();
    Serial.println("Color update for button 4");
     clearRGB();
    //FastLED.show();
    break;

  case 53:
    rgbValues();
    Btn5LEDS.fill(Btn5LEDS.Color(red, green, blue, 0));
    Btn5LEDS.show();
    Serial.println("Color update for button 5");
     clearRGB();
    //FastLED.show();
    break;

  default:
    break;
  }
  
  for(uint8_t i = 0; i<dataBuffer; i++)
  {
  data[i] = 0;
  }
  
  delay(100);  // Small delay to prevent overwhelming the serial buffer
  */
}

//1255000000
//1000255000
//1000000255

//2255000000

//3255000000

//4255000000

//5255000000