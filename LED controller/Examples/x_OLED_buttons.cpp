/* Button input test for OLED display on Teensy 4.0
SDA > pin 18 
SCL > pin 19
VCC > 3.3V
GND > GND
Buttons > pins 2-8
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
    if(digitalRead(buttonPins[i]) == LOW) {  // Button pressed (LOW)
      unsigned long currentTime = millis();
      if(currentTime - lastPressTime > DEBOUNCE_DELAY) {
        lastButtonPressed = i + 1;  // Button number 1-7
        lastPressTime = currentTime;
        Serial.print("Button ");
        Serial.print(lastButtonPressed);
        Serial.println(" pressed");
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
  
  // Initialize I2C on pins 18 (SDA) and 19 (SCL) - default for Teensy 4.0 Wire
  Wire.setSDA(18);
  Wire.setSCL(19);
  Wire.begin();
  
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
  
  // Display feedback
  displayButtonFeedback();
  
  delay(50);
}
