/* ItsyBitsy Express RGBW LED Unit with EEPROM Storage
 * 
 * Stores a single RGBW color in EEPROM and displays it on LED strip
 * I2C Address: 0x10
 * 
 * Hardware:
 * - LED Strip (SK6812 RGBW): Data pin connected to Pin 5, 5V power
 * - I2C: SDA/SCL for communication with Teensy
 * 
 * Commands from Teensy:
 * - 0x30: Send RGBW to LED (temporary, 4 bytes: R, G, B, W)
 * - 0x40: Save RGBW to EEPROM (persistent, 4 bytes: R, G, B, W)
 * 
 * On power-up: Loads and displays RGBW value from EEPROM
 */

#include <Wire.h>
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <FlashStorage.h>

#define I2C_ADDRESS 0x10
#define LED_PIN 5
#define NUM_LEDS 1000  // Adjust this to match your LED strip length

// RGBW Color structure
typedef struct {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint8_t w;
  bool valid;
} RGBWData;

FlashStorage(rgbw_storage, RGBWData);

// LED strip object - using GRBW order (SK6812 RGBW)
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRBW + NEO_KHZ800);

// I2C Commands
#define CMD_SEND_LED 0x30   // Send RGBW to LED (temporary display)
#define CMD_SAVE_LED 0x40   // Save RGBW to EEPROM (persistent storage)

// Current state
RGBWData currentRGBW;

// Pending LED update flag (set in ISR, consumed in loop)
volatile bool pendingDisplay = false;
volatile bool pendingSave = false;
volatile uint8_t pendingR, pendingG, pendingB, pendingW;

// Display RGBW color on LED strip
void displayRGBW(uint8_t r, uint8_t g, uint8_t b, uint8_t w) {
  // Create packed RGBW color value using Color() for RGBW strips
  uint32_t color = strip.Color(r, g, b, w);
  
  // Set all LEDs to the same color
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
  delayMicroseconds(50);  // Small delay to stabilize signal
}

// Handle I2C receive events (commands from Teensy)
void receiveEvent(int bytes) {
  if(bytes < 1) return;
  
  uint8_t command = Wire.read();
  
  switch(command) {
    case CMD_SEND_LED:
      // Queue RGBW for display in loop() — never call strip.show() from an ISR
      if(bytes >= 5) {  // Command + 4 bytes (R, G, B, W)
        pendingR = Wire.read();
        pendingG = Wire.read();
        pendingB = Wire.read();
        pendingW = Wire.read();
        pendingDisplay = true;
      }
      break;
      
    case CMD_SAVE_LED:
      // Queue RGBW save+display for loop() — delay() and strip.show() are unsafe in an ISR
      if(bytes >= 5) {  // Command + 4 bytes (R, G, B, W)
        pendingR = Wire.read();
        pendingG = Wire.read();
        pendingB = Wire.read();
        pendingW = Wire.read();
        pendingSave = true;
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
  //strip.setBrightness(200);  // Reduced brightness to prevent flickering (0-255)
  
  // Clear all LEDs explicitly
  for(int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, 0, 0, 0, 0);
  }
  strip.show();

  delay(200);
  
  // Read RGBW data from EEPROM
  currentRGBW = rgbw_storage.read();
  
  // Initialize with default color if first time (white)
  if(!currentRGBW.valid) {
    currentRGBW.r = 255;
    currentRGBW.g = 255;
    currentRGBW.b = 255;
    currentRGBW.w = 255;
    currentRGBW.valid = true;
    rgbw_storage.write(currentRGBW);
  }
  
  // Initialize I2C as slave
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);
  
  // Display saved RGBW color from EEPROM on power-up
  displayRGBW(currentRGBW.r, currentRGBW.g, currentRGBW.b, currentRGBW.w);
}

void loop() {
  // Main loop - I2C events handled by interrupts; LED updates are done here
  if(pendingDisplay) {
    pendingDisplay = false;
    displayRGBW(pendingR, pendingG, pendingB, pendingW);
  }

  if(pendingSave) {
    pendingSave = false;
    currentRGBW.r = pendingR;
    currentRGBW.g = pendingG;
    currentRGBW.b = pendingB;
    currentRGBW.w = pendingW;
    currentRGBW.valid = true;

    rgbw_storage.write(currentRGBW);
    displayRGBW(currentRGBW.r, currentRGBW.g, currentRGBW.b, currentRGBW.w);

    // Double blink to confirm save
    for(int i = 0; i < 2; i++) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(100);
      digitalWrite(LED_BUILTIN, LOW);
      delay(100);
    }
  }

  delay(10);
}