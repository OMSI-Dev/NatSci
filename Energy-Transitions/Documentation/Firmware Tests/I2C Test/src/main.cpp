/*
 * I2C DIAGNOSTIC FIRMWARE - TEENSY 4.1
 *
 * Standalone test sketch for probing the M0 sensor boards.
 *
 * STAGED FASTLED CULPRIT TEST:g
 *   Stage 1 (boot): scan all buses BEFORE FastLED is initialized (baseline)
 *   Stage 2 (boot): init FastLED exactly like the game firmware (7x WS2812
 *                   strips on pins 3-9), then re-scan Wire
 *   Stage 3 ('f'):  call FastLED.show() every loop pass (like the game's
 *                   updateCityLEDs) while polling - watch for failures
 *
 * Teensy 4.1 I2C ports:
 *   Wire  = SDA 18, SCL 19
 *   Wire1 = SDA 17, SCL 16
 *   Wire2 = SDA 25, SCL 24
 *
 * SERIAL COMMANDS (115200 baud):
 *   0 / 1 / 2 : select active bus (Wire / Wire1 / Wire2)
 *   s         : scan active bus (0x01-0x7E) with error codes
 *   S         : scan ALL three buses
 *   p         : poll the 10 expected M0 addresses (request 14 bytes, dump packet)
 *   w         : write a game-state byte (READY_IDLE = 1) to each M0, show ACK/NACK
 *   l         : check SDA/SCL idle levels on all buses (lines must idle HIGH)
 *   a         : toggle auto-poll every 2 seconds
 *   f         : toggle continuous FastLED.show() (replicates game loop load)
 *   h         : reprint this menu
 */

#include <Arduino.h>
#include <Wire.h>
#include <FastLED.h>

// Same LED setup as the game firmware (main.cpp)
#define NUM_LEDS_PER_STRIP 35
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
CRGB leds1[NUM_LEDS_PER_STRIP];
CRGB leds2[NUM_LEDS_PER_STRIP];
CRGB leds3[NUM_LEDS_PER_STRIP];
CRGB leds4[NUM_LEDS_PER_STRIP];
CRGB leds5[NUM_LEDS_PER_STRIP];
CRGB leds6[NUM_LEDS_PER_STRIP];
CRGB leds7[NUM_LEDS_PER_STRIP];
bool continuousShow = false;

#define NUM_M0_BOARDS 10
uint8_t m0Addresses[NUM_M0_BOARDS] = {0x08, 0x0C, 0x09, 0x0B, 0x0A, 0x0D, 0x10, 0x0E, 0x0F, 0x11};

#define I2C_CLOCK_HZ 100000
#define PACKET_SIZE 14

struct BusInfo {
  TwoWire* wire;
  const char* name;
  uint8_t sdaPin;
  uint8_t sclPin;
};

BusInfo buses[3] = {
  { &Wire,  "Wire  (SDA=18, SCL=19)", 18, 19 },
  { &Wire1, "Wire1 (SDA=17, SCL=16)", 17, 16 },
  { &Wire2, "Wire2 (SDA=25, SCL=24)", 25, 24 },
};

uint8_t activeBus = 0;
bool autoPoll = false;
uint32_t lastAutoPoll = 0;

const char* errorName(uint8_t error) {
  switch (error) {
    case 0: return "OK";
    case 1: return "DATA TOO LONG";
    case 2: return "ADDR NACK (no device ACKed this address)";
    case 3: return "DATA NACK (device ACKed address, rejected data)";
    case 4: return "OTHER/BUS ERROR (arbitration lost or stuck line?)";
    case 5: return "TIMEOUT (line held low?)";
    default: return "UNKNOWN";
  }
}

void printMenu() {
  Serial.println();
  Serial.println("=== TEENSY 4.1 I2C DIAGNOSTIC ===");
  Serial.print("Active bus: ");
  Serial.println(buses[activeBus].name);
  Serial.println("  0/1/2 = select bus   s = scan active bus   S = scan all buses");
  Serial.println("  p = poll M0s (14-byte packet)   w = write state byte to M0s");
  Serial.println("  l = check line idle levels      a = toggle auto-poll   h = menu");
  Serial.println("  f = toggle continuous FastLED.show() (game-loop load test)");
  Serial.println();
}

// Lines must idle HIGH (pull-ups). A LOW idle line = missing pull-ups,
// wrong wiring, or a slave holding the bus.
void checkLineLevels() {
  Serial.println("\n--- Line idle levels (I2C released, reading as GPIO) ---");
  for (uint8_t b = 0; b < 3; b++) {
    buses[b].wire->end();
    pinMode(buses[b].sdaPin, INPUT);
    pinMode(buses[b].sclPin, INPUT);
    delayMicroseconds(50);
    int sda = digitalRead(buses[b].sdaPin);
    int scl = digitalRead(buses[b].sclPin);

    Serial.print(buses[b].name);
    Serial.print("  SDA=");
    Serial.print(sda ? "HIGH" : "LOW ");
    Serial.print("  SCL=");
    Serial.print(scl ? "HIGH" : "LOW ");
    if (sda && scl) {
      Serial.println("  -> looks like a live bus (pull-ups present)");
    } else {
      Serial.println("  -> NOT idle-high: no pull-ups / not wired / bus held low");
    }

    buses[b].wire->begin();
    buses[b].wire->setClock(I2C_CLOCK_HZ);
  }
  Serial.println();
}

void scanBus(uint8_t b) {
  TwoWire* w = buses[b].wire;
  uint8_t found = 0;

  Serial.print("\n--- Scanning ");
  Serial.print(buses[b].name);
  Serial.println(" ---");

  for (uint8_t address = 1; address < 127; address++) {
    w->beginTransmission(address);
    uint8_t error = w->endTransmission();

    if (error == 0) {
      Serial.print("  FOUND 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
        if (m0Addresses[i] == address) {
          Serial.print("  <- expected M0#");
          Serial.print(i + 1);
          break;
        }
      }
      Serial.println();
      found++;
    } else if (error != 2) {
      // Address NACK (2) is normal for an empty address; anything else
      // is a bus-level problem worth seeing.
      Serial.print("  0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.print("  error ");
      Serial.print(error);
      Serial.print(": ");
      Serial.println(errorName(error));
    }
  }

  Serial.print("  Devices found: ");
  Serial.print(found);
  Serial.print(" (expecting ");
  Serial.print(NUM_M0_BOARDS);
  Serial.println(" M0 boards on the correct bus)");
}

void pollM0s() {
  TwoWire* w = buses[activeBus].wire;

  Serial.print("\n--- Polling M0s on ");
  Serial.print(buses[activeBus].name);
  Serial.println(" ---");

  uint8_t responding = 0;
  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    Serial.print("  M0#");
    Serial.print(i + 1);
    if (i < 9) Serial.print(" ");
    Serial.print(" [0x");
    Serial.print(m0Addresses[i], HEX);
    Serial.print("]: ");

    uint8_t bytesReceived = w->requestFrom(m0Addresses[i], (uint8_t)PACKET_SIZE);

    if (bytesReceived == 0) {
      Serial.println("NO RESPONSE (address NACK)");
      continue;
    }

    responding++;
    Serial.print(bytesReceived);
    Serial.print("/");
    Serial.print(PACKET_SIZE);
    Serial.print(" bytes:");

    uint8_t packet[PACKET_SIZE] = {0};
    for (uint8_t j = 0; j < bytesReceived && j < PACKET_SIZE; j++) {
      packet[j] = w->read();
      Serial.print(" ");
      if (packet[j] < 16) Serial.print("0");
      Serial.print(packet[j], HEX);
    }
    Serial.println();

    if (bytesReceived == PACKET_SIZE) {
      uint16_t raw1 = (packet[8] << 8) | packet[9];
      uint16_t raw2 = (packet[10] << 8) | packet[11];
      uint16_t raw3 = (packet[12] << 8) | packet[13];
      Serial.print("        detect=");
      Serial.print(packet[0]);
      Serial.print(" pol=[");
      Serial.print(packet[1]);
      Serial.print(",");
      Serial.print(packet[2]);
      Serial.print(",");
      Serial.print(packet[3]);
      Serial.print("] addrEcho=0x");
      Serial.print(packet[4], HEX);
      Serial.print(" gameState=");
      Serial.print(packet[5]);
      Serial.print(" reg=");
      Serial.print(packet[6]);
      Serial.print(" corr=");
      Serial.print(packet[7]);
      Serial.print(" raw=[");
      Serial.print(raw1);
      Serial.print(",");
      Serial.print(raw2);
      Serial.print(",");
      Serial.print(raw3);
      Serial.println("]");
      if (packet[4] != m0Addresses[i]) {
        Serial.println("        ^ WARNING: address echo does not match - check M0 firmware/addressing");
      }
    }
  }

  Serial.print("  Responding: ");
  Serial.print(responding);
  Serial.print("/");
  Serial.println(NUM_M0_BOARDS);
}

void writeStateToM0s() {
  TwoWire* w = buses[activeBus].wire;
  const uint8_t testState = 1;  // GAME_READY_IDLE

  Serial.print("\n--- Writing state byte ");
  Serial.print(testState);
  Serial.print(" to M0s on ");
  Serial.print(buses[activeBus].name);
  Serial.println(" ---");

  for (uint8_t i = 0; i < NUM_M0_BOARDS; i++) {
    w->beginTransmission(m0Addresses[i]);
    w->write(testState);
    uint8_t error = w->endTransmission();

    Serial.print("  M0#");
    Serial.print(i + 1);
    if (i < 9) Serial.print(" ");
    Serial.print(" [0x");
    Serial.print(m0Addresses[i], HEX);
    Serial.print("]: error ");
    Serial.print(error);
    Serial.print(" - ");
    Serial.println(errorName(error));
  }
}

void setup() {
  Serial.begin(115200);
  uint32_t start = millis();
  while (!Serial && millis() - start < 3000) {}  // wait up to 3s for monitor

  Serial.println("\nBooting I2C diagnostic...");

  // Check idle levels BEFORE claiming the pins for I2C
  for (uint8_t b = 0; b < 3; b++) {
    pinMode(buses[b].sdaPin, INPUT);
    pinMode(buses[b].sclPin, INPUT);
  }
  delay(10);
  Serial.println("\n--- Pre-init line levels ---");
  for (uint8_t b = 0; b < 3; b++) {
    Serial.print(buses[b].name);
    Serial.print("  SDA=");
    Serial.print(digitalRead(buses[b].sdaPin) ? "HIGH" : "LOW ");
    Serial.print("  SCL=");
    Serial.println(digitalRead(buses[b].sclPin) ? "HIGH" : "LOW");
  }

  for (uint8_t b = 0; b < 3; b++) {
    buses[b].wire->begin();
    buses[b].wire->setClock(I2C_CLOCK_HZ);
  }

  delay(500);  // let M0s settle

  // Initial full sweep
  for (uint8_t b = 0; b < 3; b++) {
    scanBus(b);
  }

  printMenu();
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case '0':
      case '1':
      case '2':
        activeBus = cmd - '0';
        Serial.print("\nActive bus: ");
        Serial.println(buses[activeBus].name);
        break;
      case 's': scanBus(activeBus); break;
      case 'S': for (uint8_t b = 0; b < 3; b++) scanBus(b); break;
      case 'p':
      case 'P': pollM0s(); break;
      case 'w':
      case 'W': writeStateToM0s(); break;
      case 'l':
      case 'L': checkLineLevels(); break;
      case 'a':
      case 'A':
        autoPoll = !autoPoll;
        Serial.print("\nAuto-poll ");
        Serial.println(autoPoll ? "ON (every 2s)" : "OFF");
        break;
      case 'h':
      case 'H': printMenu(); break;
      default: break;  // ignore newlines etc.
    }
  }

  if (autoPoll && millis() - lastAutoPoll >= 2000) {
    pollM0s();
    lastAutoPoll = millis();
  }
}
