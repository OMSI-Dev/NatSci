#include <Arduino.h>
#include <FastLED.h>

// LED Strip Configuration (APA102 / DotStar type)
#define NUM_LEDS 4
#define DATA_PIN 11
#define CLOCK_PIN 13
CRGB leds[NUM_LEDS];

// Button Configuration
#define BUTTON1_PIN 2
#define BUTTON2_PIN 3
#define BUTTON3_PIN 4
#define BUTTON4_PIN 5

// Button state tracking
bool lastButtonState[4] = {HIGH, HIGH, HIGH, HIGH};
bool currentButtonState[4] = {HIGH, HIGH, HIGH, HIGH};
unsigned long lastDebounceTime[4] = {0, 0, 0, 0};
const unsigned long debounceDelay = 50;

void setup() {
  // Initialize USB Serial for debugging
  Serial.begin(115200);
  delay(1000);
  Serial.println("Teensy 4.0 (Child) - Starting up...");
  
  // Initialize Serial1 for communication with Teensy 4.1
  Serial1.begin(115200);
  Serial.println("Serial1 initialized for communication with 4.1");
  
  // Setup buttons with internal pullup resistors
  pinMode(BUTTON1_PIN, INPUT_PULLUP);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);
  pinMode(BUTTON3_PIN, INPUT_PULLUP);
  pinMode(BUTTON4_PIN, INPUT_PULLUP);
  Serial.println("Buttons initialized on pins 2, 3, 4, 5");
  
  // Initialize LED strip
  FastLED.addLeds<APA102, DATA_PIN, CLOCK_PIN, BGR>(leds, NUM_LEDS);
  FastLED.setBrightness(50);
  
  // Turn off all LEDs initially
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Black;
  }
  FastLED.show();
  Serial.println("LED strip initialized on pins 11 (DATA), 13 (CLOCK)");
  Serial.println("Ready to send button data and receive LED commands");
}

void loop() {
  // Read button states with debouncing
  int buttonPins[4] = {BUTTON1_PIN, BUTTON2_PIN, BUTTON3_PIN, BUTTON4_PIN};
  
  for (int i = 0; i < 4; i++) {
    int reading = digitalRead(buttonPins[i]);
    
    if (reading != lastButtonState[i]) {
      lastDebounceTime[i] = millis();
    }
    
    if ((millis() - lastDebounceTime[i]) > debounceDelay) {
      if (reading != currentButtonState[i]) {
        currentButtonState[i] = reading;
        
        // Button pressed (LOW because of INPUT_PULLUP)
        if (currentButtonState[i] == LOW) {
          // Send button press to Teensy 4.1
          Serial1.print("BTN:");
          Serial1.println(i + 1);  // Buttons numbered 1-4
          
          Serial.print("Button ");
          Serial.print(i + 1);
          Serial.println(" pressed - Sent to 4.1");
        }
      }
    }
    
    lastButtonState[i] = reading;
  }
  
  // Check for LED commands from Teensy 4.1
  if (Serial1.available()) {
    String command = Serial1.readStringUntil('\n');
    command.trim();
    
    Serial.print("Received command from 4.1: ");
    Serial.println(command);
    
    // Parse command format: "LED:X" where X is 1-4
    if (command.startsWith("LED:")) {
      int ledNum = command.substring(4).toInt();
      
      if (ledNum >= 1 && ledNum <= NUM_LEDS) {
        // Turn off all LEDs
        for (int i = 0; i < NUM_LEDS; i++) {
          leds[i] = CRGB::Black;
        }
        
        // Turn on the specified LED
        leds[ledNum - 1] = CRGB::Green;
        FastLED.show();
        
        Serial.print("LED ");
        Serial.print(ledNum);
        Serial.println(" turned ON (Green)");
      }
    }
  }
  
  delay(10);  // Small delay to prevent overwhelming the serial buffer
}