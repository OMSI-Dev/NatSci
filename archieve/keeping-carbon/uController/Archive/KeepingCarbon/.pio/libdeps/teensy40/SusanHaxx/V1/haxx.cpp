#include "haxx.h"

#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)
#define PRINT_COMPILE_MESSAGE(msg) \
    _Pragma(STRINGIFY(message(__FILE__ "(" TOSTRING(__LINE__) "): " msg)))


haxx::haxx()
    : fade(), speed(), armSpeed(), centerPulse()
{
}

// , btnCenter(&haxxLight[12]), ringLight(&haxxLight[0])

uint8_t haxx::getButtonSize()
{
    return this->pixelCount;
}

void haxx::setupLEDs(uint8_t pin, uint8_t pixelNumber)
{
//29
   
    if(pixelNumber == jumboSize)
    {
        switch(pin)
        {
            case 0:
                FastLED.addLeds<WS2812B, 0, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 1:
                FastLED.addLeds<WS2812B, 1, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 2:
                FastLED.addLeds<WS2812B, 2, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 3:
                FastLED.addLeds<WS2812B, 3, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 4:
                FastLED.addLeds<WS2812B, 4, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 5:
                FastLED.addLeds<WS2812B, 5, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 6:
                FastLED.addLeds<WS2812B, 6, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 7:
                FastLED.addLeds<WS2812B, 7, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 8:
                FastLED.addLeds<WS2812B, 8, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 9:
                FastLED.addLeds<WS2812B, 9, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 10:
                FastLED.addLeds<WS2812B, 10, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 11:
                FastLED.addLeds<WS2812B, 11, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 12:
                FastLED.addLeds<WS2812B, 12, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 13:
                FastLED.addLeds<WS2812B, 13, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 14:
                FastLED.addLeds<WS2812B, 14, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 15:
                FastLED.addLeds<WS2812B, 15, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 16:
                FastLED.addLeds<WS2812B, 16, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 17:
                FastLED.addLeds<WS2812B, 17, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 18:
                FastLED.addLeds<WS2812B, 18, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 19:
                FastLED.addLeds<WS2812B, 19, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 20:
                FastLED.addLeds<WS2812B, 20, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 21:
                FastLED.addLeds<WS2812B, 21, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 22:
                FastLED.addLeds<WS2812B, 22, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 23:
                FastLED.addLeds<WS2812B, 23, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 24:
                FastLED.addLeds<WS2812B, 24, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 54:
                FastLED.addLeds<WS2812B, 54, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 59:
                FastLED.addLeds<WS2812B, 59, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 56:
                FastLED.addLeds<WS2812B, 56, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 57:
                FastLED.addLeds<WS2812B, 57, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break; 
            case 58:
                FastLED.addLeds<WS2812B, 58, GRB>(this->jumboBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;                       
        }
    }
    if(pixelNumber == largeSize)

    {
        switch(pin)
        {
            case 0:
                FastLED.addLeds<WS2812B, 0, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 1:
                FastLED.addLeds<WS2812B, 1, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 2:
                FastLED.addLeds<WS2812B, 2, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 3:
                FastLED.addLeds<WS2812B, 3, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 4:
                FastLED.addLeds<WS2812B, 4, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 5:
                FastLED.addLeds<WS2812B, 5, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 6:
                FastLED.addLeds<WS2812B, 6, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 7:
                FastLED.addLeds<WS2812B, 7, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 8:
                FastLED.addLeds<WS2812B, 8, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 9:
                FastLED.addLeds<WS2812B, 9, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 10:
                FastLED.addLeds<WS2812B, 10, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 11:
                FastLED.addLeds<WS2812B, 11, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 12:
                FastLED.addLeds<WS2812B, 12, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 13:
                FastLED.addLeds<WS2812B, 13, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 14:
                FastLED.addLeds<WS2812B, 14, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 15:
                FastLED.addLeds<WS2812B, 15, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 16:
                FastLED.addLeds<WS2812B, 16, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 17:
                FastLED.addLeds<WS2812B, 17, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 18:
                FastLED.addLeds<WS2812B, 18, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 19:
                FastLED.addLeds<WS2812B, 19, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 20:
                FastLED.addLeds<WS2812B, 20, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 21:
                FastLED.addLeds<WS2812B, 21, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 22:
                FastLED.addLeds<WS2812B, 22, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 23:
                FastLED.addLeds<WS2812B, 23, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 24:
                FastLED.addLeds<WS2812B, 24, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 54:
                FastLED.addLeds<WS2812B, 54, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 59:
                FastLED.addLeds<WS2812B, 59, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 56:
                FastLED.addLeds<WS2812B, 56, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 57:
                FastLED.addLeds<WS2812B, 57, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break; 
            case 58:
                FastLED.addLeds<WS2812B, 58, GRB>(this->largeBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;                       
        }
    }  
    if(pixelNumber == medSize)
    {
        switch(pin)
        {
            case 0:
                FastLED.addLeds<WS2812B, 0, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 1:
                FastLED.addLeds<WS2812B, 1, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 2:
                FastLED.addLeds<WS2812B, 2, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 3:
                FastLED.addLeds<WS2812B, 3, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 4:
                FastLED.addLeds<WS2812B, 4, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 5:
                FastLED.addLeds<WS2812B, 5, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 6:
                FastLED.addLeds<WS2812B, 6, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 7:
                FastLED.addLeds<WS2812B, 7, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 8:
                FastLED.addLeds<WS2812B, 8, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 9:
                FastLED.addLeds<WS2812B, 9, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 10:
                FastLED.addLeds<WS2812B, 10, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 11:
                FastLED.addLeds<WS2812B, 11, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 12:
                FastLED.addLeds<WS2812B, 12, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 13:
                FastLED.addLeds<WS2812B, 13, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 14:
                FastLED.addLeds<WS2812B, 14, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 15:
                FastLED.addLeds<WS2812B, 15, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 16:
                FastLED.addLeds<WS2812B, 16, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 17:
                FastLED.addLeds<WS2812B, 17, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 18:
                FastLED.addLeds<WS2812B, 18, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 19:
                FastLED.addLeds<WS2812B, 19, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 20:
                FastLED.addLeds<WS2812B, 20, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 21:
                FastLED.addLeds<WS2812B, 21, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 22:
                FastLED.addLeds<WS2812B, 22, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 23:
                FastLED.addLeds<WS2812B, 23, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 24:
                FastLED.addLeds<WS2812B, 24, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 54:
                FastLED.addLeds<WS2812B, 54, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 59:
                FastLED.addLeds<WS2812B, 59, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 56:
                FastLED.addLeds<WS2812B, 56, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;
            case 57:
                FastLED.addLeds<WS2812B, 57, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break; 
            case 58:
                FastLED.addLeds<WS2812B, 58, GRB>(this->medBtn, pixelNumber).setCorrection(TypicalSMD5050);
                break;                       
        }
    }  

}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param inDataPin the datapin the LEDs are attached to.
 * @param btnType 0 = Jumbo, 1 = Large, 2 = Medium. 
 * @param value 0-255 max brightness of leds. The default brightness value is set to 155, do not raise unless you have a proper powersupply.
 */
void haxx::attach(uint8_t inDataPin, uint8_t btnType, uint8_t value)
{   
    this->DataPin = inDataPin;
    if(btnType == 0)
    {
        this->pixelCount = jumboSize; //Center plus Ring
    }
    if(btnType == 1)
    {
        this->pixelCount = largeSize ; //Center plus Ring
    }
    if(btnType ==2) 
    {
        this->pixelCount = medSize; //Center plus Ring
    }
    
    
    setupLEDs(this->DataPin, this->pixelCount);
    FastLED.setBrightness(value);
}

void haxx::update(bool enable)
{
    //currently not implemented
}

/**
 * @brief Create a chase with a fading tail
 * 
 * @param r Red color component (0-255).
 * @param g Green color component (0-255).
 * @param b Blue color component (0-255).
 * @param rate How fast to chase in millis
 * @param fadeRate 0-255 creates a varying brightness/length of tail
 * @param section 0 - full button, 1 - ring, 2 - center (if set higher than 2 it defaults to full button)
 */

void haxx::chase(uint8_t r, uint8_t g, uint8_t b, uint16_t rate, uint8_t fadeRate, uint8_t section)
{
    arraySize = this->pixelCount;

    if (section > 2)
    {
        // Handle invalid section value
        section = 0;
    }

    if(chasei > arraySize){ chasei = 0; }

    if(section == 0)
    {
        if(!speed.running())
        {
            switch (this->pixelCount)
            {
            case jumboSize:
            this->jumboBtn[chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->jumboBtn, jumboSize-5, fadeRate);            
            break;
            case largeSize:
            this->largeBtn[chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->largeBtn, largeSize-5, fadeRate);      
            break;
            case medSize:
            this->medBtn[chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->medBtn, medSize-5, fadeRate);    
            break;
            }
            this->speed.setTime(rate);
            chasei++;
        }
    }

    if(section == 1)
    {
        if(chasei > 11){ chasei = 0; }
        if(!this->speed.running())
        {
            this->ringLight[chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->ringLight, 12, fadeRate);
            this->speed.setTime(rate);
            chasei++;
        }

    }

    if(section == 2)
    {
        if(chasei > this->pixelCount){ chasei = 0; }
        if(!this->speed.running())
        {
            this->btnCenter[chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->btnCenter, 19, fadeRate);
            speed.setTime(rate);
            chasei++;
        }

    }

}

/**
 * @brief Fill just the center as an RGB value
 * 
 * @param r Red color component (0-255).
 * @param g Green color component (0-255).
 * @param b Blue color component (0-255).
 */

void haxx::centerFill(uint8_t r, uint8_t g, uint8_t b)
{
    switch (this->pixelCount)
    {
    case jumboSize:
    fill_solid(this->btnCenter, this->pixelCount, CRGB(r, g, b));
    FastLED.show();         
    break;
    case largeSize:
    fill_solid(this->btnCenter, this->pixelCount, CRGB(r, g, b));
    FastLED.show();    
    break;
    case medSize:
    fill_solid(this->btnCenter, this->pixelCount, CRGB(r, g, b));
    FastLED.show();  
    break;
    }

}

/**
 * @brief Fill just the outer ring as an RGB value
 * 
 * @param r Red color component (0-255).
 * @param g Green color component (0-255).
 * @param b Blue color component (0-255).
 */
 void haxx::ringFill(uint8_t r,uint8_t g,uint8_t b)
 {
    switch (this->pixelCount)
    {
    case jumboSize:
    fill_solid(this->ringLight, ringNumLeds, CRGB(r, g, b));
    FastLED.show();      
    break;
    case largeSize:
    fill_solid(this->ringLight, ringNumLeds, CRGB(r, g, b));
    FastLED.show();    
    break;
    case medSize:
    fill_solid(this->ringLight, ringNumLeds, CRGB(r, g, b));
    FastLED.show();   
    break;
    }
 }

/**
 * @brief full button sets to Red.
 */
void haxx::red()
{
    switch (this->pixelCount)
    {
    case jumboSize:
    fill_solid(this->jumboBtn, jumboSize, CRGB::Red);
    FastLED.show();  
    break;
    case largeSize:
    fill_solid(this->largeBtn, largeSize, CRGB::Red);
    FastLED.show();    
    break;
    case medSize:
    fill_solid(this->medBtn, medSize, CRGB::Red);
    FastLED.show();   
    break;
    }     
}

/**
 * @brief full button sets to Red.
 */
void haxx::green()
{
    switch (this->pixelCount)
    {
    case jumboSize:
    fill_solid(this->jumboBtn, jumboSize, CRGB::Green);
    FastLED.show();  
    break;
    case largeSize:
    fill_solid(this->largeBtn, largeSize, CRGB::Green);
    FastLED.show();    
    break;
    case medSize:
    fill_solid(this->medBtn, medSize, CRGB::Green);
    FastLED.show();   
    break;
    }    
}

/**
 * @brief full button sets to Red.
 */

void haxx::blue()
{
    switch (this->pixelCount)
    {
    case jumboSize:
    fill_solid(this->jumboBtn, jumboSize, CRGB::Blue);
    FastLED.show();  
    break;
    case largeSize:
    fill_solid(this->largeBtn, largeSize, CRGB::Blue);
    FastLED.show();    
    break;
    case medSize:
    fill_solid(this->medBtn, medSize, CRGB::Blue);
    FastLED.show();   
    break;
    }   
}


void haxx::edgeFade(uint8_t scale)
{
    nscale8_video(btnCenter,1,scale);
    nscale8_video(btnCenter+1,1,scale);
    nscale8_video(btnCenter+2,1,scale);
    nscale8_video(btnCenter+6,1,scale);
    nscale8_video(btnCenter+7,1,scale);
    nscale8_video(btnCenter+15,1,scale);
    nscale8_video(btnCenter+16,1,scale);
    nscale8_video(btnCenter+17,1,scale);
    nscale8_video(btnCenter+18,1,scale);
    nscale8_video(btnCenter+12,1,scale);
    nscale8_video(btnCenter+11,1,scale);
    nscale8_video(btnCenter+3,1,scale);
}

void haxx::midFade(uint8_t scale)
{
    nscale8_video(btnCenter+4,1,scale);
    nscale8_video(btnCenter+5,1,scale);
    nscale8_video(btnCenter+8,1,scale);
    nscale8_video(btnCenter+14,1,scale);
    nscale8_video(btnCenter+13,1,scale);
    nscale8_video(btnCenter+10,1,scale);

}


/**
 * @brief Creates a spinning 'arm'
 * 
 * @param r Red color component (0-255).
 * @param g Green color component (0-255).
 * @param b Blue color component (0-255).
 * @param rate Update rate for the effect.
 * @param numArms 1-4 arms spinning at once, above 4 defaults to 1.
 */

// void haxx::radar(uint8_t r, uint8_t g, uint8_t b, uint16_t rate,bool dir, uint8_t numArms)
// {

//   if(!armSpeed.running())
//     {
//         fadeToBlackBy(btnCenter,19,255);
//         haxxLight[swirlArm[0]] = CRGB(r,g,b);
//         if(swirli ==0)
//         {
//             if(numArms == 1)
//             {            
//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b);
//             }
//             if(numArms == 2)
//             {
//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b);
//             }
//             if(numArms == 3)
//             {
//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b);

//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b);
//             }               
//             if(numArms == 4)
//             {
//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b);

//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b);
//             }   
//             dir ? swirli++ : swirli--;
//         }
//         else if(swirli ==1)
//         {

//             if(numArms == 1)
//             {            
//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b);
//             }
//             if(numArms == 2)
//             {
//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b);
//             }
//             if(numArms == 3)
//             {
//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b);

//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b);
//             }               
//             if(numArms == 4)
//             {
//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b);

//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b);
//             }   
//             dir ? swirli++ : swirli--;
//         }
//         else if(swirli ==2)
//         {
//             if(numArms == 1)
//             {            
//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b);
//             }
//             if(numArms == 2)
//             {
//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b);
//             }
//             if(numArms == 3)
//             {
//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b);

//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b);
//             }               
//             if(numArms == 4)
//             {
//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b);

//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b);
//             }   
//             dir ? swirli++ : swirli--;
//         }
//         else if(swirli ==3)
//         {
//             if(numArms == 1)
//             {            
//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b);
//             }
//             if(numArms == 2)
//             {
//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b);
//             }
//             if(numArms == 3)
//             {
//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b);

//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b);
//             }               
//             if(numArms == 4)
//             {
//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b);

//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b);
//             }   
//             dir ? swirli++ : swirli--;
//         }       
//         else if(swirli ==4)
//         {
//             if(numArms == 1)
//             {            
//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b);
//             }
//             if(numArms == 2)
//             {
//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b);
//             }
//             if(numArms == 3)
//             {
//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b);

//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b);
//             }               
//             if(numArms == 4)
//             {
//             haxxLight[swirlArm[9]] = CRGB(r,g,b);
//             haxxLight[swirlArm[10]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b);

//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b);
//             }   
//             dir ? swirli++ : swirli--;
//         }
//         else if(swirli ==5)
//         {
//             if(numArms == 1)
//             {            
//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b);
//             }
//             if(numArms == 2)
//             {
//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b);
//             }
//             if(numArms == 3)
//             {
//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[3]] = CRGB(r,g,b);
//             haxxLight[swirlArm[4]] = CRGB(r,g,b);

//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b);
//             }               
//             if(numArms == 4)
//             {
//             haxxLight[swirlArm[11]] = CRGB(r,g,b);
//             haxxLight[swirlArm[12]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[1]] = CRGB(r,g,b);
//             haxxLight[swirlArm[2]] = CRGB(r,g,b);

//             haxxLight[swirlArm[7]] = CRGB(r,g,b);
//             haxxLight[swirlArm[8]] = CRGB(r,g,b); 

//             haxxLight[swirlArm[5]] = CRGB(r,g,b);
//             haxxLight[swirlArm[6]] = CRGB(r,g,b);
//             }   

//             dir ? swirli++ : swirli--;
//         }
//         armSpeed.setTime(rate);
//         FastLED.show();
//     }  


//     if(dir)
//     {
//         if(swirli==6){swirli =0;}
//         }
//         else
//         {
//         if(swirli<0){swirli=5;}        
//     }

// }

/**
 * @brief Create a ripple starting from the center out
 * 
 * @param r Red color component (0-255).
 * @param g Green color component (0-255).
 * @param b Blue color component (0-255).
 * @param rate Update rate for the effect. 100-150 provide good results.
 * @param dir Change direction from center to edge or edge to center
 * 
 */
// void haxx::centerRings(uint8_t r, uint8_t g, uint8_t b, uint16_t rate, bool dir)
// {
//     FastLED.setDither(BINARY_DITHER);

//     if(!centerPulse.running())
//     {
//         //set the sections colors
//         haxxLight[21] = CRGB(r,g,b);

//         for (uint8_t i = 0; i < midNumLeds; i++)
//         {
//             haxxLight[btnCenterMidRing[i]] = CRGB(r,g,b);
//         }

//         for (uint8_t i = 0; i < edgeNumLeds; i++)
//         {
//             haxxLight[btnCenterEdgeRing[i]] = CRGB(r,g,b);
//         }

//         if(pulseState == 0)
//         {  
//             nscale8_video(btnCenter+9,1,100);   
//             midFade(16);
//             edgeFade(100);
//             FastLED.show();
//             pulseState = dir ? 5 : 1;
//             centerPulse.setTime(rate);
//         }
//         else if(pulseState == 1)
//         {   
//             nscale8_video(btnCenter+9,1,80);     
//             midFade(32);
//             edgeFade(80);
//             FastLED.show();
//             pulseState = dir ? 0 : 2;
//             centerPulse.setTime(rate);
//         }
//         else if(pulseState == 2)
//         {   
//             nscale8_video(btnCenter+9,1,70);     
//             midFade(48);
//             edgeFade(64);
//             FastLED.show();
//             pulseState = dir ? 1 : 3;
//             centerPulse.setTime(rate);
//         }
//         else if(pulseState == 3)
//         {      
//             nscale8_video(btnCenter+9,1,60);  
//             midFade(64);
//             edgeFade(48);
//             FastLED.show();
//             pulseState = dir ? 2 : 4;
//             centerPulse.setTime(rate);
//         }
//         else if(pulseState == 4)
//         {  
//             nscale8_video(btnCenter+9,1,50);      
//             midFade(80);
//             edgeFade(32);
//             FastLED.show();
//             pulseState = dir ? 3 : 5;
//             centerPulse.setTime(rate);
//         }
//         else if(pulseState == 5)
//         {   
//             nscale8_video(btnCenter+9,1,40);     
//             midFade(100);
//             edgeFade(16);
//             FastLED.show();
//             pulseState = dir ? 4 : 0;
//             centerPulse.setTime(rate);
//         }                
//      }

// }

/**
 * @brief full button sets to off.
 */
void haxx::off()
{
    switch (this->pixelCount)
    {
    case jumboSize:
    fill_solid(this->jumboBtn, jumboSize, CRGB::Black);
    FastLED.show();  
    break;
    case largeSize:
    fill_solid(this->largeBtn, largeSize, CRGB::Black);
    FastLED.show();    
    break;
    case medSize:
    fill_solid(this->medBtn, medSize, CRGB::Black);
    FastLED.show();   
    break;
    }   
}

/**
 * @brief shifting rainbow on center.
 */
// void haxx::loading(uint16_t rate)
// {
//     fill_rainbow_circular(btnCenter,centerNumLeds,hue);
//     if(!centerPulse.running())
//     {
//         hue++;
//         centerPulse.setTime(25);
//         if(hue==255){hue=0;}
//     }
//     FastLED.show();
// }