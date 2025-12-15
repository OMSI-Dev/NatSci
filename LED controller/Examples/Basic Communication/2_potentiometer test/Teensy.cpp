/* Teensy 4.0 LED Controller
 * 
 * Hardware connections:
 * - OLED Display (128x64): SDA > pin 18, SCL > pin 19, VCC > 3.3V, GND > GND
 * - Buttons 1-7: One leg > pins 2-8, Other leg > GND
 * - Potentiometer: Wiper > pin A0 (pin 14), VCC > 3.3V, GND > GND
 * - I2C to Trinket: Wire1 on pins 16/17 (3.3V bus)
 * - I2C to OLED: Wire on pins 18/19 (3.3V bus)
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

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
#define BUTTON_5 6
#define BUTTON_6 7
#define BUTTON_7 8

// Potentiometer pin
#define POT_PIN A0  // Pin 14

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Color presets for each button (RGB)
uint8_t colorMap[7][3] = {
  {255, 0, 0},    // Button 1: Red
  {0, 255, 0},    // Button 2: Green
  {0, 0, 255},    // Button 3: Blue
  {255, 255, 0},  // Button 4: Yellow
  {255, 0, 255},  // Button 5: Magenta
  {0, 255, 255},  // Button 6: Cyan
  {255, 255, 255} // Button 7: White
};

const char* colorNames[7] = {"RED", "GREEN", "BLUE", "YELLOW", "MAGENTA", "CYAN", "WHITE"};

// Button state tracking
int lastButtonPressed = 0;
unsigned long lastPressTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// Current color being displayed
uint8_t currentColor[3] = {0, 0, 0};  // Start with off

// Potentiometer value (0-255)
uint8_t potValue = 0;
uint8_t lastPotValue = 0;

void sendColorToTrinket(uint8_t red, uint8_t green, uint8_t blue) {
  Wire1.beginTransmission(TRINKET_ADDRESS);
  Wire1.write(red);
  Wire1.write(green);
  Wire1.write(blue);
  byte error = Wire1.endTransmission();
  
  if (error == 0) {
    Serial.print("✓ Sent RGB(");
    Serial.print(red);
    Serial.print(",");
    Serial.print(green);
    Serial.print(",");
    Serial.print(blue);
    Serial.println(")");
  } else {
    Serial.print("✗ I2C Error: ");
    Serial.println(error);
  }
}

void updateDisplay() {
  display.clearDisplay();
  
  // Title
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("LED Controller");
  Serial.println(lastButtonPressed);
  
  // Potentiometer value
  display.setCursor(0, 12);
  display.print("Pot: ");
  display.print(potValue);
  display.print(" (R-tweak)");
  
  // Current color name
  if(lastButtonPressed > 0) {
    display.setTextSize(2);
    display.setCursor(10, 26);
    display.println(colorNames[lastButtonPressed - 1]);
    
    // RGB values
    display.setTextSize(1);
    display.setCursor(10, 50);
    display.print("R:");
    display.print(currentColor[0]);
    display.print(" G:");
    display.print(currentColor[1]);
    display.print(" B:");
    display.println(currentColor[2]);
  } else {
    display.setTextSize(2);
    display.setCursor(25, 30);
    display.println("Press");
    display.setCursor(15, 48);
    display.println("Button");
  }
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
        lastButtonPressed = i + 1;  // Store button number (1-7)
        lastPressTime = currentTime;
        
        // Update current color from color map
        currentColor[0] = colorMap[i][0];
        currentColor[1] = colorMap[i][1];
        currentColor[2] = colorMap[i][2];
        
        // Apply potentiometer tweak to red channel
        currentColor[0] = potValue;
        
        Serial.print("Button ");
        Serial.print(lastButtonPressed);
        Serial.print(" pressed: ");
        Serial.print(colorNames[i]);
        Serial.print(" (R tweaked to ");
        Serial.print(potValue);
        Serial.println(")");
        
        // Send color to Trinket
        sendColorToTrinket(currentColor[0], currentColor[1], currentColor[2]);
        
        // Update display
        updateDisplay();
      }
      break;  // Only process one button at a time
    }
  }
}


void setup() {
  Serial.begin(9600);
  
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
  
  Serial.println("Teensy LED Controller Starting...");
  
  // Initialize OLED display
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("✗ OLED init failed! Check connections.");
    for(;;);  // Stop if display fails
  }
  
  Serial.println("✓ OLED initialized");
  
  // Show startup screen
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(5, 10);
  display.println("LED Ctrl");
  display.setTextSize(1);
  display.setCursor(15, 35);
  display.println("Ready!");
  display.setCursor(5, 50);
  display.println("Press 1-7");
  display.display();
  
  delay(2000);
  
  // Show initial screen
  updateDisplay();
  
  Serial.println("System Ready!");
  Serial.println("Press buttons 1-7 to select colors");
  Serial.println("---");
}

void loop() {
  // Read potentiometer value
  potValue = readPotentiometer();
  
  // Check if pot value changed (hysteresis to avoid jitter)
  if(abs(potValue - lastPotValue) > 1) {
    lastPotValue = potValue;
    
    // If a button has been pressed, update the LED strip
    if(lastButtonPressed > 0) {
      // Update red channel with new pot value
      currentColor[0] = potValue;
      
      // Send updated color to Trinket immediately
      sendColorToTrinket(currentColor[0], currentColor[1], currentColor[2]);
    }
    
    // Always update display to show new pot value
    updateDisplay();
  }
  
  checkButtons();
  
  delay(5);  // Small delay to prevent excessive polling
}