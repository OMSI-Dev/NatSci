#include <Arduino.h>
#include <FastLED.h>
#include <Wire.h>
#include <i2C_Address.h>

// LED Chain Configuration
const int LED_PIN = 2;        // Data pin for LED chain
const int NUM_LEDS = 20;      // Number of LEDs in the chain

// Define the array of LEDs
CRGB leds[NUM_LEDS];

uint16_t i2cAddress = 0x08;
volatile uint8_t dataReceived = 0;
volatile bool newDataFlag = false;
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 5000;  // Status update every 5 seconds

// I2C Request Handler - Called when master requests data
void requestEvent() 
{
    // Send our I2C address back to the master
    Wire.write((uint8_t)i2cAddress);
    
    Serial.print("Request received - Sent address: 0x");
    Serial.println(i2cAddress, HEX);
}

// I2C Receive Handler - Called when master sends data
void receiveEvent(int numBytes) 
{
    if (numBytes > 0) 
    {
        dataReceived = Wire.read();
        newDataFlag = true;
        
        // Clear any remaining bytes
        while (Wire.available()) 
        {
            Wire.read();
        }
    }
}

void setup() 
{
    Serial.begin(9600);
    //only use for debugging.
    // while(!Serial);

    Serial.println("=== M0 I2C Communication Test ===");
    Serial.println("Checking I2C Address...");
    
    //set address pins before polling them.
    setPins();
    i2cAddress = setAddr();
    
    // Initialize I2C as slave with callbacks
    Wire.begin(i2cAddress);
    Wire.onRequest(requestEvent);  // Register request handler
    Wire.onReceive(receiveEvent);  // Register receive handler

    Serial.print("My address is: 0x");
    Serial.print(i2cAddress, HEX);
    Serial.print(" (");
    Serial.print(i2cAddress);
    Serial.println(")");
    Serial.println("Ready for I2C communication...\n");
    
    // Initialize LED strip
    FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(50);
    FastLED.clear();
    FastLED.show();
}

void loop() 
{
    // Periodic heartbeat to confirm device is running
    if (millis() - lastHeartbeat >= heartbeatInterval) 
    {
        lastHeartbeat = millis();
        Serial.print("[Heartbeat] I2C Address: 0x");
        Serial.print(i2cAddress, HEX);
        Serial.print(" | Waiting for Teensy master...");
        Serial.println();
    }
    
    // Check if new data was received
    if (newDataFlag) 
    {
        newDataFlag = false;
        
        Serial.print("Data received: 0x");
        if (dataReceived < 16) Serial.print("0");
        Serial.println(dataReceived, HEX);
        
        // Simple test: light up LEDs if data is 0xFF
        if (dataReceived == 0xFF) 
        {
            fill_solid(leds, NUM_LEDS, CRGB::White);
            Serial.println("LEDs ON");
        } 
        else 
        {
            FastLED.clear();
            Serial.println("LEDs OFF");
        }
        
        FastLED.show();
    }
    
    delay(10);
}

