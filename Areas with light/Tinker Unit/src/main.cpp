#include <Wire.h>
#include <Adafruit_NeoPixel.h>

// I2C address for this device
#define I2C_ADDRESS 0x10

// LED setup
#define LED_PIN 4
#define NUM_LEDS 1  // Change if using a strip
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Storage for incoming RGB data
uint8_t rgbData[3] = {0, 0, 0};
volatile bool newDataReceived = false;



// I2C receive interrupt handler
void receiveEvent(int numBytes) {
  if (numBytes >= 3) {
    rgbData[0] = Wire.read();  // Red
    rgbData[1] = Wire.read();  // Green
    rgbData[2] = Wire.read();  // Blue
    
    // Set flag for main loop to process
    newDataReceived = true;
  }
  
  // Clear any extra bytes
  while (Wire.available()) {
    Wire.read();
  }
}

void setup() {
  // Initialize I2C as slave
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);  // Register receive callback
  
  // Initialize LED strip
  strip.begin();
  strip.setBrightness(255);  // Full brightness
  strip.show(); // Initialize all pixels to 'off'
  
  // Optional: Flash LED to show it's ready
  strip.setPixelColor(0, strip.Color(50, 50, 50));
  strip.show();
  delay(500);
  strip.setPixelColor(0, strip.Color(0, 0, 0));
  strip.show();
}



void updateLED() {
  // Set all LEDs to the received color
  uint32_t color = strip.Color(rgbData[0], rgbData[1], rgbData[2]);
  
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, color);
  }
  
  strip.show();
}

void loop() {
  // If new data was received via I2C, update the LED
  if (newDataReceived) {
    updateLED();
    newDataReceived = false;
  }
  
  // Main loop can do other things here
  delay(10);
}
