/* Teensy 4.0 RGB LED Controller with EEPROM Storage
 * 
 * Hardware connections:
 * - OLED Display (128x64): SDA > pin 18, SCL > pin 19, VCC > 3.3V, GND > GND
 * - Buttons 1-7: One leg > pins 2-8, Other leg > GND
 * - Potentiometer: Wiper > pin A0 (pin 14), VCC > 3.3V, GND > GND
 * - I2C to Trinket: Wire1 on pins 16/17 (3.3V bus)
 * - I2C to OLED: Wire on pins 18/19 (3.3V bus)
 * 
 * Button Functions:
 * - Buttons 1-4: Select preset slots (load from Teensy EEPROM)
 * - Button 5 (SEND): Send current RGB value to Trinket (live update only)
 * - Button 6 (SAVE): Save current RGB value to Trinket EEPROM (persistent)
 * - Button 7 (EDIT): Cycle through R→G→B→Neutral edit modes
 * 
 * Edit Mode:
 * - Press EDIT to cycle: R (red blinks) → G (green blinks) → B (blue blinks) → Neutral (no blink)
 * - In R/G/B mode: potentiometer edits that color channel (0-255)
 * - In Neutral mode: no editing, can send to LED or save to presets
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <EEPROM.h>

#define TRINKET_ADDRESS 0x10

// OLED display settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

// Button pins (2-8)
#define BUTTON_1 2
#define BUTTON_2 3
#define BUTTON_3 4
#define BUTTON_4 5
#define BUTTON_5 6  // SEND button
#define BUTTON_6 7  // SAVE button
#define BUTTON_7 8  // EDIT button

// Potentiometer pin
#define POT_PIN A0  // Pin 14

// I2C Commands
#define CMD_SEND_LED 0x30      // Send RGB to LED (3 bytes: R, G, B)
#define CMD_SAVE_LED 0x40      // Save RGB to Trinket EEPROM (3 bytes: R, G, B)

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// RGB structure
struct RGBColor {
  uint8_t r;
  uint8_t g;
  uint8_t b;
};

// EEPROM storage for 4 RGB presets (Teensy EEPROM)
#define EEPROM_START_ADDR 0
#define EEPROM_MAGIC 0xA5  // Magic number to check if EEPROM is initialized
RGBColor presetColors[4];

// Current state
int selectedPreset = -1;  // 0-3 for presets 1-4, -1 for none
RGBColor currentColor = {0, 0, 0};

// Edit mode: 0 = Neutral, 1 = Edit R, 2 = Edit G, 3 = Edit B
int editMode = 0;

// Button state tracking
unsigned long lastPressTime = 0;
const unsigned long DEBOUNCE_DELAY = 200;

// Potentiometer value (0-255)
uint8_t potValue = 0;
uint8_t lastPotValue = 0;

// Blink state for editing indicator
unsigned long lastBlinkTime = 0;
bool blinkState = false;
const unsigned long BLINK_INTERVAL = 500;  // 500ms blink interval



void saveAllPresetsToEEPROM() {
  int addr = EEPROM_START_ADDR + 1;  // Skip magic byte
  for(int i = 0; i < 4; i++) {
    EEPROM.write(addr++, presetColors[i].r);
    EEPROM.write(addr++, presetColors[i].g);
    EEPROM.write(addr++, presetColors[i].b);
  }
  Serial.println("✓ Saved all presets to Teensy EEPROM");
}

void loadAllPresetsFromEEPROM() {
  int addr = EEPROM_START_ADDR + 1;  // Skip magic byte
  for(int i = 0; i < 4; i++) {
    presetColors[i].r = EEPROM.read(addr++);
    presetColors[i].g = EEPROM.read(addr++);
    presetColors[i].b = EEPROM.read(addr++);
    Serial.print("Preset ");
    Serial.print(i + 1);
    Serial.print(": R=");
    Serial.print(presetColors[i].r);
    Serial.print(" G=");
    Serial.print(presetColors[i].g);
    Serial.print(" B=");
    Serial.println(presetColors[i].b);
  }
}

void savePresetToEEPROM(uint8_t presetIndex) {
  if(presetIndex >= 4) return;
  
  int addr = EEPROM_START_ADDR + 1 + (presetIndex * 3);
  EEPROM.write(addr, presetColors[presetIndex].r);
  EEPROM.write(addr + 1, presetColors[presetIndex].g);
  EEPROM.write(addr + 2, presetColors[presetIndex].b);
  
  Serial.print("✓ Saved Preset ");
  Serial.print(presetIndex + 1);
  Serial.print(" to Teensy EEPROM: R=");
  Serial.print(presetColors[presetIndex].r);
  Serial.print(" G=");
  Serial.print(presetColors[presetIndex].g);
  Serial.print(" B=");
  Serial.println(presetColors[presetIndex].b);
}

// Send RGB to Trinket LED strip (temporary display)
void sendRGBToLED(RGBColor color) {
  Wire1.beginTransmission(TRINKET_ADDRESS);
  Wire1.write(CMD_SEND_LED);
  Wire1.write(color.r);
  Wire1.write(color.g);
  Wire1.write(color.b);
  Wire1.endTransmission();
}

// Save RGB to Trinket EEPROM (persistent storage)
void saveRGBToTrinket(RGBColor color) {
  Wire1.beginTransmission(TRINKET_ADDRESS);
  Wire1.write(CMD_SAVE_LED);
  Wire1.write(color.r);
  Wire1.write(color.g);
  Wire1.write(color.b);
  Wire1.endTransmission();
  
  Serial.print("✓ Saved to Trinket EEPROM: R=");
  Serial.print(color.r);
  Serial.print(" G=");
  Serial.print(color.g);
  Serial.print(" B=");
  Serial.println(color.b);
}


// EEPROM Functions
void initializeEEPROM() {
  // Check if EEPROM is initialized
  if(EEPROM.read(EEPROM_START_ADDR) != EEPROM_MAGIC) {
    Serial.println("Initializing Teensy EEPROM with default RGB presets...");
    
    // Set default RGB presets
    presetColors[0] = {255, 0, 0};      // Red
    presetColors[1] = {0, 255, 0};      // Green
    presetColors[2] = {0, 0, 255};      // Blue
    presetColors[3] = {255, 255, 255};  // White
    
    // Write magic number
    EEPROM.write(EEPROM_START_ADDR, EEPROM_MAGIC);
    
    // Write presets to EEPROM
    saveAllPresetsToEEPROM();
  } else {
    Serial.println("Loading RGB presets from Teensy EEPROM...");
    loadAllPresetsFromEEPROM();
  }
}

void updateDisplay() {
  display.clearDisplay();
  
  // Title
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("RGB LED Controller");
  display.drawLine(0, 9, SCREEN_WIDTH, 9, SSD1306_WHITE);
  
  // Edit mode indicator
  const char* editModeLabels[] = {"NEUTRAL", "EDIT R", "EDIT G", "EDIT B"};
  if(editMode > 0) {
    display.setCursor(75, 0);
    display.print("[");
    display.print(editModeLabels[editMode]);
    display.print("]");
  }
  
  // Current preset info
  if(selectedPreset >= 0) {
    display.setTextSize(1);
    display.setCursor(0, 12);
    display.print("Preset ");
    display.print(selectedPreset + 1);
    
    // Display RGB values with blinking for active channel
    display.setCursor(0, 24);
    
    // Red channel
    if(editMode == 1 && !blinkState) {
      display.print("R:   ");  // Blink off
    } else {
      display.print("R:");
      display.print(currentColor.r);
    }
    
    display.setCursor(0, 34);
    
    // Green channel
    if(editMode == 2 && !blinkState) {
      display.print("G:   ");  // Blink off
    } else {
      display.print("G:");
      display.print(currentColor.g);
    }
    
    display.setCursor(0, 44);
    
    // Blue channel
    if(editMode == 3 && !blinkState) {
      display.print("B:   ");  // Blink off
    } else {
      display.print("B:");
      display.print(currentColor.b);
    }
    
    // Show color preview bar
    display.drawRect(60, 24, 60, 24, SSD1306_WHITE);
    // Calculate brightness for monochrome display
    uint8_t brightness = (currentColor.r + currentColor.g + currentColor.b) / 3;
    if(brightness > 128) {
      display.fillRect(62, 26, 56, 20, SSD1306_WHITE);
    }
    
    // Pot value if editing
    if(editMode > 0) {
      display.setCursor(60, 50);
      display.print("Pot:");
      display.print(potValue);
    }
  } else {
    display.setTextSize(1);
    display.setCursor(5, 16);
    display.println("Select Preset 1-4");
    display.setCursor(5, 30);
    display.println("5:SEND  6:SAVE");
    display.setCursor(5, 40);
    display.println("7:EDIT(Cycle R/G/B)");
  }
  
  // Show all preset colors at bottom
  display.setTextSize(1);
  display.setCursor(0, 56);
  display.print("1:");
  display.print(presetColors[0].r);
  display.print(",");
  display.print(presetColors[0].g);
  display.print(",");
  display.print(presetColors[0].b);
  
  display.display();
}

uint8_t readPotentiometer() {
  // Read analog value (0-1023 on Teensy 4.0, 10-bit ADC)
  int rawValue = analogRead(POT_PIN);
  // Map to 0-255 for RGB value
  return map(rawValue, 0, 1023, 0, 255);
}

void checkButtons() {
  int buttonPins[] = {BUTTON_1, BUTTON_2, BUTTON_3, BUTTON_4, BUTTON_5, BUTTON_6, BUTTON_7};
  
  for(int i = 0; i < 7; i++) {
    if(digitalRead(buttonPins[i]) == LOW) {  // Button pressed (active LOW)
      unsigned long currentTime = millis();
      if(currentTime - lastPressTime > DEBOUNCE_DELAY) {
        lastPressTime = currentTime;
        
        // Buttons 1-4: Select preset from Teensy EEPROM
        if(i >= 0 && i <= 3) {
          selectedPreset = i;
          editMode = 0;  // Reset to neutral mode
          
          // Load RGB from Teensy EEPROM
          currentColor = presetColors[selectedPreset];
          
          Serial.print("Selected Preset ");
          Serial.print(selectedPreset + 1);
          Serial.print(": R=");
          Serial.print(currentColor.r);
          Serial.print(" G=");
          Serial.print(currentColor.g);
          Serial.print(" B=");
          Serial.println(currentColor.b);
          
          // Display preset on LED strip immediately
          sendRGBToLED(currentColor);
        }
        // Button 5 (SEND): Send to LED (temporary display)
        else if(i == 4) {
          if(selectedPreset >= 0 && editMode == 0) {  // Only in neutral mode
            sendRGBToLED(currentColor);
            Serial.println("Sent RGB to LED strip");
          }
        }
        // Button 6 (SAVE): Save to Trinket EEPROM (persistent)
        else if(i == 5) {
          if(selectedPreset >= 0 && editMode == 0) {  // Only in neutral mode
            // Update Teensy EEPROM preset
            presetColors[selectedPreset] = currentColor;
            savePresetToEEPROM(selectedPreset);
            
            // Save to Trinket EEPROM
            saveRGBToTrinket(currentColor);
          }
        }
        // Button 7 (EDIT): Cycle through edit modes (R → G → B → Neutral)
        else if(i == 6) {
          if(selectedPreset >= 0) {
            editMode = (editMode + 1) % 4;  // Cycle: 0→1→2→3→0
            Serial.print("Edit mode: ");
            const char* modes[] = {"NEUTRAL", "R", "G", "B"};
            Serial.println(modes[editMode]);
          }
        }
        
        updateDisplay();
      }
      break;  // Only process one button at a time
    }
  }
}


void setup() {
  Serial.begin(9600);
  delay(100);
  Serial.println("=== RGB LED Controller Starting ===");
  
  // Initialize potentiometer pin
  pinMode(POT_PIN, INPUT);
  analogReadResolution(10);  // 10-bit ADC (0-1023)
  
  // Initialize button pins with internal pull-up resistors
  pinMode(BUTTON_1, INPUT_PULLUP);
  pinMode(BUTTON_2, INPUT_PULLUP);
  pinMode(BUTTON_3, INPUT_PULLUP);
  pinMode(BUTTON_4, INPUT_PULLUP);
  pinMode(BUTTON_5, INPUT_PULLUP);
  pinMode(BUTTON_6, INPUT_PULLUP);
  pinMode(BUTTON_7, INPUT_PULLUP);
  
  // Initialize I2C for OLED (Wire on pins 18/19)
  Wire.setSDA(18);
  Wire.setSCL(19);
  Wire.begin();
  
  // Initialize I2C for Trinket (Wire1 on pins 16/17)
  Wire1.begin();
  
  delay(100);
  
  // Initialize OLED display
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("✗ OLED display failed!");
    for(;;);  // Stop if display fails
  }
  
  // Show startup screen
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 9);
  display.println("RGB LED");
  display.setCursor(10, 25);
  display.println("Controller");
  display.setCursor(20, 45);
  display.println("Ready!");
  display.display();
  
  // Initialize Teensy EEPROM (load or create RGB presets)
  initializeEEPROM();
  
  delay(2000);
  
  Serial.println("=== Teensy EEPROM RGB Presets ===");
  for(int i = 0; i < 4; i++) {
    Serial.print("Preset ");
    Serial.print(i + 1);
    Serial.print(": R=");
    Serial.print(presetColors[i].r);
    Serial.print(" G=");
    Serial.print(presetColors[i].g);
    Serial.print(" B=");
    Serial.println(presetColors[i].b);
  }
  Serial.println("==================================");
  
  // Show initial screen
  updateDisplay();
}

void loop() {
  // Read potentiometer value
  potValue = readPotentiometer();
  
  // Handle blinking for active edit channel
  unsigned long currentTime = millis();
  if(currentTime - lastBlinkTime > BLINK_INTERVAL) {
    lastBlinkTime = currentTime;
    blinkState = !blinkState;
    if(editMode > 0) {  // Only update display if actively editing
      updateDisplay();
    }
  }
  
  // If in edit mode (1=R, 2=G, 3=B) and pot changed, update the active channel
  if(editMode > 0 && abs(potValue - lastPotValue) > 1) {
    lastPotValue = potValue;
    
    // Update the appropriate color channel
    switch(editMode) {
      case 1:  // Edit Red
        currentColor.r = potValue;
        break;
      case 2:  // Edit Green
        currentColor.g = potValue;
        break;
      case 3:  // Edit Blue
        currentColor.b = potValue;
        break;
    }
    
    // Live update LED strip
    sendRGBToLED(currentColor);
    updateDisplay();
  }
  
  checkButtons();
  
  delay(10);  // Small delay to prevent excessive polling
}



