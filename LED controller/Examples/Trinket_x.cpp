#include <Wire.h>
#include <Adafruit_NeoPixel.h>

// I2C address for this device
#define I2C_ADDRESS 0x10

// LED setup
#define LED_PIN 4
#define NUM_LEDS 6  // Change if using a strip
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Storage for incoming RGB data
uint8_t rgbData[3] = {0, 0, 0};
volatile bool newDataReceived = false;

// I2C receive interrupt handler
void receiveEvent(int numBytes) {
  // Read incoming RGB data (3 bytes: R, G, B)
  if(numBytes >= 3) {
    rgbData[0] = Wire.read();  // Red
    rgbData[1] = Wire.read();  // Green
    rgbData[2] = Wire.read();  // Blue
    newDataReceived = true;
  }
  
  // Clear any remaining bytes in the buffer
  while(Wire.available()) {
    Wire.read();
  }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize I2C as slave at address 0x10
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
  
  // Initialize LED strip
  strip.begin();
  strip.show();  // Turn off all LEDs
  
  Serial.println("Trinket M0 LED Controller initialized");
  Serial.print("I2C Address: 0x");
  Serial.println(I2C_ADDRESS, HEX);
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
  // If new data was received, update the LED
  if(newDataReceived) {
    updateLED();
    newDataReceived = false;
    
    Serial.print("LED updated: R=");
    Serial.print(rgbData[0]);
    Serial.print(" G=");
    Serial.print(rgbData[1]);
    Serial.print(" B=");
    Serial.println(rgbData[2]);
  }
  
  delay(10);  // Small delay to prevent watchdog issues
}
