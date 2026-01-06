#pragma once
#include <Arduino.h>
#include <FastLED.h>
#include <Timer.h>

/**
 * @brief Options are 1-Jumbo 2-Large 3-Medium
*/
template <int btnType>
class Haxx {
  static_assert(
    btnType == 1 || btnType == 2 || btnType == 3,
    "Options are 1-Jumbo 2-Large 3-Medium"
  );
};

//Template for Jumbo Buttons
template <>
class Haxx<1>
{
public:
    Haxx();
    void attach(uint8_t pin, uint8_t brightness=155);
    bool isOn();
    void red();
    void green();
    void blue();
    void off();
    bool ringTimer(uint32_t time,uint8_t r,uint8_t g,uint8_t b, bool flash = true,bool reset = false);
    void centerFill(uint8_t r,uint8_t g,uint8_t b);
    void ringFill(uint8_t r,uint8_t g,uint8_t b);
    void chase(uint8_t r,uint8_t g,uint8_t b, uint16_t rate, uint8_t fadeRate,uint8_t section);
    void rainbow(uint16_t rate=25);   
    //ring timer control vars
    MoToTimer ringTiming;
private:
    static constexpr uint8_t pixelCount = 89; 
    CRGBArray<89> jumbo;        
    void setupLEDs(uint8_t pin, uint8_t pixelNumber);

    CRGB* ring;
    CRGB* center;
    CRGB curColor;
    //Function Vars
    uint8_t DataPin;
    const uint8_t ringNumLeds = 12;
    const uint8_t centerNumLeds = 77;
    //ringTimer Vars
    MoToTimer flashTimer;
    uint8_t flashingCount;
    uint8_t timeLEDcount;
    uint32_t setTime;
    bool finished = false;
    bool reset = false;
    //Chase Timers
    uint8_t arraySize = pixelCount;
    uint8_t chasei;
    //timers
    MoToTimer fade; // Declare fade timer
    MoToTimer speed; // Declare chase timer

};

//Template for Large Buttons
template <>
class Haxx<2>
{
public:
    Haxx();
    void attach(uint8_t pin, uint8_t brightness=155);
    bool isOn();
    void red();
    void green();
    void blue();
    void off();
    bool ringTimer(uint32_t time,uint8_t r,uint8_t g,uint8_t b, bool flash = true,bool reset = false);
    void centerFill(uint8_t r,uint8_t g,uint8_t b);
    void ringFill(uint8_t r,uint8_t g,uint8_t b);
    void chase(uint8_t r,uint8_t g,uint8_t b, uint16_t rate, uint8_t fadeRate,uint8_t section);
    void rainbow(uint16_t rate=25);
    //ring timer control vars
    MoToTimer ringTiming;
private:
    static constexpr uint8_t pixelCount = 49;     
    void setupLEDs(uint8_t pin, uint8_t pixelNumber);

    CRGBArray<49> large;  
    CRGB* ring;
    CRGB* center;
    CRGB curColor;
    //Function Vars
    uint8_t DataPin;
    const uint8_t ringNumLeds = 12;
    const uint8_t centerNumLeds = 37;
    //ringTimer Vars
    MoToTimer flashTimer;
    uint8_t flashingCount;
    uint8_t timeLEDcount;
    uint32_t setTime;
    bool finished = false;
    bool reset = false;
    //Chase Timers
    uint8_t arraySize = pixelCount;
    uint8_t chasei;
    //timers
    MoToTimer fade; // Declare fade timer
    MoToTimer speed; // Declare chase timer

};

//Template for Medium Buttons
template <>
class Haxx<3>
{
public:
    Haxx();
    void attach(uint8_t pin, uint8_t brightness=155);
    bool isOn();
    void red();
    void green();
    void blue();
    void off();
    bool ringTimer(uint32_t time,uint8_t r,uint8_t g,uint8_t b, bool flash = true,bool reset = false);
    void centerFill(uint8_t r,uint8_t g,uint8_t b);
    void ringFill(uint8_t r,uint8_t g,uint8_t b);
    void chase(uint8_t r,uint8_t g,uint8_t b, uint16_t rate, uint8_t fadeRate,uint8_t section);
    void rainbow(uint16_t rate=25);
    //ring timer control vars
    MoToTimer ringTiming;
private:
    //pixel count for medium template
    static constexpr uint8_t pixelCount = 29;
    void setupLEDs(uint8_t pin, uint8_t pixelNumber);
    //led arrays
    CRGBArray<29> med;
    CRGB* ring;
    CRGB* center;
    CRGB curColor;    
    //Function Vars
    uint8_t DataPin;
    const uint8_t ringNumLeds = 12;
    const uint8_t centerNumLeds = 17;
    //ringTimer Vars
    MoToTimer flashTimer;
    uint8_t flashingCount;
    uint8_t timeLEDcount;
    uint32_t setTime;
    bool finished = false;
    bool reset = false;
    //Chase Timers
    uint8_t arraySize = pixelCount;
    uint8_t chasei;

    //timers
    MoToTimer fade; // Declare fade timer
    MoToTimer speed; // Declare chase timer
};
