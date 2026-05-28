#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
bool idle = 1;
#include <serial_handler.h>
#include <led_Handler.h>
#include <button_handler.h>

void correctData();

void setup()
{
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  //delay(1000);
  //while(!Serial);
  setPins();
  Serial.println("Teensy 4.0 (Child) - Starting up...");
  setSerial();
  

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
  Btn1LEDS.setBrightness(150);
  Btn2LEDS.setBrightness(150);
  Btn3LEDS.setBrightness(150);
  Btn4LEDS.setBrightness(150);
  Btn5LEDS.setBrightness(150);
#endif
}

void loop()
{
  // read incoming messages from 4.1
  clearBuffer();
  readSerial();
  buttonUpdate();
  rgbValues();
  correctData();
  idleButton();
  // updateLED(data[0]);
/* switch (data[0])
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

    buttonStates[0] = true;
    Serial.println("Set button state to true.");
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

    buttonStates[1] = true;
    Serial.println("Set button state to true.");
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

    buttonStates[2] = true;
    Serial.println("Set button state to true.");
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

    buttonStates[3] = true;
    Serial.println("Set button state to true.");
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

    Serial.println("Set button state to true.");
    // Set allow button press state
    buttonStates[4] = true;
    break;
  case 73:
    // idle mode
    idle = 1;
    Serial.println("Set to idle mode.");
    clearBuffer();
    Serial.println("Clear buffer values");
  default:
    break;
  }
    
*/
}

void correctData()
{
    if(data[0] == '2')
    {
        red = 255;
        green = 0;
        blue = 0;

        Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue));
        Btn1LEDS.show();

        Btn3LEDS.fill(Btn3LEDS.Color(red, green, blue));
        Btn3LEDS.show();        

        Btn5LEDS.fill(Btn5LEDS.Color(red, green, blue));
        Btn5LEDS.show();
        buttonStates[0] = true;
        buttonStates[2] = true;
        buttonStates[4] = true;
    }

       if(data[0] == '1')
    {
        red = 255;
        green = 0;
        blue = 0;

        Btn2LEDS.fill(Btn2LEDS.Color(red, green, blue));
        Btn2LEDS.show();

        Btn4LEDS.fill(Btn4LEDS.Color(red, green, blue));
        Btn4LEDS.show();    
        buttonStates[1] = true;
        buttonStates[3] = true;    
    }

    if(data[0] == '1')
    {
        red = 0;
        green = 0;
        blue = 0;

        Btn2LEDS.fill(Btn2LEDS.Color(red, green, blue));
        Btn2LEDS.show();

        Btn4LEDS.fill(Btn4LEDS.Color(red, green, blue));
        Btn4LEDS.show();    
        buttonStates[1] = true;
        buttonStates[3] = true;    
    }


    if(data[0] == 73)
    {
        red = 0;
        green = 0;
        blue = 0;

        Btn1LEDS.fill(Btn1LEDS.Color(red, green, blue));
        Btn1LEDS.show();

        Btn2LEDS.fill(Btn2LEDS.Color(red, green, blue));
        Btn2LEDS.show();    

        Btn3LEDS.fill(Btn3LEDS.Color(red, green, blue));
        Btn4LEDS.show();

        Btn4LEDS.fill(Btn4LEDS.Color(red, green, blue));
        Btn4LEDS.show();    

        Btn5LEDS.fill(Btn5LEDS.Color(red, green, blue));
        Btn5LEDS.show();   

        buttonStates[0] = true;
        buttonStates[1] = true;
        buttonStates[2] = true;  
        buttonStates[3] = true;
        buttonStates[4] = true;    
    }


}