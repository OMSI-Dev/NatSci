/*
This uses the GPL-3.0 Licence.

It uses the MoToTimer from the MoBaTool library for timing.
https://github.com/MicroBahner/MobaTools

***Using the modified OMSI Timer that is a stripped down version of Mobatools*****


*/


#include <Pulse.h>

Pulse::Pulse() 
    : lightRaise(), lightLower(), PWMpin(0), pulseEnable(false), rate(10),
      maxVal(255), minVal(0), increment(5), tick(0), En(0)
{}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param attach the datapin the LED attached to.
 */
void Pulse::attach(int8_t inPWMpin)
{   
    this->PWMpin = inPWMpin;
}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param setRate the rate at which the pulse updates
 */
void Pulse::setRate(int8_t inRate)
{
    this->rate = inRate;
}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param setMax Max brightness the led will hit before fading out. 125 is a good high when not diffusing.
 */
void Pulse::setMax(int8_t inMaxVal)
{
    this->maxVal = inMaxVal;
}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param setMin min brightness the light will get to before starting to fade up
 */
void Pulse::setMin(int8_t inMinVal)
{
    this->minVal = inMinVal;
}

/**
 * @brief Attachs the lights to a pin on the board, supports 0-23, defaults to 0;
 * @param setIncrement how much does each interval increase. ie every 5ms increase/decrease by 5
 */
void Pulse::setIncrement(int8_t inIncrement)
{
    this->increment = inIncrement;
}


void Pulse::update(bool inPulseEnable)
{   
    this->pulseEnable = inPulseEnable;

        if(!this->lightRaise.running())
        {   
            if(this->pulseEnable)
            {
                //En 0 == raise light
                if(!this->En)
                {   
                    this->tick += this->increment;
                    if(this->tick >= this->maxVal)
                    {
                        this->En = 1;
                        this->tick = this->maxVal;
                        
                    }else
                    {
                        analogWrite(this->PWMpin, this->tick);
                        this->lightRaise.setTime(this->rate);   
                    }

                }
            
                //EN 1 == lower light
                if(this->En == 1)
                {  
                    this->tick = this->tick - this->increment;
                    if(this->tick <= this->minVal){this->En = 0; this->tick = this->minVal;}  
                    analogWrite(this->PWMpin, this->tick);
                    this->lightRaise.setTime(this->rate);                               
                }
            }
        }


        if(this->lightLower.running() == false)
        {
            //fade out when game start
            if(this->pulseEnable == 0)
            {   
                if(this->tick > 0)
                {
                this->tick = this->tick - this->increment; 
                analogWrite(this->PWMpin, this->tick);
                this->lightLower.setTime(this->rate);
                }
                if(this->tick <= 0){this->En = 0; this->tick = 0;}    
            }
        }


}