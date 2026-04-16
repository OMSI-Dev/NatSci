#include <Arduino.h>
#include <Wire.h>

// PILL BOARD (M0 Express) - I2C Slave with Address Initialization
// Header pins for I2C address configuration
const int HEADER_PIN_A = 3;
const int HEADER_PIN_B = 4;
const int HEADER_PIN_C = 5;
const int HEADER_PIN_D = 7;

// LED output pin
const int LED_OUTPUT_PIN = 2;

// I2C base address
const int I2C_BASE_ADDRESS = 0x08;

// Global variables
uint8_t myI2CAddress = 0;
volatile uint8_t ledData = 0;
volatile bool newDataReceived = false;

// I2C receive callback
void receiveEvent(int numBytes) {
  if (numBytes > 0) {
    ledData = Wire.read();
    newDataReceived = true;
    
    // Clear any remaining bytes
    while (Wire.available()) {
      Wire.read();
    }
  }
}

uint8_t readHeaderPins() {
  uint8_t addressOffset = 0;
  
  // Read each header pin and build address offset
  if (digitalRead(HEADER_PIN_A) == HIGH) addressOffset |= 0x01;
  if (digitalRead(HEADER_PIN_B) == HIGH) addressOffset |= 0x02;
  if (digitalRead(HEADER_PIN_C) == HIGH) addressOffset |= 0x04;
  if (digitalRead(HEADER_PIN_D) == HIGH) addressOffset |= 0x08;
  
  return addressOffset;
}

void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("=== PILL BOARD (M0 Express) I2C Slave ===");
  
  // Configure header pins as inputs with pulldown
  pinMode(HEADER_PIN_A, INPUT_PULLDOWN);
  pinMode(HEADER_PIN_B, INPUT_PULLDOWN);
  pinMode(HEADER_PIN_C, INPUT_PULLDOWN);
  pinMode(HEADER_PIN_D, INPUT_PULLDOWN);
  
  // Configure LED output pin
  pinMode(LED_OUTPUT_PIN, OUTPUT);
  digitalWrite(LED_OUTPUT_PIN, LOW);
  
  // Read header pins to determine I2C address
  uint8_t addressOffset = readHeaderPins();
  myI2CAddress = I2C_BASE_ADDRESS + addressOffset;
  
  Serial.print("Header Pin Configuration: ");
  Serial.print("A="); Serial.print(digitalRead(HEADER_PIN_A));
  Serial.print(" B="); Serial.print(digitalRead(HEADER_PIN_B));
  Serial.print(" C="); Serial.print(digitalRead(HEADER_PIN_C));
  Serial.print(" D="); Serial.print(digitalRead(HEADER_PIN_D));
  Serial.println();
  
  Serial.print("I2C Address Offset: 0x");
  Serial.println(addressOffset, HEX);
  Serial.print("My I2C Address: 0x");
  Serial.println(myI2CAddress, HEX);
  
  // Initialize I2C as slave
  Wire.begin(myI2CAddress);
  Wire.onReceive(receiveEvent);
  
  Serial.println("I2C Slave initialized. Waiting for data...");
  Serial.println();
}

void loop() {
  // Check if new LED data has been received
  if (newDataReceived) {
    newDataReceived = false;
    
    // Output LED data to Pin 2
    digitalWrite(LED_OUTPUT_PIN, ledData ? HIGH : LOW);
    
    Serial.print("LED Data Received: ");
    Serial.print(ledData);
    Serial.print(" -> Pin 2 set to ");
    Serial.println(ledData ? "HIGH" : "LOW");
  }
  
  delay(10); // Small delay to prevent overwhelming the serial output
}

