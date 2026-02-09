#include "Haxx.h"

Haxx<3>::Haxx()
    : ring(&med[0]),center(&med[12]),fade(), speed()
{
}

void Haxx<3>::setupLEDs(uint8_t pin, uint8_t pixelNumber)
{
    switch(pin)
    {
        case 0:
            FastLED.addLeds<WS2812B, 0, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 1:
            FastLED.addLeds<WS2812B, 1, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 2:
            FastLED.addLeds<WS2812B, 2, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 3:
            FastLED.addLeds<WS2812B, 3, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 4:
            FastLED.addLeds<WS2812B, 4, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 5:
            FastLED.addLeds<WS2812B, 5, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 6:
            FastLED.addLeds<WS2812B, 6, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 7:
            FastLED.addLeds<WS2812B, 7, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 8:
            FastLED.addLeds<WS2812B, 8, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 9:
            FastLED.addLeds<WS2812B, 9, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 10:
            FastLED.addLeds<WS2812B, 10, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 11:
            FastLED.addLeds<WS2812B, 11, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 12:
            FastLED.addLeds<WS2812B, 12, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 13:
            FastLED.addLeds<WS2812B, 13, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 14:
            FastLED.addLeds<WS2812B, 14, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 15:
            FastLED.addLeds<WS2812B, 15, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 16:
            FastLED.addLeds<WS2812B, 16, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 17:
            FastLED.addLeds<WS2812B, 17, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 18:
            FastLED.addLeds<WS2812B, 18, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 19:
            FastLED.addLeds<WS2812B, 19, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 20:
            FastLED.addLeds<WS2812B, 20, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 21:
            FastLED.addLeds<WS2812B, 21, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 22:
            FastLED.addLeds<WS2812B, 22, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 23:
            FastLED.addLeds<WS2812B, 23, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;
        case 24:
            FastLED.addLeds<WS2812B, 24, GRB>(this->med, pixelNumber).setCorrection(TypicalSMD5050);
            break;                
    }
}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param inDataPin the datapin the LEDs are attached to.
 * @param brightness 0-255 max brightness of leds. The default brightness value is set to 155, do not raise unless you have a proper powersupply.
 */
void Haxx<3>::attach(uint8_t inDataPin, uint8_t brightness)
{   
    this->DataPin = inDataPin;
    //pass this data pin and the med pixelcount, set brighness
    setupLEDs(this->DataPin, pixelCount);
    FastLED.setBrightness(brightness);
}



/**
 * @brief full button sets to Red.
 */
void Haxx<3>::red()
{
    fill_solid(this->med, pixelCount, CRGB::Red);
    FastLED.show();     
}

/**
 * @brief full button sets to Green.
 */
void Haxx<3>::green()
{
    fill_solid(this->med, pixelCount, CRGB::Green);
    FastLED.show();     
}

/**
 * @brief full button sets to Blue.
 */
void Haxx<3>::blue()
{
    fill_solid(this->med, pixelCount, CRGB::Blue);
    FastLED.show();     
}

/**
 * @brief full button sets to Blue.
 */
void Haxx<3>::off()
{
    fill_solid(this->med, pixelCount, CRGB::Black);
    FastLED.show();     
}

/**
 * @brief This will return a true when the timer is finished,
 * you will need to control the logic or the timer will loop.
 * @param time the full amount of time the ring repersents, pass 0 if you want to restart the timer
 * @param r - red value
 * @param g - green value
 * @param b - blue value
 * @param flash - Enabled by default, when finished lights will blink for about 2 seconds.
 * @param reset - send a reset signal, if the timer needs to be ended early - default off
 */
bool Haxx<3>::ringTimer(uint32_t time,uint8_t r,uint8_t g,uint8_t b,bool flash,bool reset)
{   
    
    if(reset || time == 0)
    {
        this->flashingCount = 0;
        this->timeLEDcount = 0;
        fill_solid(this->med,ringNumLeds,CRGB::Black);
        FastLED.show();   
        this->finished = false;
        return this->finished;
    }

    this->setTime = time/12;

    if(this->timeLEDcount == 0)
    {   fill_solid(this->med,ringNumLeds,CRGB(r,g,b));
        FastLED.show();
        this->finished = false;
        this->ringTiming.setTime(setTime);
        timeLEDcount++;
    }

    
        if(!this->ringTiming.running() &&  this->timeLEDcount <= 12)
        {       

            fill_solid(this->med,ringNumLeds,CRGB(r,g,b));
            for(uint8_t leds = 0; leds <= this->timeLEDcount; leds++)
            {
                this->med[12-leds] = CRGB::Black;
            }
                              

            FastLED.show();

            if(this->timeLEDcount <= 12 && flashingCount == 0)
            {               
                this->finished = false;
                this->ringTiming.setTime(setTime); 
            }
            if(this->timeLEDcount <= 12)
            {
                this->timeLEDcount++; 
            }
        }

if(flash && this->timeLEDcount > 12)
    {
        if(!this->flashTimer.running())
        {
            this->flashingCount++;
            this->flashTimer.setTime(250);
        }

        if(this->flashingCount % 2 != 0)
        {
            fill_solid(this->med,ringNumLeds,CRGB(r,g,b));
        }else
        {
            fill_solid(this->med,ringNumLeds,CRGB::Black);
        }


        FastLED.show();

        if(this->flashingCount == 8)
        {
            this->flashingCount = 0;
            this->timeLEDcount = 0;
             fill_solid(this->med,ringNumLeds,CRGB::Black);
             FastLED.show();       
            this->finished = true;
            return this->finished;
        }

     }else if(!flash && this->timeLEDcount >= 12)
    {
        this->flashingCount = 0;
        this->timeLEDcount = 0;
        fill_solid(this->med,ringNumLeds,CRGB::Black);
        FastLED.show(); 
        this->finished = true;
        return this->finished;
    }        

    return this->finished;

}

/**
 * @brief Fill center of button a solid RGB color.
 * @param r - red value (0-255)
 * @param g - green value (0-255)
 * @param b - blue value (0-255)
*/
void Haxx<3>::centerFill(uint8_t r,uint8_t g,uint8_t b)
{
    fill_solid(this->center,centerNumLeds,CRGB(r,g,b));
    FastLED.show();
}

/**
 * @brief Fill ring of button a solid RGB color.
 * @param r - red value (0-255)
 * @param g - green value (0-255)
 * @param b - blue value (0-255)
*/
void Haxx<3>::ringFill(uint8_t r,uint8_t g,uint8_t b)
{
    fill_solid(this->ring,centerNumLeds,CRGB(r,g,b));
    FastLED.show();
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
void Haxx<3>::chase(uint8_t r, uint8_t g, uint8_t b, uint16_t rate, uint8_t fadeRate, uint8_t section)
{
    if (section > 2)
    {
        // Handle invalid section value
        section = 0;
    }

    if(this->chasei > arraySize){ this->chasei = 0; }

    if(section == 0)
    {
        if(!speed.running())
        {
            this->med[this->chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->med, pixelCount, fadeRate);    

            this->speed.setTime(rate);
            this->chasei++;
        }
    }

    if(section == 1)
    {
        if(!speed.running())
        {
        if(this->chasei>11){this->chasei = 0;}
            this->ring[this->chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->ring, ringNumLeds, fadeRate);    
       
            this->speed.setTime(rate);
            this->chasei++;
        }
    }

    if(section == 2)
    {
        if(!speed.running())
        {
            if(this->chasei>pixelCount){this->chasei = 0;}
            this->med[this->chasei] = CRGB(r, g, b);
            FastLED.show();
            fadeToBlackBy(this->med, pixelCount, fadeRate);    

            this->speed.setTime(rate);
            this->chasei++;
        }

    }

}
