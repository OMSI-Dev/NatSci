/* ItsyBitsy Express RGBW LED Unit with EEPROM Storage (FastLED)
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
 * FastLED Power Management:
 * - Voltage and amperage control configured for safe operation
 * - Automatic brightness limiting based on power constraints
 * 
 * On power-up: Loads and displays RGBW value from EEPROM
 */

#include <Wire.h>
#include <Arduino.h>
#include <FastLED.h>
#include <FlashStorage.h>

#define I2C_ADDRESS 0x10
#define LED_PIN 5
#define NUM_LEDS 1000  // Adjust this to match your LED strip length

// Power Supply Configuration
#define VOLTS 5          // Power Supply Voltage and Amperage 
#define MAX_MILLIAMPS 10000  

// RGBW Color structure
typedef struct {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint8_t w;
  bool valid;
} RGBWData;

FlashStorage(rgbw_storage, RGBWData);

// FastLED array - we handle RGBW by maintaining separate white channel
CRGB leds[NUM_LEDS];
uint8_t whiteChannel[NUM_LEDS];  // Separate array for white channel data

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
  // For RGBW strips: FastLED doesn't natively support RGBW, but we can
  // approximate by adding white channel to RGB values
  // For a more accurate representation, use: RGB + W for final color
  
  for(int i = 0; i < NUM_LEDS; i++) {
    // Store RGB values
    leds[i].r = r;
    leds[i].g = g;
    leds[i].b = b;
    
    // Store white value separately
    whiteChannel[i] = w;
    
    // Optional: blend white into RGB for display
    // You can adjust this blending based on desired behavior
    if(w > 0) {
      leds[i].r = qadd8(leds[i].r, w);  // FastLED's saturating add
      leds[i].g = qadd8(leds[i].g, w);
      leds[i].b = qadd8(leds[i].b, w);
    }
  }
  
  // FastLED's show() with automatic power management
  FastLED.show();
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
  
  // Initialize FastLED for SK6812 RGBW strips
  // Note: FastLED uses WS2812 chipset for SK6812 (compatible protocol)
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  
  FastLED.setMaxPowerInVoltsAndMilliamps(VOLTS, MAX_MILLIAMPS);

  // FastLED.setBrightness(200);
    FastLED.clear();
  FastLED.show();

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