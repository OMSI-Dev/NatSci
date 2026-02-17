/*
 * Calico Randall
 * How Fast header file for controlling TOFs
 * TOFs used are the DF Robot SEN0647
 * February 2026
 */

#include <Arduino.h>

#define TOTAL_TOFS 10

typedef struct
{
  unsigned char id;              // ID of the TOF module
  unsigned long system_time;     // Time elapsed since the TOF module was powered on, in ms
  float dis;                     // Distance output by the TOF module, in meters
  unsigned char dis_status;      // Distance status indication output by the TOF module
  unsigned int signal_strength;  // Signal strength output by the TOF module
  unsigned char range_precision; // Reference value of repeat ranging accuracy output by the TOF module, valid for TOFSense-F series, in cm
} tof_parameter;                 // Decoded TOF data structure

/**
  @brief  Read data in the serial port
  @param  buf Storage for the read data
  @param  len Number of bytes to read
  @return  The return value is the number of bytes actually read
*/
size_t readN(uint8_t *buf, size_t len);

/**
  @brief  Read a complete data packet
  @param  buf Storage for the read data
  @param  id Module ID
  @return  True means success, false means failure
*/
bool recdData(tof_parameter *buf, uint8_t id = 0);

tof_parameter tof0; // Define a structure to store the decoded data
tof_parameter tofs[TOTAL_TOFS];

void setupTOFSerial()
{
  // Defaults to SERIAL_8N1 if not defined explicitly.
  // Baud rate 921600 for fast transmission.
  // All TOFs should have the same baud rate.
  Serial1.begin(921600); // RX,TX
  // mySerial.begin(921600);  //RX,TX
}

size_t readN(uint8_t *buf, size_t len)
{
  size_t offset = 0, left = len;
  int16_t Timeout = 250;
  uint8_t *buffer = buf;
  long curr = millis();
  while (left)
  {
    if (Serial1.available())
    {
      buffer[offset] = Serial1.read();
      offset++;
      left--;
    }
    if (millis() - curr > Timeout)
    {
      break;
    }
  }
  return offset;
}

bool recdData(tof_parameter *buf, uint8_t id)
{
  uint8_t rx_buf[16]; // Serial receive array
  int16_t Timeout = 1000;
  uint8_t ch;
  bool ret = false;
  uint8_t Sum;
  uint8_t cmdBuf[8] = {0x57, 0x10, 0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0x00};
  cmdBuf[4] = id;
  cmdBuf[7] = 0;
  for (int i = 0; i < 7; i++)
    cmdBuf[7] += cmdBuf[i];
  long timeStart = millis();
  long timeStart1 = 0;

  while (!ret)
  {
    if (millis() - timeStart > Timeout)
    {
      break;
    }

    if ((millis() - timeStart1) > 1000)
    {
      while (Serial1.available() > 0)
      {
        Serial1.read();
      }
      Serial1.write(cmdBuf, 8);
      timeStart1 = millis();
    }

    if (readN(&ch, 1) == 1)
    {
      if (ch == 0x57)
      {
        rx_buf[0] = ch;
        if (readN(&ch, 1) == 1)
        {
          if (ch == 0x00)
          {
            rx_buf[1] = ch;
            if (readN(&rx_buf[2], 14) == 14)
            {
              Sum = 0;
              for (int i = 0; i < 15; i++)
                Sum += rx_buf[i];
              if (Sum == rx_buf[15])
              {
                buf->id = rx_buf[3];                                                                                                                                                  // Take the id of the TOF module
                buf->system_time = (unsigned long)(((unsigned long)rx_buf[7]) << 24 | ((unsigned long)rx_buf[6]) << 16 | ((unsigned long)rx_buf[5]) << 8 | (unsigned long)rx_buf[4]); // Take the time elapsed since the TOF module was powered on
                buf->dis = ((float)(((long)(((unsigned long)rx_buf[10] << 24) | ((unsigned long)rx_buf[9] << 16) | ((unsigned long)rx_buf[8] << 8))) / 256)) / 1000.0;                // Take the distance output by the TOF module
                buf->dis_status = rx_buf[11];                                                                                                                                         // Take the distance status indication output by the TOF module
                buf->signal_strength = (unsigned int)(((unsigned int)rx_buf[13] << 8) | (unsigned int)rx_buf[12]);                                                                    // Take the signal strength output by the TOF module
                buf->range_precision = rx_buf[14];                                                                                                                                    // Take the reference value of repeat ranging accuracy output by the TOF module
                ret = true;
              }
            }
          }
        }
      }
    }
  }
  return ret;
}

void readTOFData()
{
  recdData(&tof0, 0);

  // for (uint8_t i = 0; i < TOTAL_TOFS; i++)
  //{
  //   recdData(&tofs[i], i);
  // }
}

void printTOFDistance()
{
  Serial.print("Distance:");
  Serial.println(tof0.dis);

  // Print all TOF distances
  /*for (uint8_t i = 0; i < TOTAL_TOFS; i++)
  {
    Serial.print("Distance of TOF ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(tofs[i].dis);
  }*/
}

float getSpecificTOFDis(uint8_t tofNum)
{
  // For array of TOFs, return the distance of a specific one.
  // if(tofNum > TOTAL_TOFS || tofNum < 0) {
  //      Serial.println("Requested distance for a TOF that does not exist.");
  //      return 0.0;
  //}
  // return tofs[tofNum].dis;
}

// Print data through the serial port
void printTOFInfo()
{
  Serial.print("id:");
  Serial.println(tof0.id);
  Serial.print("system_time:");
  Serial.println(tof0.system_time);
  Serial.print("Distance:");
  Serial.println(tof0.dis);
  Serial.print("dis_status:");
  Serial.println(tof0.dis_status);
  Serial.print("signal_strength:");
  Serial.println(tof0.signal_strength);
  Serial.print("range_precision:");
  Serial.println(tof0.range_precision);
  Serial.println("");
}

// Print data through the serial port
void printSpecificTOFInfo(uint8_t tofNum)
{
  Serial.print("**** INFO FOR TOF ");
  Serial.print(tofNum);
  Serial.println(" ****");
  Serial.print("id:");
  Serial.println(tofs[tofNum].id);
  Serial.print("system_time:");
  Serial.println(tofs[tofNum].system_time);
  Serial.print("Distance:");
  Serial.println(tofs[tofNum].dis);
  Serial.print("dis_status:");
  Serial.println(tofs[tofNum].dis_status);
  Serial.print("signal_strength:");
  Serial.println(tofs[tofNum].signal_strength);
  Serial.print("range_precision:");
  Serial.println(tofs[tofNum].range_precision);
  Serial.println("");
}

// If a TOF is triggered, return that TOF number
// Can be called in main loop?
uint8_t tofTriggered()
{
  for (uint8_t i = 0; i < TOTAL_TOFS; i++)
  {
    if (tofs[i].dis < 4.0)
    {
      Serial.print("ToF #");
      Serial.print(i);
      Serial.println(" triggered.");
      return i;
    }
  }

  // If goes through the loop and none of the TOFs have been triggered.
  return -1;
}