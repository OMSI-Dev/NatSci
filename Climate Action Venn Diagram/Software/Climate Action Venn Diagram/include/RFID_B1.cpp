#include "RFID_B1.h"

// CRC-CCITT Lookup Table
static const uint16_t CCITTCRCTable[256] = {
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
};

RFID_B1::RFID_B1(HardwareSerial &serial) : _serial(&serial) {
    _lastResult = RESULT_NO_ERROR;
    _tagType = TAG_NO_TAG;
    _tagUIDSize = 0;
    memset(_tagUID, 0, sizeof(_tagUID));
}

void RFID_B1::begin(unsigned long baudRate) {
    _serial->begin(baudRate);
    delay(100); // Allow module to stabilize
}

void RFID_B1::reset() {
    sendCommand(CMD_RESET, nullptr, 0);
    delay(200); // Wait for module to reset
}

bool RFID_B1::waitForReady(unsigned long timeout) {
    unsigned long startTime = millis();
    uint8_t buffer[32];
    uint16_t size;
    
    while (millis() - startTime < timeout) {
        if (receiveResponse(buffer, size, sizeof(buffer), 100)) {
            if (size > 0 && buffer[0] == RESP_SYSTEM_START) {
                return true;
            }
        }
    }
    return false;
}

uint16_t RFID_B1::calculateCRC(const uint8_t* data, uint16_t size) {
    uint16_t crc = 0xFFFF;
    
    for (uint16_t i = 0; i < size; i++) {
        uint16_t temp = ((crc >> 8) ^ data[i]) & 0xFF;
        crc = CCITTCRCTable[temp] ^ (crc << 8);
    }
    
    return crc;
}

bool RFID_B1::sendPacket(const uint8_t* data, uint16_t dataSize) {
    // Type A Header with Plain Data (default)
    uint8_t packet[512];
    uint16_t idx = 0;
    
    // Header: Start byte
    packet[idx++] = 0x02;
    
    // Header: Data size (LSB first)
    packet[idx++] = dataSize & 0xFF;
    packet[idx++] = (dataSize >> 8) & 0xFF;
    
    // Header: CRC of header (first 3 bytes)
    uint16_t headerCRC = calculateCRC(packet, 3);
    packet[idx++] = headerCRC & 0xFF;
    packet[idx++] = (headerCRC >> 8) & 0xFF;
    
    // Data: Copy data
    memcpy(&packet[idx], data, dataSize);
    idx += dataSize;
    
    // Send packet
    _serial->write(packet, idx);
    _serial->flush();
    
    return true;
}

bool RFID_B1::receivePacket(uint8_t* data, uint16_t &dataSize, uint16_t maxSize, unsigned long timeout) {
    unsigned long startTime = millis();
    uint8_t state = 0; // 0 = wait for STX, 1 = read size, 2 = read header CRC, 3 = read data
    uint16_t expectedSize = 0;
    uint16_t idx = 0;
    uint8_t header[5];
    uint8_t headerIdx = 0;
    
    while (millis() - startTime < timeout) {
        if (_serial->available()) {
            uint8_t b = _serial->read();
            
            switch (state) {
                case 0: // Wait for STX (0x02)
                    if (b == 0x02) {
                        header[headerIdx++] = b;
                        state = 1;
                    }
                    break;
                    
                case 1: // Read data size (2 bytes)
                    header[headerIdx++] = b;
                    if (headerIdx == 3) {
                        expectedSize = header[1] | (header[2] << 8);
                        state = 2;
                    }
                    break;
                    
                case 2: // Read header CRC (2 bytes)
                    header[headerIdx++] = b;
                    if (headerIdx == 5) {
                        // Verify header CRC
                        uint16_t receivedCRC = header[3] | (header[4] << 8);
                        uint16_t calculatedCRC = calculateCRC(header, 3);
                        if (receivedCRC != calculatedCRC) {
                            return false; // Header CRC mismatch
                        }
                        state = 3;
                        idx = 0;
                    }
                    break;
                    
                case 3: // Read data
                    if (idx < maxSize) {
                        data[idx++] = b;
                    }
                    if (idx >= expectedSize) {
                        // Verify data CRC (last 2 bytes of data)
                        if (expectedSize >= 2) {
                            uint16_t receivedCRC = data[expectedSize-2] | (data[expectedSize-1] << 8);
                            uint16_t calculatedCRC = calculateCRC(data, expectedSize - 2);
                            if (receivedCRC != calculatedCRC) {
                                return false; // Data CRC mismatch
                            }
                            dataSize = expectedSize - 2; // Exclude CRC bytes
                            return true;
                        }
                        return false;
                    }
                    break;
            }
            
            startTime = millis(); // Reset timeout on each byte received
        }
    }
    
    return false; // Timeout
}

bool RFID_B1::sendCommand(uint8_t cmd, const uint8_t* params, uint8_t paramSize) {
    uint8_t data[256];
    uint16_t idx = 0;
    
    // Command byte
    data[idx++] = cmd;
    
    // Parameters
    if (params && paramSize > 0) {
        memcpy(&data[idx], params, paramSize);
        idx += paramSize;
    }
    
    // CRC
    uint16_t crc = calculateCRC(data, idx);
    data[idx++] = crc & 0xFF;
    data[idx++] = (crc >> 8) & 0xFF;
    
    return sendPacket(data, idx);
}

bool RFID_B1::receiveResponse(uint8_t* buffer, uint16_t &size, uint16_t maxSize, unsigned long timeout) {
    if (receivePacket(buffer, size, maxSize, timeout)) {
        // First byte is response type
        if (size > 0) {
            return true;
        }
    }
    return false;
}

void RFID_B1::clearSerialBuffer() {
    while (_serial->available()) {
        _serial->read();
    }
}

bool RFID_B1::dummyCommand() {
    clearSerialBuffer();
    
    if (!sendCommand(CMD_DUMMY, nullptr, 0)) {
        return false;
    }
    
    uint8_t response[16];
    uint16_t size;
    
    if (receiveResponse(response, size, sizeof(response))) {
        return (size > 0 && response[0] == RESP_ACK);
    }
    
    return false;
}

bool RFID_B1::writeRFIDMemory(uint16_t address, const uint8_t* data, uint16_t dataSize) {
    uint8_t params[260];
    uint16_t idx = 0;
    
    // Address (LSB first)
    params[idx++] = address & 0xFF;
    params[idx++] = (address >> 8) & 0xFF;
    
    // Data size (LSB first)
    params[idx++] = dataSize & 0xFF;
    params[idx++] = (dataSize >> 8) & 0xFF;
    
    // Data
    memcpy(&params[idx], data, dataSize);
    idx += dataSize;
    
    if (!sendCommand(CMD_WRITE_RFID_MEMORY, params, idx)) {
        return false;
    }
    
    uint8_t response[16];
    uint16_t size;
    
    if (receiveResponse(response, size, sizeof(response))) {
        return (size > 0 && response[0] == RESP_ACK);
    }
    
    return false;
}

bool RFID_B1::readRFIDMemory(uint16_t address, uint8_t* data, uint16_t dataSize) {
    uint8_t params[4];
    
    // Address (LSB first)
    params[0] = address & 0xFF;
    params[1] = (address >> 8) & 0xFF;
    
    // Data size (LSB first)
    params[2] = dataSize & 0xFF;
    params[3] = (dataSize >> 8) & 0xFF;
    
    if (!sendCommand(CMD_READ_RFID_MEMORY, params, 4)) {
        return false;
    }
    
    uint8_t response[300];
    uint16_t size;
    
    if (receiveResponse(response, size, sizeof(response))) {
        if (size > 1 && response[0] == RESP_ACK) {
            // Data starts after ACK byte
            uint16_t copySize = min((int)dataSize, (int)(size - 1));
            memcpy(data, &response[1], copySize);
            return true;
        }
    }
    
    return false;
}

bool RFID_B1::executeRFIDCommand(uint8_t rfidCmd, const uint8_t* params, uint8_t paramSize) {
    // Write command parameters
    if (params && paramSize > 0) {
        if (!writeRFIDMemory(ADDR_COMMAND_PARAMS, params, paramSize)) {
            return false;
        }
        delay(10); // Small delay between writes
    }
    
    // Write command to command register
    if (!writeRFIDMemory(ADDR_COMMAND_REG, &rfidCmd, 1)) {
        return false;
    }
    
    // Wait for async packet indicating command completion
    return waitForAsyncPacket();
}

bool RFID_B1::waitForAsyncPacket(unsigned long timeout) {
    unsigned long startTime = millis();
    uint8_t response[16];
    uint16_t size;
    
    while (millis() - startTime < timeout) {
        if (receiveResponse(response, size, sizeof(response), 100)) {
            if (size > 0 && response[0] == RESP_ASYNC_PACKET) {
                // Read result register to check for errors
                delay(10);
                readRFIDMemory(ADDR_RESULT_REG, &_lastResult, 1);
                return (_lastResult == RESULT_NO_ERROR);
            }
        }
    }
    
    return false;
}

bool RFID_B1::getUIDandType() {
    if (!executeRFIDCommand(RFID_CMD_GET_UID_TYPE, nullptr, 0)) {
        return false;
    }
    
    // Read tag type
    if (!readRFIDMemory(ADDR_TAG_TYPE, &_tagType, 1)) {
        return false;
    }
    
    // Read UID size
    if (!readRFIDMemory(ADDR_TAG_UID_SIZE, &_tagUIDSize, 1)) {
        return false;
    }
    
    // Read UID
    if (_tagUIDSize > 0 && _tagUIDSize <= 10) {
        if (!readRFIDMemory(ADDR_TAG_UID, _tagUID, _tagUIDSize)) {
            return false;
        }
    }
    
    return (_tagType != TAG_NO_TAG);
}

bool RFID_B1::readPage(uint8_t pageAddress, uint8_t numPages, uint8_t bufferOffset) {
    uint8_t params[3];
    params[0] = pageAddress;  // Absolute page number
    params[1] = numPages;     // Number of pages to read
    params[2] = bufferOffset; // Data buffer offset
    
    return executeRFIDCommand(RFID_CMD_READ_PAGE, params, 3);
}

bool RFID_B1::writePage(uint8_t pageAddress, const uint8_t* data, uint8_t numPages, uint8_t bufferOffset) {
    // First write data to buffer
    if (!writeDataBuffer(bufferOffset, data, numPages * 4)) {
        return false;
    }
    
    // Then execute write page command
    uint8_t params[3];
    params[0] = pageAddress;  // Absolute page number
    params[1] = numPages;     // Number of pages to write
    params[2] = bufferOffset; // Data buffer offset
    
    return executeRFIDCommand(RFID_CMD_WRITE_PAGE, params, 3);
}

bool RFID_B1::passwordAuthentication(uint8_t passwordNumber, const uint8_t* password) {
    // Write password to data buffer first
    if (!writeDataBuffer(0, password, 4)) {
        return false;
    }
    
    uint8_t params[2];
    params[0] = 0;              // Buffer offset
    params[1] = passwordNumber; // Password number
    
    return executeRFIDCommand(RFID_CMD_PASSWORD_AUTH, params, 2);
}

bool RFID_B1::halt() {
    return executeRFIDCommand(RFID_CMD_HALT, nullptr, 0);
}

bool RFID_B1::writeDataBuffer(uint16_t offset, const uint8_t* data, uint16_t size) {
    return writeRFIDMemory(ADDR_DATA_BUFFER + offset, data, size);
}

bool RFID_B1::readDataBuffer(uint16_t offset, uint8_t* data, uint16_t size) {
    return readRFIDMemory(ADDR_DATA_BUFFER + offset, data, size);
}

bool RFID_B1::getTagUID(uint8_t* uid, uint8_t &uidSize) {
    if (_tagUIDSize > 0 && _tagUIDSize <= 10) {
        memcpy(uid, _tagUID, _tagUIDSize);
        uidSize = _tagUIDSize;
        return true;
    }
    return false;
}

uint8_t RFID_B1::getTagType() {
    return _tagType;
}

uint8_t RFID_B1::getLastResult() {
    return _lastResult;
}

// High-level NTAG215 Functions

bool RFID_B1::readNTAG215(uint8_t startPage, uint8_t numPages, uint8_t* data) {
    // NTAG215 has pages 0-134 (135 pages total)
    if (startPage + numPages > NTAG215_PAGES) {
        return false;
    }
    
    // Read pages
    if (!readPage(startPage, numPages, 0)) {
        return false;
    }
    
    // Read data from buffer
    return readDataBuffer(0, data, numPages * NTAG215_PAGE_SIZE);
}

bool RFID_B1::writeNTAG215(uint8_t startPage, const uint8_t* data, uint8_t numPages) {
    // NTAG215 has pages 0-134 (135 pages total)
    // User writable area is typically pages 4-129
    if (startPage + numPages > NTAG215_PAGES) {
        return false;
    }
    
    return writePage(startPage, data, numPages, 0);
}

bool RFID_B1::readNTAG215User(uint8_t* data, uint16_t &dataSize) {
    // Read user memory area (pages 4-129 = 126 pages = 504 bytes)
    uint8_t numPages = NTAG215_USER_END_PAGE - NTAG215_USER_START_PAGE + 1;
    
    if (!readNTAG215(NTAG215_USER_START_PAGE, numPages, data)) {
        return false;
    }
    
    dataSize = numPages * NTAG215_PAGE_SIZE;
    return true;
}

bool RFID_B1::writeNTAG215User(const uint8_t* data, uint16_t dataSize) {
    // Calculate number of pages
    uint8_t numPages = (dataSize + NTAG215_PAGE_SIZE - 1) / NTAG215_PAGE_SIZE;
    uint8_t maxPages = NTAG215_USER_END_PAGE - NTAG215_USER_START_PAGE + 1;
    
    if (numPages > maxPages) {
        return false;
    }
    
    return writeNTAG215(NTAG215_USER_START_PAGE, data, numPages);
}

// Utility Functions

const char* RFID_B1::getTagTypeName(uint8_t tagType) {
    switch (tagType) {
        case TAG_NO_TAG: return "No Tag";
        case TAG_INCOMPLETE: return "Incomplete Type";
        case TAG_ULTRALIGHT: return "Ultralight";
        case TAG_ULTRALIGHT_EV1_80B: return "Ultralight EV1 80B";
        case TAG_ULTRALIGHT_EV1_164B: return "Ultralight EV1 164B";
        case TAG_CLASSIC_MINI: return "Classic Mini";
        case TAG_CLASSIC_1K: return "Classic 1K";
        case TAG_CLASSIC_4K: return "Classic 4K";
        case TAG_NTAG203F: return "NTAG203F";
        case TAG_NTAG210: return "NTAG210";
        case TAG_NTAG212: return "NTAG212";
        case TAG_NTAG213F: return "NTAG213F";
        case TAG_NTAG216F: return "NTAG216F";
        case TAG_NTAG213: return "NTAG213";
        case TAG_NTAG215: return "NTAG215";
        case TAG_NTAG216: return "NTAG216";
        case TAG_UNKNOWN: return "Unknown";
        default: return "Invalid";
    }
}

const char* RFID_B1::getResultName(uint8_t result) {
    switch (result) {
        case RESULT_NO_ERROR: return "No Error";
        case RESULT_INVALID_CMD: return "Invalid Command";
        case RESULT_INVALID_PARAM: return "Invalid Parameter";
        case RESULT_INDEX_OUT_RANGE: return "Index Out of Range";
        case RESULT_NV_WRITE_ERROR: return "NV Write Error";
        case RESULT_SYSTEM_ERROR: return "System Error";
        case RESULT_TAG_CRC_ERROR: return "Tag CRC Error";
        case RESULT_TAG_COLLISION: return "Tag Collision";
        case RESULT_NO_TAG: return "No Tag";
        case RESULT_AUTH_ERROR: return "Authentication Error";
        case RESULT_VALUE_CORRUPTED: return "Value Corrupted";
        case RESULT_OVERHEATED: return "Overheated";
        case RESULT_TAG_NOT_SUPPORTED: return "Tag Not Supported";
        case RESULT_TAG_COMM_ERROR: return "Tag Communication Error";
        case RESULT_INVALID_PASSWORD: return "Invalid Password";
        case RESULT_ALREADY_LOCKED: return "Already Locked";
        case RESULT_MODULE_BUSY: return "Module Busy";
        default: return "Unknown Error";
    }
}

void RFID_B1::printUID(uint8_t* uid, uint8_t size) {
    for (uint8_t i = 0; i < size; i++) {
        if (uid[i] < 0x10) Serial.print("0");
        Serial.print(uid[i], HEX);
        if (i < size - 1) Serial.print(":");
    }
    Serial.println();
}

void RFID_B1::printBuffer(uint8_t* data, uint16_t size) {
    for (uint16_t i = 0; i < size; i++) {
        if (data[i] < 0x10) Serial.print("0");
        Serial.print(data[i], HEX);
        Serial.print(" ");
        if ((i + 1) % 16 == 0) Serial.println();
    }
    Serial.println();
}
