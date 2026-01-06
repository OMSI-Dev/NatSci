#pragma once
#include <Arduino.h>
#include <FastLED.h>
#include <Timer.h>

#ifndef HAXX_H
#define HAXX_H


class haxx 
{   
    public:
        haxx();
        void attach(uint8_t inDataPin = 0, uint8_t btnType=0,uint8_t value = 155);
        void update(bool enable);
        void chase(uint8_t r,uint8_t g,uint8_t b, uint16_t rate, uint8_t fadeRate,uint8_t section);
        void red();
        void green();
        void blue();
        void centerFill(uint8_t r,uint8_t g,uint8_t b);
        void ringFill(uint8_t r,uint8_t g,uint8_t b);
        void radar(uint8_t r,uint8_t g,uint8_t b,uint16_t rate,bool dir=true, uint8_t numArms=1);
        void centerRings(uint8_t r,uint8_t g,uint8_t b,uint16_t rate=125, bool dir= true);
        void off();
        void loading(uint16_t rate=25);
        #define jumboSize 89
        #define largeSize 49
        #define medSize 29

    private:
        uint8_t DataPin;
        uint8_t pixelCount;
        bool enable;
        uint8_t rate;
        uint8_t chasei;
        int8_t swirli;
        uint8_t pulseState;
        uint8_t hue;
        uint8_t arraySize;

        MoToTimer fade; // Declare fade timer
        MoToTimer speed; // Declare chase timer
        MoToTimer centerPulse; //used  in the center pulse
        MoToTimer armSpeed; // used for the radar

        CRGBArray<82> jumboBtn;
        CRGBArray<49> largeBtn;
        CRGBArray<29> medBtn;

        CRGB* btnCenter;
        CRGB* ringLight;

        static const uint8_t centerNumLeds = 19;
        static const uint8_t edgeNumLeds = 12;
        static const uint8_t midNumLeds = 6;
        static const uint8_t ringNumLeds = 12;

        void setupLEDs(uint8_t pin, uint8_t pixelNumber);
        void edgeFade(uint8_t scale);
        void midFade(uint8_t scale);
        uint8_t getButtonSize();

        /*
        arm1 = 0,1,2 (26,28)
        arm2 = 0,3,4 (25,30)
        arm3 = 0,5,6 (22,23)
        arm4 = 0,7,8 (16,12)
        arm5 = 0,9,10 (17,14)
        arm6 = 0,11,12 (20,19)
        */
        const uint8_t swirlArm[13] = {21,26,28, 25,30, 22,23, 16,12, 17,14, 20,19};

        const uint8_t btnCenterEdgeRing[12] = {12,13,14,18,19,27,28,29,30,24,23,15};
        const uint8_t btnCenterMidRing[6] = {16, 17, 20, 25, 26, 22};
};





#endif