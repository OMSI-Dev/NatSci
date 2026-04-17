/*
 * TEST 1 - TEENSY BOARD
 * Monitor I2C bus for M0 addresses
 * Wait for 2x M0 boards to initialize
 * Maintain active communication with both devices
 */

#include <Arduino.h>
#include <Wire.h>

// I2C Configuration
const uint8_t I2C_BASE_ADDRESS = 0x08;
const uint8_t MAX_M0_DEVICES = 10;
const uint8_t REQUIRED_M0_DEVICES = 2;  // Wait for 2 M0 boards

// Device tracking
uint8_t detectedAddresses[MAX_M0_DEVICES];
uint8_t numDetectedDevices = 0;
bool systemReady = false;

// Timing
unsigned long lastScan = 0;
unsigned long lastComm = 0;
const unsigned long scanInterval = 3000;    // Scan every 3 seconds
const unsigned long commInterval = 1000;    // Communicate every 1 second

// Forward declarations
void scanForM0Devices();
void communicateWithDevices();
void printStatus();

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println("\n========================================");
  Serial.println("   TEST 1 - TEENSY I2C MASTER");
  Serial.println("========================================\n");
  
  Serial.println("I2C Configuration:");
  Serial.println("  SDA: Pin 18");
  Serial.println("  SCL: Pin 19");
  Serial.println("  Speed: 100 kHz\n");
  
  // Initialize I2C as master
  Wire.begin();
  Wire.setClock(100000);
  
  Serial.println("I2C Master initialized\n");
  Serial.print("Waiting for ");
  Serial.print(REQUIRED_M0_DEVICES);
  Serial.println(" M0 devices to connect...\n");
  
  delay(500);
}

void scanForM0Devices() {
  Serial.println("--- Scanning for M0 Devices ---");
  
  numDetectedDevices = 0;
  
  // Scan the M0 address range (0x08-0x11)
  for (uint8_t addr = I2C_BASE_ADDRESS; addr < (I2C_BASE_ADDRESS + MAX_M0_DEVICES); addr++) {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      // Device found!
      detectedAddresses[numDetectedDevices] = addr;
      numDetectedDevices++;
      
      Serial.print("  ✓ M0 found at 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      
      // Request counter value to verify communication
      uint8_t bytesReceived = Wire.requestFrom(addr, (uint8_t)1);
      if (bytesReceived > 0) {
        uint8_t counter = Wire.read();
        Serial.print(" (counter: ");
        Serial.print(counter);
        Serial.println(")");
      } else {
        Serial.println(" (no data)");
      }
    }
    
    delay(5);
  }
  
  Serial.print("\nDevices found: ");
  Serial.print(numDetectedDevices);
  Serial.print(" / ");
  Serial.println(REQUIRED_M0_DEVICES);
  
  if (numDetectedDevices >= REQUIRED_M0_DEVICES && !systemReady) {
    systemReady = true;
    Serial.println("\n*** SYSTEM READY ***");
    Serial.println("Beginning active communication...\n");
  } else if (numDetectedDevices < REQUIRED_M0_DEVICES) {
    Serial.println("Waiting for more devices...\n");
  }
  
  Serial.println("-------------------------------\n");
}

void communicateWithDevices() {
  if (!systemReady) return;
  
  static uint8_t commandIndex = 0;
  
  // Cycle through different commands
  uint8_t commands[] = {0xFF, 0x00, 0x05, 0x0A};  // ON, OFF, color1, color2
  uint8_t currentCommand = commands[commandIndex % 4];
  commandIndex++;
  
  Serial.println("--- Active Communication ---");
  
  for (uint8_t i = 0; i < numDetectedDevices; i++) {
    uint8_t addr = detectedAddresses[i];
    
    // Request data from M0
    uint8_t bytesReceived = Wire.requestFrom(addr, (uint8_t)1);
    
    if (bytesReceived > 0) {
      uint8_t counter = Wire.read();
      Serial.print("[RX from 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print("] Counter: ");
      Serial.println(counter);
    }
    
    // Send command to M0
    Wire.beginTransmission(addr);
    Wire.write(currentCommand);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("[TX to 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print("] Command: 0x");
      if (currentCommand < 16) Serial.print("0");
      Serial.println(currentCommand, HEX);
    } else {
      Serial.print("[ERROR] Failed to send to 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print(" - Error code: ");
      Serial.println(error);
    }
    
    delay(50);
  }
  
  Serial.println("----------------------------\n");
}

void printStatus() {
  Serial.println("\n=== SYSTEM STATUS ===");
  Serial.print("Devices detected: ");
  Serial.println(numDetectedDevices);
  Serial.print("System ready: ");
  Serial.println(systemReady ? "YES" : "NO");
  
  if (numDetectedDevices > 0) {
    Serial.println("\nActive addresses:");
    for (uint8_t i = 0; i < numDetectedDevices; i++) {
      Serial.print("  Device ");
      Serial.print(i + 1);
      Serial.print(": 0x");
      if (detectedAddresses[i] < 16) Serial.print("0");
      Serial.println(detectedAddresses[i], HEX);
    }
  }
  Serial.println("=====================\n");
}

void loop() {
  // Scan for devices periodically
  if (millis() - lastScan >= scanInterval) {
    lastScan = millis();
    scanForM0Devices();
  }
  
  // Communicate with devices when system is ready
  if (systemReady && (millis() - lastComm >= commInterval)) {
    lastComm = millis();
    communicateWithDevices();
  }
  
  // Check for serial commands
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    switch(cmd) {
      case 's':
      case 'S':
        Serial.println("\nManual scan requested...");
        scanForM0Devices();
        break;
        
      case 'i':
      case 'I':
        printStatus();
        break;
        
      case '?':
      case 'h':
      case 'H':
        Serial.println("\n=== COMMANDS ===");
        Serial.println("s - Scan for M0 devices");
        Serial.println("i - Show system status");
        Serial.println("h - Show this help");
        Serial.println("================\n");
        break;
    }
    
    // Clear serial buffer
    while (Serial.available()) Serial.read();
  }
  
  delay(10);
}

// Timing
unsigned long lastScan = 0;
const unsigned long scanInterval = 2000;  // Scan every 2 seconds

// Forward declarations
void requestAddressConfirmation(uint8_t addr);
void sendTestData(uint8_t addr, uint8_t data);
void scanI2CDevices();
void fullI2CScan();
void printI2CInfo();

void setup() 
{
  Serial.begin(115200);
  
  // Wait for serial port to connect (optional, useful for debugging)
  while (!Serial && millis() < 3000) {
    ; // wait up to 3 seconds
  }
  
  Serial.println("=== Teensy 4.1 I2C Master - Communication Test ===");
  Serial.println();
  
  // Print I2C pin information
  printI2CInfo();
  
  // Initialize I2C as master
  Wire.begin();
  Wire.setClock(100000);  // 100kHz I2C speed (standard mode)
  
  Serial.println("I2C Master initialized");
  Serial.println("Clock speed: 100 kHz (Standard Mode)");
  Serial.println();
  
  delay(100);
  
  Serial.println("Starting initial full I2C scan (0x01-0x7F)...");
  fullI2CScan();
  Serial.println();
}

void printI2CInfo()
{
  Serial.println("--- I2C Configuration ---");
  Serial.println("Teensy 4.1 I2C Pins (Wire/I2C0):");
  Serial.println("  SDA: Pin 18");
  Serial.println("  SCL: Pin 19");
  Serial.println();
  Serial.println("IMPORTANT: Ensure 4.7kΩ pull-up resistors are connected");
  Serial.println("between SDA/SCL and 3.3V if not already present!");
  Serial.println("-------------------------");
  Serial.println();
}

void fullI2CScan()
{
  Serial.println("\n--- Full I2C Bus Scan (0x01-0x7F) ---");
  uint8_t devicesFound = 0;
  uint8_t error;
  
  for (uint8_t addr = 1; addr < 127; addr++)
  {
    Wire.beginTransmission(addr);
    error = Wire.endTransmission();
    
    if (error == 0)
    {
      devicesFound++;
      Serial.print("Device found at address: 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print(" (");
      Serial.print(addr);
      Serial.println(")");
    }
    else if (error == 4)
    {
      Serial.print("Unknown error at address: 0x");
      if (addr < 16) Serial.print("0");
      Serial.println(addr, HEX);
    }
    // error == 2 means NACK (no device), don't print
    
    delay(5);
  }
  
  if (devicesFound == 0)
  {
    Serial.println("*** NO DEVICES FOUND ON I2C BUS ***");
    Serial.println();
    Serial.println("Troubleshooting:");
    Serial.println("1. Check wiring: SDA to pin 18, SCL to pin 19");
    Serial.println("2. Verify pull-up resistors (4.7kΩ) on SDA and SCL");
    Serial.println("3. Ensure M0 device is powered and running");
    Serial.println("4. Check M0 serial output for I2C address");
    Serial.println("5. Verify common ground between Teensy and M0");
  }
  else
  {
    Serial.print("\nTotal devices found: ");
    Serial.println(devicesFound);
  }
  Serial.println("--- Full Scan Complete ---\n");
}

void scanI2CDevices()
{
  Serial.println("\n--- M0 Device Scan (0x08-0x11) ---");
  uint8_t devicesFound = 0;
  
  for (uint8_t addr = I2C_BASE_ADDRESS; addr < (I2C_BASE_ADDRESS + NUM_M0_DEVICES); addr++)
  {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0)
    {
      devicesFound++;
      Serial.print("Device found at address: 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      Serial.print(" (");
      Serial.print(addr);
      Serial.println(")");
      
      // Request address confirmation
      requestAddressConfirmation(addr);
    }
    else if (error == 4)
    {
      Serial.print("Unknown error at address: 0x");
      if (addr < 16) Serial.print("0");
      Serial.println(addr, HEX);
    }
    // error == 2 means NACK on address (no device)
    
    delay(10);  // Small delay between scans
  }
  
  if (devicesFound == 0)
  {
    Serial.println("No M0 devices found in range 0x08-0x11");
    Serial.println("Try 'f' for full bus scan or check wiring/power");
  }
  else
  {
    Serial.print("\nTotal M0 devices found: ");
    Serial.println(devicesFound);
  }
  Serial.println("--- Scan Complete ---\n");
}

void requestAddressConfirmation(uint8_t addr)
{
  // Request 1 byte from the M0 device
  uint8_t bytesReceived = Wire.requestFrom(addr, (uint8_t)1);
  
  if (bytesReceived > 0)
  {
    uint8_t response = Wire.read();
    Serial.print("  -> Response: 0x");
    if (response < 16) Serial.print("0");
    Serial.print(response, HEX);
    
    if (response == addr)
    {
      Serial.println(" ✓ Address confirmed!");
    }
    else
    {
      Serial.println(" ✗ Address mismatch!");
    }
  }
  else
  {
    Serial.println("  -> No response from device");
  }
}

void sendTestData(uint8_t addr, uint8_t data)
{
  Wire.beginTransmission(addr);
  Wire.write(data);
  uint8_t error = Wire.endTransmission();
  
  if (error == 0)
  {
    Serial.print("Sent data 0x");
    if (data < 16) Serial.print("0");
    Serial.print(data, HEX);
    Serial.print(" to device 0x");
    if (addr < 16) Serial.print("0");
    Serial.println(addr, HEX);
  }
  else
  {
    Serial.print("Error sending to 0x");
    if (addr < 16) Serial.print("0");
    Serial.print(addr, HEX);
    Serial.print(" - Error code: ");
    Serial.println(error);
  }
}

void loop() 
{
  // Periodic device scan
  if (millis() - lastScan >= scanInterval)
  {
    lastScan = millis();
    scanI2CDevices();
  }
  
  // Check for serial commands
  if (Serial.available() > 0)
  {
    char cmd = Serial.read();
    
    switch(cmd)
    {
      case 's':
      case 'S':
        Serial.println("\nM0 device scan requested...");
        scanI2CDevices();
        break;
        
      case 'f':
      case 'F':
        Serial.println("\nFull I2C bus scan requested...");
        fullI2CScan();
        break;
        
      case 't':
      case 'T':
        Serial.println("\nSending test data to all M0 devices...");
        for (uint8_t addr = I2C_BASE_ADDRESS; addr < (I2C_BASE_ADDRESS + NUM_M0_DEVICES); addr++)
        {
          sendTestData(addr, 0xFF);  // Send test byte
          delay(10);
        }
        break;
        
      case 'i':
      case 'I':
        printI2CInfo();
        break;
        
      case '?':
      case 'h':
      case 'H':
        Serial.println("\n=== Commands ===");
        Serial.println("s - Scan for M0 devices (0x08-0x11)");
        Serial.println("f - Full I2C bus scan (0x01-0x7F)");
        Serial.println("t - Send test data to all M0 devices");
        Serial.println("i - Show I2C pin information");
        Serial.println("h - Show this help");
        Serial.println();
        break;
        
      default:
        break;
    }
    
    // Clear remaining serial buffer
    while (Serial.available()) Serial.read();
  }
  
  delay(10);
}
