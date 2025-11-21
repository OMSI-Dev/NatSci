#include <Wire.h>

// I2C address of Trinket M0
#define TRINKET_ADDRESS 0x10

// Button pin
#define BUTTON_PIN 2

// RGB colors to cycle through
uint8_t colors[][3] = {
  {255, 0, 0},    // Red
  {0, 255, 0},    // Green
  {0, 0, 255},    // Blue
  {255, 255, 0},  // Yellow
  {255, 0, 255},  // Magenta
  {0, 255, 255},  // Cyan
  {255, 128, 0},  // Orange
  {255, 255, 255} // White
};

int colorIndex = 0;
bool lastButtonState = HIGH;
bool buttonPressed = false;

void setup() {
  Serial.begin(9600);
  Wire.begin();  // Initialize I2C as master
  
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  Serial.println("Teensy I2C Master Ready");
  Serial.println("Press button to send colors to Trinket");
}

void sendColorToTrinket(uint8_t r, uint8_t g, uint8_t b) {
  Serial.print("Sending RGB: ");
  Serial.print(r); Serial.print(", ");
  Serial.print(g); Serial.print(", ");
  Serial.println(b);
  
  Wire.beginTransmission(TRINKET_ADDRESS);
  Wire.write(r);  // Red
  Wire.write(g);  // Green
  Wire.write(b);  // Blue
  byte error = Wire.endTransmission();
  
  if (error == 0) {
    Serial.println("✓ Transmission successful");
  } else {
    Serial.print("✗ Transmission error: ");
    Serial.println(error);
  }
  
  Serial.println("---");
}

void loop() {
  // Read button with debouncing
  bool currentButtonState = digitalRead(BUTTON_PIN);
  
  // Detect button press (HIGH to LOW transition)
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    buttonPressed = true;
    delay(50); // Debounce delay
  }
  
  lastButtonState = currentButtonState;
  
  // If button was pressed, send color
  if (buttonPressed) {
    sendColorToTrinket(colors[colorIndex][0], 
                       colors[colorIndex][1], 
                       colors[colorIndex][2]);
    
    // Move to next color
    colorIndex = (colorIndex + 1) % 8;
    
    buttonPressed = false;
  }
}

