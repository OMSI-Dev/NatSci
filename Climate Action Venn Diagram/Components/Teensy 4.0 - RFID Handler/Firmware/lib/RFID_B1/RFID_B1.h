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
#define RFID_CMD_UNLOCK             0x1B
#define RFID_CMD_LOCK               0x1C
#define RFID_CMD_SELECT_TAG         0x21
#define RFID_CMD_POLLING            0x22

// Memory Addresses
#define ADDR_RESULT_REG             0x0000
#define ADDR_COMMAND_REG            0x0001
#define ADDR_COMMAND_PARAMS         0x0002
#define ADDR_TAG_UID                0x0014
#define ADDR_TAG_TYPE               0x001E
#define ADDR_TAG_UID_SIZE           0x001F
#define ADDR_DATA_BUFFER            0x0020
#define ADDR_PASSWORD                0x0120
#define ADDR_USER_MEMORY             0x0258
// Defined Tag List lives in User Memory starting at byte index 19
// (see manual 5.5.6): <UIDSize><UID>...<UIDSize><UID>
#define ADDR_DEFINED_TAG_LIST        (ADDR_USER_MEMORY + 19)
#define USER_MEMORY_SIZE             128

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

// ---------------------------------------------------------------------
// Polling (0x22) - see manual chapter 5.4.34 / 5.5
// ---------------------------------------------------------------------

// "Asynchronous Packet Mode" - how a detected UID is reported over UART
#define POLL_PKT_NONE                0x00  // do not send any packet
#define POLL_PKT_ASYNC                0x01  // send Async Packet (chapter 5.6)
#define POLL_PKT_BINARY                0x02  // <UIDSize><UID> raw binary
#define POLL_PKT_STRING                0x03  // <UIDSize><UID><\r\n> ASCII

// PWM channel used for tag-presence signalling. Any value > 2 = "do not use PWM".
#define POLL_PWM_IO0                  0x00
#define POLL_PWM_IO1                  0x01
#define POLL_PWM_IO2                  0x02
#define POLL_PWM_NONE                 0x03

// Allowed UID sizes for the Defined Tag List (manual 5.5.6)
#define TAG_UID_SIZE_4               4
#define TAG_UID_SIZE_7               7
#define TAG_UID_SIZE_10              10

// Builds the "IO Config" byte for a Polling Defined/Undefined Tag block.
// Bits 4-7 = which IOx to drive on tag presence, bits 0-3 = the state to
// drive it to (1 = high) when its enable bit is set. See manual Table 5.4.34.3.
#define POLL_IO_CONFIG(io0En, io0State, io1En, io1State, io2En, io2State, io3En, io3State) \
    (uint8_t)( (((io3En)&1)<<7) | (((io2En)&1)<<6) | (((io1En)&1)<<5) | (((io0En)&1)<<4) | \
               (((io3State)&1)<<3) | (((io2State)&1)<<2) | (((io1State)&1)<<1) | ((io0State)&1) )

#define POLL_IO_CONFIG_NONE          0x00 // do not use any IO outputs

// Behaviour applied when a Defined tag (on the list) or an Undefined tag
// (not on the list) is detected during Polling. Two of these together make
// up the full 16-byte Polling command payload after Period/NumDefinedTags.
struct PollingTagSettings {
    uint8_t  asyncPacketMode; // POLL_PKT_*
    uint8_t  ioConfig;        // build with POLL_IO_CONFIG(), or POLL_IO_CONFIG_NONE
    uint8_t  pwmChannel;      // POLL_PWM_*
    uint8_t  pwmDuty;         // 0-100 (%)
    uint32_t pwmPeriodUs;     // 5..3120761 uS (only the low 24 bits are sent); frequency = 1e6/pwmPeriodUs
    uint8_t  tagTimeout;      // delay in x100ms before polling resumes after this detection

    PollingTagSettings()
        : asyncPacketMode(POLL_PKT_NONE), ioConfig(POLL_IO_CONFIG_NONE),
          pwmChannel(POLL_PWM_NONE), pwmDuty(0), pwmPeriodUs(0), tagTimeout(1) {}
};

// Full parameter set for the Polling (0x22) command.
struct PollingConfig {
    uint8_t period;             // polling interval in x100ms (e.g. 1 = 100ms)
    uint8_t numDefinedTags;     // number of tags in the Defined Tag List (0 = list unused)
    PollingTagSettings definedTag;   // behaviour when a listed tag is seen
    PollingTagSettings undefinedTag; // behaviour when an unlisted tag is seen

    PollingConfig() : period(1), numDefinedTags(0) {}
};

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

    // Polling Mode (0x22) - stand-alone continuous tag detection
    bool startPolling(const PollingConfig &config);
    bool stopPolling(); // stops polling by issuing a Halt command
    // Convenience wrapper: starts Polling with everything (IO, PWM, packet
    // reporting) disabled, purely so the module keeps the TPI pin (pin 17)
    // updated in the background. Wire TPI to a GPIO and digitalRead() it -
    // no UART traffic needed per check. Call getUIDandType() only once you
    // actually want to read the tag (stopPolling() first, per manual 5.5.7).
    bool startPresenceWatch(uint8_t periodX100ms = 1);
    // Reads one raw packet sent by the module while Polling is active.
    // Interpretation of `data` depends on the asyncPacketMode configured:
    //   POLL_PKT_ASYNC  - Asynchronous Packet, format in manual chapter 5.6
    //   POLL_PKT_BINARY - <UIDSize><UID> raw bytes
    //   POLL_PKT_STRING - <UIDSize><UID> as ASCII text, ends with \r\n
    // Returns true and sets size if a packet arrived before timeout.
    bool pollForPacket(uint8_t* data, uint8_t &size, unsigned long timeout = 0);

    // Memory locking (needed to write the Defined Tag List / User Memory)
    bool unlock(const uint8_t* password); // 8-byte password
    bool lock();

    // Writes the Defined Tag List into User Memory (index 19 onward).
    // Call unlock() first and lock() afterward to persist it, per manual 5.5.6.
    // uidSizes[i] must be 4, 7, or 10. numTags must match PollingConfig::numDefinedTags.
    bool setDefinedTagList(const uint8_t uidSizes[], const uint8_t* const uids[], uint8_t numTags);
    
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
