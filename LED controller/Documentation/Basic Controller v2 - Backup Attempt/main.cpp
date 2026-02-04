/* ItsyBitsy Express RGB LED Unit with EEPROM Storage
 * 
 * Stores a single RGB color in EEPROM and displays it on LED strip
 * I2C Address: 0x10
 * 
 * Hardware:
 * - LED Strip (SK6812 RGBW): Data pin connected to Pin 5, 5V power
 * - I2C: SDA/SCL for communication with Teensy
 * 
 * Commands from Teensy:
 * - 0x30: Send RGB to LED (temporary, 3 bytes: R, G, B)
 * - 0x40: Save RGB to EEPROM (persistent, 3 bytes: R, G, B)
 * 
 * On power-up: Loads and displays RGB value from EEPROM
 */

#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <FlashStorage.h>

#define I2C_ADDRESS 0x10
#define LED_PIN 5
#define NUM_LEDS 150  // Adjust this to match your LED strip length

// RGB Color structure
typedef struct {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  bool valid;
} RGBData;

FlashStorage(rgb_storage, RGBData);

// LED strip object - using GRB order (WS2812B/SK6812 RGB)
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// I2C Commands
#define CMD_SEND_LED 0x30   // Send RGB to LED (temporary display)
#define CMD_SAVE_LED 0x40   // Save RGB to EEPROM (persistent storage)

// Current state
RGBData currentRGB;

// Display RGB color on LED strip
void displayRGB(uint8_t r, uint8_t g, uint8_t b) {
  // Explicitly set each LED to ensure all are the same color
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, r, g, b);
  }
  strip.show();
}

// Handle I2C receive events (commands from Teensy)
void receiveEvent(int bytes) {
  if(bytes < 1) return;
  
  uint8_t command = Wire.read();
  
  switch(command) {
    case CMD_SEND_LED:
      // Send RGB to LED strip (temporary display)
      if(bytes >= 4) {  // Command + 3 bytes (R, G, B)
        uint8_t r = Wire.read();
        uint8_t g = Wire.read();
        uint8_t b = Wire.read();
        
        displayRGB(r, g, b);
      }
      break;
      
    case CMD_SAVE_LED:
      // Save RGB to EEPROM (persistent storage)
      if(bytes >= 4) {  // Command + 3 bytes (R, G, B)
        currentRGB.r = Wire.read();
        currentRGB.g = Wire.read();
        currentRGB.b = Wire.read();
        currentRGB.valid = true;
        
        // Save to EEPROM
        rgb_storage.write(currentRGB);
        
        // Display the saved color
        displayRGB(currentRGB.r, currentRGB.g, currentRGB.b);
        
        // Double blink to confirm save
        for(int i = 0; i < 2; i++) {
          digitalWrite(LED_BUILTIN, HIGH);
          delay(100);
          digitalWrite(LED_BUILTIN, LOW);
          delay(100);
        }
      }
      break;
  }
  
  // Clear any remaining bytes
  while(Wire.available()) {
    Wire.read();
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Initialize LED strip
  strip.begin();
  strip.setBrightness(255);  // Full brightness (0-255)
  
  // Clear all LEDs explicitly
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, 0, 0, 0, 0);
  }
  strip.show();
  delay(200);
  
  // Read RGB data from EEPROM
  currentRGB = rgb_storage.read();
  
  // Initialize with default color if first time (white)
  if(!currentRGB.valid) {
    currentRGB.r = 255;
    currentRGB.g = 255;
    currentRGB.b = 255;
    currentRGB.valid = true;
    rgb_storage.write(currentRGB);
  }
  
  // Initialize I2C as slave
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
  
  // Display saved RGB color from EEPROM on power-up
  displayRGB(currentRGB.r, currentRGB.g, currentRGB.b);
}

void loop() {
  // Main loop - I2C events handled by interrupts
  delay(10);
}