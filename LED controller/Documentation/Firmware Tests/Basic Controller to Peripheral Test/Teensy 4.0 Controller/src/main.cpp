/* Teensy 4.0 RGBW LED Controller with EEPROM Storage and Animation Mode
 * 
 * Hardware connections:
 * - OLED Display (128x64): SDA > pin 18, SCL > pin 19, VCC > 5V, GND > GND
 * - Rotary Encoder: A1 > pin 15, B1 > pin 14, GND > GND
 * - Buttons S1-S4: pins 2-5 (Presets 1-4)
 * - Button S5 (EDIT): pin 6
 * - Button S6 (SAVE): pin 7
 * - Button S7 (WRITE): pin 8
 * - Button S8 (EXPORT/Animation Toggle): pin 9
 * - LED Indicator: pin 10 (for S8 button)
 * - I2C to ItsyBitsy: Wire1 on pins 16/17 (3.3V bus)
 * - I2C to OLED: Wire on pins 18/19 (3.3V bus)
 * 
 * Button Functions:
 * - S1-S4: Select preset slots (Static RGBW or Animation based on mode)
 * - S5 (EDIT): Cycle through R→G→B→W→Neutral edit modes
 * - S6 (WRITE): Save current RGBW to ItsyBitsy EEPROM (persistent)
 * - S7 (EXPORT): Save current RGBW to Teensy EEPROM preset slot
 * - S8 (ANIM): Toggle Animation Mode ON/OFF
 * 
 * Edit Mode:
 * - Press EDIT to cycle: Neutral → R (red blinks) → G (green blinks) → B (blue blinks) → W (white blinks) → Neutral
 * - In R/G/B/W mode: rotary encoder edits that color channel (0-255)
 * - In Neutral mode: no editing, can send to LED or save to presets
 * 
 * Animation Mode:
 * - When toggled ON: LED indicator lights up, presets become animation slots
 * - OLED displays "Animation Preset X" instead of "Preset X"
 * - Animation sequences not yet implemented
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <EEPROM.h>

#define ITSYBITSY_ADDRESS 0x10

// OLED display settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

// Button pins
#define BUTTON_S1 2      // Preset 1
#define BUTTON_S2 3      // Preset 2
#define BUTTON_S3 4      // Preset 3
#define BUTTON_S4 5      // Preset 4
#define BUTTON_S5 6      // EDIT button
#define BUTTON_S6 7      // WRITE button
#define BUTTON_S7 8      // EXPORT button
#define BUTTON_S8 9      // ANIM/Animation Toggle button
#define LED_S8 10        // LED indicator for S8 button

// Rotary encoder pins
#define ENCODER_A 15     // A1
#define ENCODER_B 14     // B1

// I2C Commands
#define CMD_SEND_LED 0x30      // Send RGBW to LED (4 bytes: R, G, B, W)
#define CMD_SAVE_LED 0x40      // Save RGBW to ItsyBitsy EEPROM (4 bytes: R, G, B, W)

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// RGBW structure
struct RGBWColor {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint8_t w;
};

// EEPROM storage for 4 RGBW presets (Teensy EEPROM)
#define EEPROM_START_ADDR 0
#define EEPROM_MAGIC 0xA5  // Magic number to check if EEPROM is initialized
RGBWColor presetColors[4];

// Current state
int selectedPreset = -1;  // 0-3 for presets 1-4, -1 for none
RGBWColor currentColor = {0, 0, 0, 0};

// Edit mode: 0 = Neutral, 1 = Edit R, 2 = Edit G, 3 = Edit B, 4 = Edit W
int editMode = 0;

// Animation mode
bool animationMode = false;  // false = Static RGB mode, true = Animation mode

// Rotary encoder state
volatile int lastEncoderA = HIGH;
volatile int lastEncoderB = HIGH;

// Button state tracking
unsigned long lastPressTime = 0;
const unsigned long DEBOUNCE_DELAY = 200;

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
    EEPROM.write(addr++, presetColors[i].w);
  }
  Serial.println("✓ Saved all presets to Teensy EEPROM");
}

void loadAllPresetsFromEEPROM() {
  int addr = EEPROM_START_ADDR + 1;  // Skip magic byte
  for(int i = 0; i < 4; i++) {
    presetColors[i].r = EEPROM.read(addr++);
    presetColors[i].g = EEPROM.read(addr++);
    presetColors[i].b = EEPROM.read(addr++);
    presetColors[i].w = EEPROM.read(addr++);
    Serial.print("Preset ");
    Serial.print(i + 1);
    Serial.print(": R=");
    Serial.print(presetColors[i].r);
    Serial.print(" G=");
    Serial.print(presetColors[i].g);
    Serial.print(" B=");
    Serial.print(presetColors[i].b);
    Serial.print(" W=");
    Serial.println(presetColors[i].w);
  }
}

void savePresetToEEPROM(uint8_t presetIndex) {
  if(presetIndex >= 4) return;
  
  int addr = EEPROM_START_ADDR + 1 + (presetIndex * 4);
  EEPROM.write(addr, presetColors[presetIndex].r);
  EEPROM.write(addr + 1, presetColors[presetIndex].g);
  EEPROM.write(addr + 2, presetColors[presetIndex].b);
  EEPROM.write(addr + 3, presetColors[presetIndex].w);
  
  Serial.print("✓ Saved Preset ");
  Serial.print(presetIndex + 1);
  Serial.print(" to Teensy EEPROM: R=");
  Serial.print(presetColors[presetIndex].r);
  Serial.print(" G=");
  Serial.print(presetColors[presetIndex].g);
  Serial.print(" B=");
  Serial.print(presetColors[presetIndex].b);
  Serial.print(" W=");
  Serial.println(presetColors[presetIndex].w);
}

// Send RGBW to ItsyBitsy LED strip (temporary display)
void sendRGBWToLED(RGBWColor color) {
  Wire1.beginTransmission(ITSYBITSY_ADDRESS);
  Wire1.write(CMD_SEND_LED);
  Wire1.write(color.r);
  Wire1.write(color.g);
  Wire1.write(color.b);
  Wire1.write(color.w);
  Wire1.endTransmission();
}

// Save RGBW to ItsyBitsy EEPROM (persistent storage)
void saveRGBWToItsyBitsy(RGBWColor color) {
  Wire1.beginTransmission(ITSYBITSY_ADDRESS);
  Wire1.write(CMD_SAVE_LED);
  Wire1.write(color.r);
  Wire1.write(color.g);
  Wire1.write(color.b);
  Wire1.write(color.w);
  Wire1.endTransmission();
  
  Serial.print("✓ Saved to ItsyBitsy EEPROM: R=");
  Serial.print(color.r);
  Serial.print(" G=");
  Serial.print(color.g);
  Serial.print(" B=");
  Serial.print(color.b);
  Serial.print(" W=");
  Serial.println(color.w);
}


// EEPROM Functions
void initializeEEPROM() {
  // Check if EEPROM is initialized
  if(EEPROM.read(EEPROM_START_ADDR) != EEPROM_MAGIC) {
    Serial.println("Initializing Teensy EEPROM with default RGBW presets...");
    
    // Set default RGBW presets
    presetColors[0] = {255, 0, 0, 0};      // Pure Red
    presetColors[1] = {0, 255, 0, 0};      // Pure Green
    presetColors[2] = {0, 0, 255, 0};      // Pure Blue
    presetColors[3] = {0, 0, 0, 255};      // Pure White
    
    // Write magic number
    EEPROM.write(EEPROM_START_ADDR, EEPROM_MAGIC);
    
    // Write presets to EEPROM
    saveAllPresetsToEEPROM();
  } else {
    Serial.println("Loading RGBW presets from Teensy EEPROM...");
    loadAllPresetsFromEEPROM();
  }
}

void updateDisplay() {
  display.clearDisplay();
  
  // Title
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("RGBW LED Controller");
  display.drawLine(0, 9, SCREEN_WIDTH, 9, SSD1306_WHITE);
  
  // Edit mode indicator
  const char* editModeLabels[] = {"NEUTRAL", "EDIT R", "EDIT G", "EDIT B", "EDIT W"};
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
    if(animationMode) {
      display.print("Animation Preset ");
    } else {
      display.print("Preset ");
    }
    display.print(selectedPreset + 1);
    
    // Display RGBW values with blinking for active channel
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
    
    display.setCursor(0, 54);
    
    // White channel
    if(editMode == 4 && !blinkState) {
      display.print("W:   ");  // Blink off
    } else {
      display.print("W:");
      display.print(currentColor.w);
    }
    
    // Show color preview bar
    display.drawRect(60, 24, 60, 34, SSD1306_WHITE);
    // Calculate brightness for monochrome display (including white channel)
    uint8_t brightness = (currentColor.r + currentColor.g + currentColor.b + currentColor.w) / 4;
    if(brightness > 128) {
      display.fillRect(62, 26, 56, 30, SSD1306_WHITE);
    }
  } else {
    display.setTextSize(1);
    display.setCursor(5, 16);
    display.println("Select Preset 1-4");
    display.setCursor(5, 28);
    display.println("S5:EDIT S6:WRITE");
    display.setCursor(5, 38);
    display.println("S7:EXPORT S8:ANIM");
    if(animationMode) {
      display.setCursor(5, 50);
      display.println("[ANIMATION MODE]");
    }
  }
  
  // Show all preset colors at bottom
  // display.setTextSize(1);
  // display.setCursor(0, 56);
  // display.print("1:");
  // display.print(presetColors[0].r);
  // display.print(",");
  // display.print(presetColors[0].g);
  // display.print(",");
  // display.print(presetColors[0].b);
  
  display.display();
}

void readEncoder() {
  int encoderA = digitalRead(ENCODER_A);
  int encoderB = digitalRead(ENCODER_B);
  
  if (encoderA != lastEncoderA) {
    if (encoderA == LOW) {
      int direction = (encoderB == HIGH) ? 1 : -1;
      int stepSize = 5;  // Adjust values by ±5 instead of ±1 for faster changes
      
      // Update current color channel based on edit mode
      switch(editMode) {
        case 1:  // Edit Red
          currentColor.r = constrain(currentColor.r + (direction * stepSize), 0, 255);
          sendRGBWToLED(currentColor);
          updateDisplay();
          break;
        case 2:  // Edit Green
          currentColor.g = constrain(currentColor.g + (direction * stepSize), 0, 255);
          sendRGBWToLED(currentColor);
          updateDisplay();
          break;
        case 3:  // Edit Blue
          currentColor.b = constrain(currentColor.b + (direction * stepSize), 0, 255);
          sendRGBWToLED(currentColor);
          updateDisplay();
          break;
        case 4:  // Edit White
          currentColor.w = constrain(currentColor.w + (direction * stepSize), 0, 255);
          sendRGBWToLED(currentColor);
          updateDisplay();
          break;
      }
    }
  }
  
  lastEncoderA = encoderA;
  lastEncoderB = encoderB;
}

void checkButtons() {
  int buttonPins[] = {BUTTON_S1, BUTTON_S2, BUTTON_S3, BUTTON_S4, BUTTON_S5, BUTTON_S6, BUTTON_S7, BUTTON_S8};
  
  for(int i = 0; i < 8; i++) {
    if(digitalRead(buttonPins[i]) == LOW) {
      unsigned long currentTime = millis();
      if(currentTime - lastPressTime > DEBOUNCE_DELAY) {
        lastPressTime = currentTime;
        
        // Buttons S1-S4: Select preset from Teensy EEPROM
        if(i >= 0 && i <= 3) {
          selectedPreset = i;
          editMode = 0;
          
          currentColor = presetColors[selectedPreset];
          
          Serial.print("Selected ");
          if(animationMode) {
            Serial.print("Animation ");
          }
          Serial.print("Preset ");
          Serial.print(selectedPreset + 1);
          Serial.print(": R=");
          Serial.print(currentColor.r);
          Serial.print(" G=");
          Serial.print(currentColor.g);
          Serial.print(" B=");
          Serial.print(currentColor.b);
          Serial.print(" W=");
          Serial.println(currentColor.w);
          
          sendRGBWToLED(currentColor);
        }
        // Button S5 (EDIT): Cycle through edit modes
        else if(i == 4) {
          if(selectedPreset >= 0) {
            editMode = (editMode + 1) % 5;
            Serial.print("Edit mode: ");
            const char* modes[] = {"NEUTRAL", "R", "G", "B", "W"};
            Serial.println(modes[editMode]);
          }
        }
        // Button S6 (WRITE): Save to ItsyBitsy EEPROM
        else if(i == 5) {
          if(selectedPreset >= 0) {
            saveRGBWToItsyBitsy(currentColor);
            editMode = 0;
          }
        }
        // Button S7 (EXPORT): Save to Teensy EEPROM preset slot
        else if(i == 6) {
          if(selectedPreset >= 0) {
            presetColors[selectedPreset] = currentColor;
            savePresetToEEPROM(selectedPreset);
            sendRGBWToLED(currentColor);
            editMode = 0;
            Serial.println("Saved preset to Teensy EEPROM");
          }
        }
        // Button S8 (ANIM): Toggle Animation Mode
        else if(i == 7) {
          animationMode = !animationMode;
          digitalWrite(LED_S8, animationMode ? HIGH : LOW);
          Serial.print("Animation Mode: ");
          Serial.println(animationMode ? "ON" : "OFF");
        }
        
        updateDisplay();
      }
      break;
    }
  }
}


void setup() {
  Serial.begin(9600);
  delay(100);
  Serial.println("=== RGBW LED Controller Starting ===");
  
  // Initialize rotary encoder pins
  pinMode(ENCODER_A, INPUT_PULLUP);
  pinMode(ENCODER_B, INPUT_PULLUP);
  lastEncoderA = digitalRead(ENCODER_A);
  lastEncoderB = digitalRead(ENCODER_B);
  
  // Initialize LED indicator pin
  pinMode(LED_S8, OUTPUT);
  digitalWrite(LED_S8, LOW);
  
  // Initialize button pins with internal pull-up resistors
  pinMode(BUTTON_S1, INPUT_PULLUP);
  pinMode(BUTTON_S2, INPUT_PULLUP);
  pinMode(BUTTON_S3, INPUT_PULLUP);
  pinMode(BUTTON_S4, INPUT_PULLUP);
  pinMode(BUTTON_S5, INPUT_PULLUP);
  pinMode(BUTTON_S6, INPUT_PULLUP);
  pinMode(BUTTON_S7, INPUT_PULLUP);
  pinMode(BUTTON_S8, INPUT_PULLUP);
  
  // Initialize I2C for OLED (Wire on pins 18/19)
  Wire.setSDA(18);
  Wire.setSCL(19);
  Wire.begin();
  
  // Initialize I2C for ItsyBitsy (Wire1 on pins 16/17)
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
  display.println("RGBW LED");
  display.setCursor(10, 25);
  display.println("Controller");
  display.setCursor(20, 45);
  display.println("Ready!");
  display.display();
  
  // Initialize Teensy EEPROM (load or create RGB presets)
  initializeEEPROM();
  
  delay(2000);
  
  Serial.println("=== Teensy EEPROM RGBW Presets ===");
  for(int i = 0; i < 4; i++) {
    Serial.print("Preset ");
    Serial.print(i + 1);
    Serial.print(": R=");
    Serial.print(presetColors[i].r);
    Serial.print(" G=");
    Serial.print(presetColors[i].g);
    Serial.print(" B=");
    Serial.print(presetColors[i].b);
    Serial.print(" W=");
    Serial.println(presetColors[i].w);
  }
  Serial.println("==================================");
  
  // Show initial screen
  updateDisplay();
}

void loop() {
  // Read rotary encoder
  if(editMode > 0) {
    readEncoder();
  }
  
  // Handle blinking for active edit channel
  unsigned long currentTime = millis();
  if(currentTime - lastBlinkTime > BLINK_INTERVAL) {
    lastBlinkTime = currentTime;
    blinkState = !blinkState;
    if(editMode > 0) {
      updateDisplay();
    }
  }
  
  checkButtons();
  
  delay(10);
}



