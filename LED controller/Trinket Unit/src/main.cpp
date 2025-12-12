#include <Wire.h>
#include <Arduino.h>


#define I2C_ADDRESS 0x10

volatile bool dataReceived = false;

void receiveEvent(int bytes) {
  dataReceived = true;
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // Turn on when data received
  
  while(Wire.available()) {
    Wire.read();
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  // 3 fast blinks on startup
  for(int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
  
  delay(100);
  
  // Initialize I2C BEFORE setting callback
  Wire.begin(I2C_ADDRESS);
  delay(10);
  Wire.onReceive(receiveEvent);
  
  // Heartbeat blink = waiting
  while(!dataReceived) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);
    delay(950);
  }
}

void loop() {
  // If we get here, I2C worked
  digitalWrite(LED_BUILTIN, HIGH);
  delay(10);
}