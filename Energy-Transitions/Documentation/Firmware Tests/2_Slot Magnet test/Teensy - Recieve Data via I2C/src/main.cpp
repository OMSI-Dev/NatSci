/*
 * TEST 2 - TEENSY BOARD - POLARITY DETECTION MONITOR
 *
 * Polls M0 boards at 0x08 and 0x09 every 250 ms via I2C.
 * Receives the 6-byte status packet and prints human-readable output.
 *
 * Packet format from M0:
 *   [0] state   0=IDLE  1=REGISTERING  2=CORRECT  3=INCORRECT
 *   [1] S1 pol  0=UNCERTAIN  1=SOUTH  2=NORTH
 *   [2] S2 pol
 *   [3] S3 pol
 *   [4] M0 I2C address low byte
 *   [5] reserved
 */

#include <Arduino.h>
#include <Wire.h>

const uint8_t M0_ADDRESSES[] = { 0x08, 0x09 };
const uint8_t NUM_M0         = sizeof(M0_ADDRESSES);

unsigned long lastPoll = 0;
const unsigned long POLL_INTERVAL = 250;

const char* STATE_NAMES[] = { "IDLE       ", "REGISTERING", "CORRECT    ", "INCORRECT  " };

char polChar(uint8_t p) {
  switch (p) {
    case 1:  return 'S';
    case 2:  return 'N';
    default: return '?';
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);

  Serial.println(F("\n========================================"));
  Serial.println(F("  TEST 2 - POLARITY DETECTION (TEENSY)"));
  Serial.println(F("========================================"));
  Serial.println(F("Polling 0x08 (Buoy) and 0x09 (Dam)."));
  Serial.println(F("S=SOUTH  N=NORTH  ?=UNCERTAIN/no magnet"));
  Serial.println(F("----------------------------------------"));
  Serial.println(F("[addr]  [state      ]  [S1 S2 S3]  result"));
  Serial.println(F("----------------------------------------"));

  Wire.begin();
  Wire.setClock(100000);

  delay(500);
}

void pollM0(uint8_t addr) {
  // Check device is present
  Wire.beginTransmission(addr);
  if (Wire.endTransmission() != 0) return;  // absent — skip silently

  uint8_t received = Wire.requestFrom(addr, (uint8_t)6);
  if (received < 6) return;  // short read — skip

  uint8_t buf[6];
  for (uint8_t i = 0; i < 6; i++) buf[i] = Wire.read();

  uint8_t state = buf[0];
  uint8_t p1    = buf[1];
  uint8_t p2    = buf[2];
  uint8_t p3    = buf[3];
  // buf[4] = address echo, buf[5] = reserved

  // Address prefix
  Serial.print(F("[0x"));
  if (addr < 0x10) Serial.print('0');
  Serial.print(addr, HEX);
  Serial.print(F("]  "));

  // State
  if (state < 4) Serial.print(STATE_NAMES[state]);
  else           Serial.print(F("?          "));

  // Per-sensor polarity
  Serial.print(F("  ["));
  Serial.print(polChar(p1));
  Serial.print(polChar(p2));
  Serial.print(polChar(p3));
  Serial.print(F("]"));

  // Result packet
  if (state == 2) {
    if      (addr == 0x08) Serial.print(F("  → 1,Buoy"));
    else if (addr == 0x09) Serial.print(F("  → 1,Dam"));
  } else if (state == 3) {
    Serial.print(F("  → 0,"));
    Serial.print(polChar(p1));
    Serial.print(polChar(p2));
    Serial.print(polChar(p3));
  }

  Serial.println();
}

void loop() {
  if (millis() - lastPoll >= POLL_INTERVAL) {
    lastPoll = millis();
    for (uint8_t i = 0; i < NUM_M0; i++) pollM0(M0_ADDRESSES[i]);
  }

  delay(10);
}
