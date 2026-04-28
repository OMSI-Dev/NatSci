#include <Arduino.h>
//#include </include/serialOverride/HardwareSerial.h>
#include <Adafruit_NeoPixel.h>
bool idle = 1;
#include <serial_handler.h>
#include <led_Handler.h>
#include <button_handler.h>



void setup() {
  //Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(1000);
  //while(!Serial);
  Serial.println("Teensy 4.0 (Child) - Starting up...");
  setSerial();
  setPins();
  
  Btn1LEDS.begin();
  Btn2LEDS.begin(); 
  Btn3LEDS.begin(); 
  Btn4LEDS.begin(); 
  Btn5LEDS.begin(); 

  clearLED(1);
  clearLED(2);
  clearLED(3);
  clearLED(4);
  clearLED(5);

  #ifndef RGB
  Btn1LEDS.setBrightness(200);
  Btn2LEDS.setBrightness(200);
  Btn3LEDS.setBrightness(200);
  Btn4LEDS.setBrightness(200);
  Btn5LEDS.setBrightness(200);
  #else
  Btn1LEDS.setBrightness(100);
  Btn2LEDS.setBrightness(100);
  Btn3LEDS.setBrightness(100);
  Btn4LEDS.setBrightness(100);
  Btn5LEDS.setBrightness(100);
  #endif


 
}


void loop() {
  //read incoming messages from 4.1
  
  readSerial();
  buttonUpdate();
  rgbValues();

  if(idle)idleButton();

  switch (data[0])
  {

  case 49:
    #ifndef RGB
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn1LEDS.show();
    Serial.println("Color update for button 1");
    clearRGB();
    Serial.println("Clear RGB Values");
    clearBuffer();
    Serial.println("Clear buffer values");
    //Set allow button press state
    Serial.println("Set button state to true.");
    buttonStates[0] = true;
    break;

  case 50:
    #ifndef RGB
    Btn2LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn2LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn2LEDS.show();
    Serial.println("Color update for button 2");
    clearRGB();
    Serial.println("Clear RGB Values");
    clearBuffer();
    Serial.println("Clear buffer values");
    //Set allow button press state
    Serial.println("Set button state to true.");
    //Set allow button press state
    buttonStates[1] = true;
    break;

  case 51:
    #ifndef RGB
    Btn3LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn3LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn3LEDS.show();
    Serial.println("Color update for button 3");
    clearRGB();
    Serial.println("Clear RGB Values");
    clearBuffer();
    Serial.println("Clear buffer values");
    Serial.println("Set button state to true.");
    buttonStates[2] = true;
    break;

  case 52:
    
    #ifndef RGB
    Btn4LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn4LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn4LEDS.show();
    Serial.println("Color update for button 4");
     clearRGB();
    Serial.println("Clear RGB Values");
    clearBuffer();
    Serial.println("Clear buffer values");
    //Set allow button press state
    Serial.println("Set button state to true.");
    //Set allow button press state
    buttonStates[3] = true;
    break;

  case 53:
    
    #ifndef RGB
    Btn5LEDS.fill(Btn1LEDS.Color(red, green, blue, 0));
    #else
    Btn5LEDS.fill(Btn1LEDS.Color(red, green, blue));
    #endif
    Btn5LEDS.show();
    Serial.println("Color update for button 5");
    clearRGB();
    Serial.println("Clear RGB Values");
    clearBuffer();
    Serial.println("Clear buffer values");
    //Set allow button press state
    Serial.println("Set button state to true.");
    //Set allow button press state
    buttonStates[4] = true;
    break;
  case 73:
    //idle mode
    idle = 1;
    Serial.println("Set to idle mode.");
    clearBuffer();
    Serial.println("Clear buffer values");
  default:
    break;
  }
  
}

