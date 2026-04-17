#include <Arduino.h>
#include <Wire.h>

// Teensy 4.1 I2C Master - Communication Test
// Tests I2C communication with M0 devices

// I2C Configuration
const uint8_t I2C_BASE_ADDRESS = 0x08;
const uint8_t NUM_M0_DEVICES = 10;  // Up to 10 M0 devices (0x08 to 0x11)

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
