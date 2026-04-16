#include <Arduino.h>
#include <Wire.h>

// MAIN BOARD (Teensy 4.1) - I2C Master
// I2C Communication via Wire1: SDA=Pin 18, SCL=Pin 19
// Sends LED data to connected PILL BOARDS via I2C

const int ONBOARD_LED = 13;  // Onboard LED for status indication

// I2C address range for pill boards
const int I2C_BASE_ADDRESS = 0x08;
const int MAX_PILL_BOARDS = 16;

// I2C communication tracking
bool connectedDevices[MAX_PILL_BOARDS] = {false};
int activeDeviceCount = 0;

// LED pattern settings
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 500; // Update every 500ms
uint8_t ledState = 0;

void scanI2CDevices() {
  Serial.println("==================== I2C SCAN START ====================");
  Serial.println("Scanning I2C bus for PILL BOARDS...");
  Serial.print("Testing addresses 0x");
  if (I2C_BASE_ADDRESS < 16) Serial.print("0");
  Serial.print(I2C_BASE_ADDRESS, HEX);
  Serial.print(" to 0x");
  uint8_t maxAddr = I2C_BASE_ADDRESS + MAX_PILL_BOARDS - 1;
  if (maxAddr < 16) Serial.print("0");
  Serial.print(maxAddr, HEX);
  Serial.println("...");
  Serial.println();
  
  // Visual: rapid blink during scan
  for (int i = 0; i < 5; i++) {
    digitalWrite(ONBOARD_LED, HIGH);
    delay(50);
    digitalWrite(ONBOARD_LED, LOW);
    delay(50);
  }
  
  activeDeviceCount = 0;
  
  // Reset connection tracking
  for (int i = 0; i < MAX_PILL_BOARDS; i++) {
    connectedDevices[i] = false;
  }
  
  // Scan only pill board address range
  for (int i = 0; i < MAX_PILL_BOARDS; i++) {
    uint8_t address = I2C_BASE_ADDRESS + i;
    
    // Pulse LED during each address check
    digitalWrite(ONBOARD_LED, HIGH);
    delay(10);
    
    Wire.beginTransmission(address);
    byte error = Wire.endTransmission(true);  // Send STOP condition
    
    digitalWrite(ONBOARD_LED, LOW);
    delay(10);
    
    Serial.print("  0x");
    if (address < 16) Serial.print("0");
    Serial.print(address, HEX);
    Serial.print(" -> ");
    
    if (error == 0) {
      connectedDevices[i] = true;
      activeDeviceCount++;
      Serial.print("FOUND! (Header: ");
      Serial.print(i, BIN);
      Serial.println(")");
      
      // Long blink for found device
      digitalWrite(ONBOARD_LED, HIGH);
      delay(300);
      digitalWrite(ONBOARD_LED, LOW);
      delay(100);
    } else {
      Serial.print("Not found (Error: ");
      Serial.print(error);
      Serial.println(")");
    }
  }
  
  Serial.println();
  if (activeDeviceCount == 0) {
    Serial.println("========================================");
    Serial.println(">>> NO PILL BOARDS DETECTED <<<");
    Serial.println("========================================");
    Serial.println("Troubleshooting:");
    Serial.println("1. Check SDA (Pin 18) and SCL (Pin 19) connections");
    Serial.println("2. Ensure M0 is powered and initialized");
    Serial.println("3. Check M0 serial output for its I2C address");
    Serial.println("4. Verify 4.7k pullup resistors on SDA/SCL lines");
    Serial.println("5. Confirm common ground between boards");
    Serial.println("========================================");
  } else {
    Serial.println("========================================");
    Serial.print(">>> SUCCESS! FOUND ");
    Serial.print(activeDeviceCount);
    Serial.println(" PILL BOARD(S) <<<");
    Serial.println(">>> I2C COMMUNICATION CONFIRMED! <<<");
    Serial.println("========================================");
  }
  Serial.println("==================== I2C SCAN END ======================");
  Serial.println();
}

void sendLEDData(uint8_t address, uint8_t data) {
  Wire.beginTransmission(address);
  Wire.write(data);
  byte error = Wire.endTransmission(true);  // Send STOP condition
  
  if (error == 0) {
    Serial.print("  -> 0x");
    if (address < 16) Serial.print("0");
    Serial.print(address, HEX);
    Serial.print(": Sent value ");
    Serial.print(data);
    Serial.print(" (");
    Serial.print(data > 0 ? "ON" : "OFF");
    Serial.println(") - SUCCESS");
  } else {
    Serial.print("  -> 0x");
    if (address < 16) Serial.print("0");
    Serial.print(address, HEX);
    Serial.print(": FAILED (Error code: ");
    Serial.print(error);
    Serial.println(")");
  }
}

void setup() {
  // FIRST THING: Configure and test onboard LED immediately
  pinMode(ONBOARD_LED, OUTPUT);
  
  // Immediate rapid blink to show Teensy is powered and code is running
  for (int i = 0; i < 10; i++) {
    digitalWrite(ONBOARD_LED, HIGH);
    delay(100);
    digitalWrite(ONBOARD_LED, LOW);
    delay(100);
  }
  
  // Initialize Serial for debugging
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("=== MAIN BOARD (Teensy 4.1) I2C Master ===");
  Serial.println("I2C Pins: SDA=18, SCL=19");
  Serial.println();
  
  // CRITICAL: Enable internal pull-ups on Teensy I2C pins
  // Since there are no external pull-ups on the Teensy side, we MUST enable these
  pinMode(18, INPUT_PULLUP);  // SDA - REQUIRED for I2C
  pinMode(19, INPUT_PULLUP);  // SCL - REQUIRED for I2C
  
  Serial.println(">>> Enabled internal pull-ups on Teensy pins 18 & 19");
  Serial.println(">>> CRITICAL: Using Wire (default I2C)");
  Serial.println(">>> Physical pins: SDA=18, SCL=19");
  Serial.println(">>> VERIFY M0 Pin 20 connects to Teensy Pin 18");
  Serial.println(">>> VERIFY M0 Pin 21 connects to Teensy Pin 19");
  Serial.println(">>> VERIFY common GND between boards");
  
  // Small delay for pull-ups to stabilize
  delay(100);
  
  // Initialize I2C as master on Wire (SDA=18, SCL=19)
  Wire.begin();
  Wire.setClock(100000); // 100kHz I2C clock speed
  Wire.setTimeout(1000); // 1 second timeout
  
  Serial.println("I2C Master initialized on Wire (default I2C bus)");
  Serial.println();
  
  // CONNECTIVITY TEST: Test if wires are actually connected
  Serial.println(">>> CONNECTIVITY TEST: Testing physical wire connections");
  Serial.println(">>> Setting Pin 18 HIGH for 2 seconds...");
  pinMode(18, OUTPUT);
  digitalWrite(18, HIGH);
  delay(2000);
  
  Serial.println(">>> Setting Pin 18 LOW for 2 seconds...");
  digitalWrite(18, LOW);
  delay(2000);
  
  Serial.println(">>> Check M0 serial - it should see Pin 20 change!");
  Serial.println(">>> If M0 doesn't see changes, wires are NOT connected!");
  Serial.println();
  
  // Now restore for I2C
  pinMode(18, INPUT_PULLUP);
  pinMode(19, INPUT_PULLUP);
  delay(100);
  
  // Test: Try to communicate with ANY I2C device (full bus scan)
  Serial.println(">>> PRE-TEST: Full I2C bus scan (0x01 to 0x7F)");
  int totalDevices = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    byte error = Wire.endTransmission(true);
    if (error == 0) {
      Serial.print("    Device found at 0x");
      if (addr < 16) Serial.print("0");
      Serial.println(addr, HEX);
      totalDevices++;
    }
  }
  if (totalDevices == 0) {
    Serial.println("    >>> NO I2C DEVICES FOUND ON ENTIRE BUS <<<");
    Serial.println("    >>> This indicates a wiring or power issue <<<");
  } else {
    Serial.print("    Total devices found: ");
    Serial.println(totalDevices);
  }
  Serial.println();
  
  // Blink 3 times to show starting scan
  for (int i = 0; i < 3; i++) {
    digitalWrite(ONBOARD_LED, HIGH);
    delay(200);
    digitalWrite(ONBOARD_LED, LOW);
    delay(200);
  }
  
  // Wait for pill boards to initialize
  Serial.println("Waiting 5 seconds for M0 to complete startup...");
  delay(5000);  // Longer delay to ensure M0 is fully ready
  
  // Scan for connected devices
  scanI2CDevices();
  
  // Blink onboard LED to show how many devices found
  Serial.print("Blinking ");
  Serial.print(activeDeviceCount);
  Serial.println(" times to show connected devices");
  
  for (int i = 0; i < activeDeviceCount; i++) {
    digitalWrite(ONBOARD_LED, HIGH);
    delay(300);
    digitalWrite(ONBOARD_LED, LOW);
    delay(300);
  }
  
  if (activeDeviceCount == 0) {
    // Rapid blink if no devices (error indicator)
    for (int i = 0; i < 10; i++) {
      digitalWrite(ONBOARD_LED, HIGH);
      delay(100);
      digitalWrite(ONBOARD_LED, LOW);
      delay(100);
    }
  }
  
  delay(1000);
}

void loop() {
  // Heartbeat blink to show Teensy is running
  static unsigned long lastBlink = 0;
  static bool blinkState = false;
  
  // Only send LED data if we have confirmed I2C communication
  if (activeDeviceCount > 0) {
    // Send LED data periodically
    if (millis() - lastUpdate >= updateInterval) {
      lastUpdate = millis();
      
      // Toggle LED state
      ledState = !ledState;
      
      Serial.println("========================================");
      Serial.print("Broadcasting LED State: ");
      Serial.println(ledState ? "ON (255)" : "OFF (0)");
      
      // Send only to connected pill boards
      for (int i = 0; i < MAX_PILL_BOARDS; i++) {
        if (connectedDevices[i]) {
          uint8_t address = I2C_BASE_ADDRESS + i;
          sendLEDData(address, ledState ? 255 : 0);
        }
      }
      
      // Blink LED to show transmission
      digitalWrite(ONBOARD_LED, HIGH);
      delay(100);
      digitalWrite(ONBOARD_LED, LOW);
      
      Serial.println("========================================");
      Serial.println();
    }
  } else {
    // No devices connected - heartbeat pattern (slow blink)
    if (millis() - lastBlink >= 500) {
      lastBlink = millis();
      blinkState = !blinkState;
      digitalWrite(ONBOARD_LED, blinkState);
    }
    
    // Periodically rescan for devices if none connected
    if (millis() - lastUpdate >= 5000) {
      lastUpdate = millis();
      Serial.println("[Rescan] No devices found, scanning again...");
      scanI2CDevices();
    }
  }
}
