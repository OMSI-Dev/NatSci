/* For Teensy 4.0

OLED display:
SDA > pin 18 
SCL > pin 19
VCC > 3.3V
GND > GND

Button legs 1 > pins 2-8
Button legs 2 > GND
*/


#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1  // Reset pin (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C  // Common I2C address (try 0x3D if this doesn't work)

// Button pins
#define BUTTON_1 2
#define BUTTON_2 3
#define BUTTON_3 4
#define BUTTON_4 5
#define BUTTON_5 6
#define BUTTON_6 7
#define BUTTON_7 8

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Button states and timing
int lastButtonPressed = 0;
unsigned long lastPressTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;

void checkButtons() {
  // Check each button pin
  int buttonPins[] = {BUTTON_1, BUTTON_2, BUTTON_3, BUTTON_4, BUTTON_5, BUTTON_6, BUTTON_7};
  
  for(int i = 0; i < 7; i++) {
    int pinState = digitalRead(buttonPins[i]);
    
    if(pinState == LOW) {  // Button pressed (LOW)
      unsigned long currentTime = millis();
      if(currentTime - lastPressTime > DEBOUNCE_DELAY) {
        lastButtonPressed = i + 1;  // Button number 1-7
        lastPressTime = currentTime;
        Serial.print("Button ");
        Serial.print(lastButtonPressed);
        Serial.println(" Pressed");
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize button pins as inputs with pull-up
  pinMode(BUTTON_1, INPUT_PULLUP);
  pinMode(BUTTON_2, INPUT_PULLUP);
  pinMode(BUTTON_3, INPUT_PULLUP);
  pinMode(BUTTON_4, INPUT_PULLUP);
  pinMode(BUTTON_5, INPUT_PULLUP);
  pinMode(BUTTON_6, INPUT_PULLUP);
  pinMode(BUTTON_7, INPUT_PULLUP);
  
  // Initialize Wire on pins 18 (SDA) and 19 (SCL) for OLED (5V bus)
  Wire.setSDA(18);
  Wire.setSCL(19);
  Wire.begin();
  
  // Initialize Wire1 on pins 16 (SDA) and 17 (SCL) for Trinket (3.3V bus)
  Wire1.setSDA(16);
  Wire1.setSCL(17);
  Wire1.begin();
  
  delay(100);
  
  Serial.println("Button Test Starting...");
  
  // Initialize display
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("SSD1306 allocation failed");
    Serial.println("Check connections and I2C address (try 0x3D if 0x3C fails)");
    for(;;); // Don't proceed, loop forever
  }
  
  Serial.println("Display initialized successfully!");
  
  // Clear the buffer
  display.clearDisplay();
  display.display();
  delay(500);
  
  // Show startup message
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(15, 25);
  display.println("Button Test");
  display.setTextSize(1);
  display.setCursor(20, 50);
  display.println("Press buttons 1-7");
  display.display();
  
  delay(2000);
}

void sendColorToTrinket(uint8_t red, uint8_t green, uint8_t blue) {
  // Send RGB color to Trinket M0 (I2C address 0x10) via Wire1
  Wire1.beginTransmission(0x10);
  Wire1.write(red);
  Wire1.write(green);
  Wire1.write(blue);
  Wire1.endTransmission();
  
  Serial.print("Sent to Trinket - R:");
  Serial.print(red);
  Serial.print(" G:");
  Serial.print(green);
  Serial.print(" B:");
  Serial.println(blue);
}

void displayButtonFeedback() {
  display.clearDisplay();
  display.setTextSize(3);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(40, 15);
  display.println("Button");
  display.setCursor(50, 40);
  display.setTextSize(4);
  display.println(lastButtonPressed);
  display.display();
}

void loop() {
  // Check for button presses
  checkButtons();
  
  // Display feedback on OLED
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Button Test - Raw Pins");
  display.println("Pin 2-8 States:");
  display.println();
  
  // Display each pin state on OLED
  int buttonPins[] = {BUTTON_1, BUTTON_2, BUTTON_3, BUTTON_4, BUTTON_5, BUTTON_6, BUTTON_7};
  for(int i = 0; i < 7; i++) {
    display.print("Pin ");
    display.print(buttonPins[i]);
    display.print(": ");
    display.println(digitalRead(buttonPins[i]) == LOW ? "PRESS" : "HIGH");
  }
  
  if(lastButtonPressed > 0) {
    display.println();
    display.setTextSize(2);
    display.print("Button: ");
    display.println(lastButtonPressed);
    
    // Send different colors to Trinket based on button pressed
    // Example: each button triggers a different color
    uint8_t colorMap[7][3] = {
      {255, 0, 0},    // Button 1: Red
      {0, 255, 0},    // Button 2: Green
      {0, 0, 255},    // Button 3: Blue
      {255, 255, 0},  // Button 4: Yellow
      {255, 0, 255},  // Button 5: Magenta
      {0, 255, 255},  // Button 6: Cyan
      {255, 255, 255} // Button 7: White
    };
    
    sendColorToTrinket(colorMap[lastButtonPressed-1][0], 
                       colorMap[lastButtonPressed-1][1], 
                       colorMap[lastButtonPressed-1][2]);
    
    lastButtonPressed = 0;  // Reset so it only sends once per press
  }
  
  display.display();
  
  delay(200);  // Update less frequently for readability
}
