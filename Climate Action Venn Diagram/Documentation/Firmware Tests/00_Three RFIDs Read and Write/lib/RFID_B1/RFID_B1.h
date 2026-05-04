#ifndef RFID_B1_H
#define RFID_B1_H

#include <Arduino.h>

// UART Commands
#define CMD_DUMMY                   0x00
#define CMD_WRITE_RFID_MEMORY       0x01
#define CMD_READ_RFID_MEMORY        0x02
#define CMD_ENTER_SLEEP             0x03
#define CMD_RESET                   0x04
#define CMD_SET_BAUD_RATE           0x05
#define CMD_SET_DATA_TYPE           0x06
#define CMD_SET_HEADER_TYPE         0x07

// RFID Commands
#define RFID_CMD_GET_UID_TYPE       0x01
#define RFID_CMD_READ_BLOCK         0x02
#define RFID_CMD_WRITE_BLOCK        0x03
#define RFID_CMD_READ_DATA_BLOCK    0x04
#define RFID_CMD_WRITE_DATA_BLOCK   0x05
#define RFID_CMD_READ_PAGE          0x06
#define RFID_CMD_WRITE_PAGE         0x07
#define RFID_CMD_ENCRYPT_DATA       0x08
#define RFID_CMD_DECRYPT_DATA       0x09
#define RFID_CMD_PASSWORD_AUTH      0x17
#define RFID_CMD_HALT               0x18
#define RFID_CMD_SELECT_TAG         0x21

// Memory Addresses
#define ADDR_RESULT_REG             0x0000
#define ADDR_COMMAND_REG            0x0001
#define ADDR_COMMAND_PARAMS         0x0002
#define ADDR_TAG_UID                0x0014
#define ADDR_TAG_TYPE               0x001E
#define ADDR_TAG_UID_SIZE           0x001F
#define ADDR_DATA_BUFFER            0x0020

// Response Packet Types
#define RESP_ACK                    0x00
#define RESP_INVALID_COMMAND        0x01
#define RESP_INVALID_PARAM          0x02
#define RESP_PROTOCOL_ERROR         0x03
#define RESP_MEMORY_ERROR           0x04
#define RESP_SYSTEM_ERROR           0x05
#define RESP_MODULE_TIMEOUT         0x06
#define RESP_OVERFLOW               0x07
#define RESP_ASYNC_PACKET           0x08
#define RESP_BUSY                   0x09
#define RESP_SYSTEM_START           0x0A

// Result Register Values
#define RESULT_NO_ERROR             0x00
#define RESULT_INVALID_CMD          0x01
#define RESULT_INVALID_PARAM        0x02
#define RESULT_INDEX_OUT_RANGE      0x03
#define RESULT_NV_WRITE_ERROR       0x04
#define RESULT_SYSTEM_ERROR         0x05
#define RESULT_TAG_CRC_ERROR        0x06
#define RESULT_TAG_COLLISION        0x07
#define RESULT_NO_TAG               0x08
#define RESULT_AUTH_ERROR           0x09
#define RESULT_VALUE_CORRUPTED      0x0A
#define RESULT_OVERHEATED           0x0B
#define RESULT_TAG_NOT_SUPPORTED    0x0C
#define RESULT_TAG_COMM_ERROR       0x0D
#define RESULT_INVALID_PASSWORD     0x0E
#define RESULT_ALREADY_LOCKED       0x0F
#define RESULT_MODULE_BUSY          0xFF

// Tag Types
#define TAG_NO_TAG                  0x00
#define TAG_INCOMPLETE              0x01
#define TAG_ULTRALIGHT              0x02
#define TAG_ULTRALIGHT_EV1_80B      0x03
#define TAG_ULTRALIGHT_EV1_164B     0x04
#define TAG_CLASSIC_MINI            0x05
#define TAG_CLASSIC_1K              0x06
#define TAG_CLASSIC_4K              0x07
#define TAG_NTAG203F                0x08
#define TAG_NTAG210                 0x09
#define TAG_NTAG212                 0x0A
#define TAG_NTAG213F                0x0B
#define TAG_NTAG216F                0x0C
#define TAG_NTAG213                 0x0D
#define TAG_NTAG215                 0x0E
#define TAG_NTAG216                 0x0F
#define TAG_UNKNOWN                 0x10

// NTAG215 Specifications
#define NTAG215_PAGES               135
#define NTAG215_PAGE_SIZE           4
#define NTAG215_USER_START_PAGE     4
#define NTAG215_USER_END_PAGE       129
#define NTAG215_TOTAL_BYTES         540

class RFID_B1 {
public:
    RFID_B1(HardwareSerial &serial);
    
    // Initialization
    void begin(unsigned long baudRate = 9600);
    void reset();
    bool waitForReady(unsigned long timeout = 2000);
    
    // Basic UART Commands
    bool dummyCommand();
    bool writeRFIDMemory(uint16_t address, const uint8_t* data, uint16_t size);
    bool readRFIDMemory(uint16_t address, uint8_t* data, uint16_t size);
    
    // RFID Tag Operations
    bool getUIDandType();
    bool readPage(uint8_t pageAddress, uint8_t numPages, uint8_t bufferOffset = 0);
    bool writePage(uint8_t pageAddress, const uint8_t* data, uint8_t numPages, uint8_t bufferOffset = 0);
    bool passwordAuthentication(uint8_t passwordNumber, const uint8_t* password);
    bool halt();
    
    // Data Buffer Operations
    bool writeDataBuffer(uint16_t offset, const uint8_t* data, uint16_t size);
    bool readDataBuffer(uint16_t offset, uint8_t* data, uint16_t size);
    
    // Tag Information
    bool getTagUID(uint8_t* uid, uint8_t &uidSize);
    uint8_t getTagType();
    uint8_t getLastResult();
    
    // High-level NTAG215 functions
    bool readNTAG215(uint8_t startPage, uint8_t numPages, uint8_t* data);
    bool writeNTAG215(uint8_t startPage, const uint8_t* data, uint8_t numPages);
    bool readNTAG215User(uint8_t* data, uint16_t &dataSize);
    bool writeNTAG215User(const uint8_t* data, uint16_t dataSize);
    
    // Utility
    const char* getTagTypeName(uint8_t tagType);
    const char* getResultName(uint8_t result);
    void printUID(uint8_t* uid, uint8_t size);
    void printBuffer(uint8_t* data, uint16_t size);

private:
    HardwareSerial *_serial;
    uint8_t _lastResult;
    uint8_t _tagType;
    uint8_t _tagUID[10];
    uint8_t _tagUIDSize;
    
    // Packet handling
    bool sendCommand(uint8_t cmd, const uint8_t* params, uint8_t paramSize);
    bool receiveResponse(uint8_t* buffer, uint16_t &size, uint16_t maxSize, unsigned long timeout = 1000);
    uint16_t calculateCRC(const uint8_t* data, uint16_t size);
    bool sendPacket(const uint8_t* data, uint16_t dataSize);
    bool receivePacket(uint8_t* data, uint16_t &dataSize, uint16_t maxSize, unsigned long timeout);
    
    // Helper functions
    bool executeRFIDCommand(uint8_t rfidCmd, const uint8_t* params, uint8_t paramSize);
    bool waitForAsyncPacket(unsigned long timeout = 2000);
    void clearSerialBuffer();
};

#endif // RFID_B1_H
