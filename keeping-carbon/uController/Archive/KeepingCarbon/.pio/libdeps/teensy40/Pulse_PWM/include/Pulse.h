#include <stdint.h>
#include <avr/io.h>
#include <Arduino.h>
#include <Timer.h>

#ifndef PULSE_H
#define PULSE_H




class Pulse 
{   
    public:
        Pulse();
        void attach(int8_t inPWMpin);
        void setRate(int8_t inRate = 10);
        void update(bool inPulseEnable);
        void setMax(int8_t inMaxVal=255);
        void setMin(int8_t inMinVal=0);
        void setIncrement(int8_t inIncrement=5);
    private:
        uint8_t PWMpin;
        bool pulseEnable;
        uint8_t rate;
        uint8_t maxVal; //max value to raise light to
        uint8_t minVal; //min value to lower light to
        uint8_t increment; //how many increments to increase
        uint8_t tick;
        bool En = 0; //bool to hold direction of pulse
        
        MoToTimer lightRaise; // Declare lightRaise
        MoToTimer lightLower; // Declare lightLower

};



#endif