/* Animation test for OLED display on Teensy 4.0
SDA > pin 18 
SCL > pin 19
VCC > 3.3V
GND > GND
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1  // Reset pin (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C  // Common I2C address (try 0x3D if this doesn't work)

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void testText() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("OLED Test");
  display.println("Teensy 4.0");
  display.println();
  display.setTextSize(2);
  display.println("Success!");
  display.display();
  Serial.println("Text test complete");
}

void testShapes() {
  display.clearDisplay();
  
  // Draw rectangles
  display.drawRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, SSD1306_WHITE);
  display.fillRect(10, 10, 20, 20, SSD1306_WHITE);
  display.drawRect(35, 10, 20, 20, SSD1306_WHITE);
  
  // Draw circles
  display.drawCircle(80, 20, 10, SSD1306_WHITE);
  display.fillCircle(110, 20, 10, SSD1306_WHITE);
  
  // Draw lines
  display.drawLine(0, 40, SCREEN_WIDTH, 40, SSD1306_WHITE);
  display.drawLine(0, 45, SCREEN_WIDTH, 50, SSD1306_WHITE);
  
  display.display();
  Serial.println("Shapes test complete");
}

void testScrolling() {
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 0);
  display.println("Scroll");
  display.setCursor(10, 20);
  display.println("Test");
  display.display();
  
  // Scroll in various directions
  display.startscrollright(0x00, 0x0F);
  delay(2000);
  display.stopscroll();
  delay(500);
  
  display.startscrollleft(0x00, 0x0F);
  delay(2000);
  display.stopscroll();
  delay(500);
  
  display.startscrolldiagright(0x00, 0x07);
  delay(2000);
  display.stopscroll();
  
  Serial.println("Scrolling test complete");
}

void testAnimation() {
  display.clearDisplay();
  
  // Bouncing ball animation
  int x = 0, y = 32;
  int dx = 2, dy = 2;
  int radius = 5;
  
  for(int i = 0; i < 200; i++) {
    display.clearDisplay();
    display.fillCircle(x, y, radius, SSD1306_WHITE);
    display.display();
    
    x += dx;
    y += dy;
    
    // Bounce off edges
    if(x <= radius || x >= SCREEN_WIDTH - radius) dx = -dx;
    if(y <= radius || y >= SCREEN_HEIGHT - radius) dy = -dy;
    
    delay(20);
  }
  
  Serial.println("Animation test complete");
}

void setup() {
  Serial.begin(9600);
  
  // Initialize I2C on pins 18 (SDA) and 19 (SCL) - default for Teensy 4.0 Wire
  Wire.setSDA(18);
  Wire.setSCL(19);
  Wire.begin();
  
  delay(100);
  
  Serial.println("OLED Test Starting...");
  
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
  
  // Run test sequence
  testText();
  delay(2000);
  
  testShapes();
  delay(2000);
  
  testScrolling();
  delay(2000);
  
  testAnimation();
}

void drawRunningDog(int x, int y, int legFrame) {
  // Dog body
  display.fillRect(x, y, 16, 8, SSD1306_WHITE);
  // Dog head
  display.fillRect(x + 14, y - 2, 8, 8, SSD1306_WHITE);
  // Dog ear
  display.fillRect(x + 18, y - 6, 3, 5, SSD1306_WHITE);
  
  // Animated legs
  if(legFrame % 2 == 0) {
    display.fillRect(x + 2, y + 8, 2, 5, SSD1306_WHITE);   // Front left
    display.fillRect(x + 7, y + 8, 2, 3, SSD1306_WHITE);   // Front right
    display.fillRect(x + 10, y + 8, 2, 3, SSD1306_WHITE);  // Back left
    display.fillRect(x + 15, y + 8, 2, 5, SSD1306_WHITE);  // Back right
  } else {
    display.fillRect(x + 2, y + 8, 2, 3, SSD1306_WHITE);   // Front left
    display.fillRect(x + 7, y + 8, 2, 5, SSD1306_WHITE);   // Front right
    display.fillRect(x + 10, y + 8, 2, 5, SSD1306_WHITE);  // Back left
    display.fillRect(x + 15, y + 8, 2, 3, SSD1306_WHITE);  // Back right
  }
  
  // Tail
  display.drawLine(x + 1, y + 2, x - 3, y - 1, SSD1306_WHITE);
}

void drawCookingFood(int x, int y, int frame) {
  // Pot/pan
  display.drawRect(x, y, 20, 12, SSD1306_WHITE);
  display.fillRect(x + 1, y + 1, 18, 6, SSD1306_WHITE);
  display.drawLine(x - 2, y + 8, x, y + 8, SSD1306_WHITE);
  display.drawLine(x + 20, y + 8, x + 22, y + 8, SSD1306_WHITE);
  
  // Food in pot (circles bouncing)
  int bobAmount = (frame % 8 < 4) ? 1 : -1;
  display.fillCircle(x + 5, y + 3 + bobAmount, 2, SSD1306_WHITE);
  display.fillCircle(x + 10, y + 4 + (bobAmount * -1), 2, SSD1306_WHITE);
  display.fillCircle(x + 15, y + 3 + bobAmount, 2, SSD1306_WHITE);
  
  // Steam puffs
  int steamPhase = frame % 12;
  if(steamPhase < 6) {
    display.drawCircle(x + 4, y - 2 - steamPhase, 2, SSD1306_WHITE);
    display.drawCircle(x + 10, y - 1 - steamPhase, 2, SSD1306_WHITE);
    display.drawCircle(x + 16, y - 2 - steamPhase, 2, SSD1306_WHITE);
  }
}

void drawPizzaOven(int x, int y, int frame) {
  // Oven (rounded square)
  display.drawRect(x, y, 24, 18, SSD1306_WHITE);
  // Oven door
  display.drawRect(x + 2, y + 4, 20, 12, SSD1306_WHITE);
  // Pizza rotating inside
  int rotation = frame % 8;
  display.drawCircle(x + 12, y + 10, 5, SSD1306_WHITE);
  // Pizza slice animation
  for(int i = 0; i < 3; i++) {
    int angle = (rotation * 20 + i * 120) % 360;
    int px = x + 12 + (4 * cos(angle * 3.14159 / 180));
    int py = y + 10 + (4 * sin(angle * 3.14159 / 180));
    display.fillCircle(px, py, 1, SSD1306_WHITE);
  }
  // Heat waves
  if(frame % 4 < 2) {
    display.drawLine(x + 4, y - 1, x + 6, y - 3, SSD1306_WHITE);
    display.drawLine(x + 14, y - 1, x + 16, y - 3, SSD1306_WHITE);
  }
}

void drawFryer(int x, int y, int frame) {
  // Fryer machine body
  display.drawRect(x, y, 20, 16, SSD1306_WHITE);
  // Basket inside
  display.drawRect(x + 2, y + 2, 16, 8, SSD1306_WHITE);
  // Food bubbles (rising)
  int bubbleOffset = frame % 10;
  display.drawCircle(x + 5, y + 10 - bubbleOffset, 2, SSD1306_WHITE);
  display.drawCircle(x + 12, y + 11 - (bubbleOffset * 0.8), 2, SSD1306_WHITE);
  display.drawCircle(x + 18, y + 10 - (bubbleOffset * 0.6), 2, SSD1306_WHITE);
}

void loop() {
  static int animationCounter = 0;
  static int currentAnimation = 0;
  
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Show different animations in sequence
  switch(currentAnimation) {
    case 0:
      // Running dog animation - just one dog
      display.setCursor(0, 0);
      display.println("Running Dog!");
      drawRunningDog(40, 30, animationCounter);
      break;
      
    case 1:
      // Cooking food animation
      display.setCursor(0, 0);
      display.println("Cooking...");
      drawCookingFood(40, 25, animationCounter);
      break;
      
    case 2:
      // Pizza oven animation
      display.setCursor(0, 0);
      display.println("Pizza Time!");
      drawPizzaOven(40, 20, animationCounter);
      break;
      
    case 3:
      // Deep fryer animation
      display.setCursor(0, 0);
      display.println("Frying!");
      drawFryer(50, 25, animationCounter);
      break;
  }
  
  display.display();
  
  animationCounter++;
  
  // Change animation every 40 frames (~1.6 seconds at 25fps)
  if(animationCounter >= 40) {
    animationCounter = 0;
    currentAnimation = (currentAnimation + 1) % 4;
  }
  
  delay(40);
}
