# RFID B1 Protocol Quick Reference

## Packet Structure (Type A Header, Plain Data)

### Command Packet

```
┌────────────────────── HEADER ──────────────────────┐ ┌────────────── DATA ──────────────┐
│                                                     │ │                                  │
[0x02] [SizeLSB] [SizeMSB] [CRC_L] [CRC_H] [Command] [Param1] [Param2] ... [CRC_L] [CRC_H]
  │       │         │         │       │        │                               │       │
  │       │         │         └───────┴────────┼───────────────────────────────┘       │
  │       │         │                          │                                       │
  │       └─────────┴──> Header CRC            └────────────> Data CRC ────────────────┘
  │
  └──> Start of Text (STX)
```

### Response Packet

```
┌────────────────────── HEADER ──────────────────────┐ ┌────────────── DATA ──────────────┐
│                                                     │ │                                  │
[0x02] [SizeLSB] [SizeMSB] [CRC_L] [CRC_H] [Response] [Data1] [Data2] ... [CRC_L] [CRC_H]
```

## Example Packets

### 1. Dummy Command (0x00)

**Send:**
```
Header: 02 03 00 A5 27    (STX, Size=3, CRC=0x27A5)
Data:   00 BC 5C          (CMD=0x00, CRC=0x5CBC)
```

**Receive (ACK):**
```
Header: 02 03 00 A5 27    (STX, Size=3, CRC=0x27A5)
Data:   00 BC 5C          (Response=ACK, CRC=0x5CBC)
```

### 2. Read RFID Memory (Tag Type)

**Send (Read 1 byte from 0x001E):**
```
Header: 02 07 00 1A 2E
Data:   02 1E 00 01 00 D1 3F
         │  └──┬──┘ └──┬──┘
         │  Address   Size=1
         └─ CMD_READ_RFID_MEMORY
```

**Receive (if NTAG215):**
```
Header: 02 04 00 80 C5
Data:   00 0E C4 BD
         │  │  └──┬─ CRC
         │  └─ 0x0E (TAG_NTAG215)
         └─ ACK
```

### 3. Write RFID Memory (Command Register)

**Send (Write 0x01 to address 0x0001 to execute Get UID command):**
```
Header: 02 08 00 37 6D
Data:   01 01 00 01 00 01 DB EA
         │  └──┬──┘ └──┬──┘ │
         │  Address   Size   └─ Data to write (0x01 = Get UID)
         └─ CMD_WRITE_RFID_MEMORY
```

**Receive (ACK):**
```
Header: 02 03 00 A5 27
Data:   00 BC 5C
```

**Then receive (Async Packet when command completes):**
```
Header: 02 04 00 80 C5
Data:   08 01 B4 9C
         │  │  └──┬─ CRC
         │  └─ Event flags
         └─ RESP_ASYNC_PACKET
```

### 4. Read Page Command Sequence

**Step 1: Write command parameters (page=4, count=1, offset=0)**
```
Header: 02 0A 00 C0 05
Data:   01 02 00 03 00 04 01 00 71 A7
         │  └──┬──┘ └──┬──┘ │  │  │
         │  Addr=2   Size=3  │  │  └─ Buffer offset
         │  (params)          │  └─ Read count
         └─ CMD_WRITE         └─ Page 4
```

**Step 2: Write RFID command (0x06 = Read Page)**
```
Header: 02 08 00 37 6D
Data:   01 01 00 01 00 06 18 8A
         │  └──┬──┘ └──┬──┘ │
         │  Addr=1   Size=1  └─ RFID_CMD_READ_PAGE
         └─ CMD_WRITE_RFID_MEMORY
```

**Step 3: Wait for async packet**
```
Header: 02 04 00 80 C5
Data:   08 01 B4 9C
         └─ Command complete
```

**Step 4: Read data buffer (0x0020, 4 bytes)**
```
Header: 02 07 00 1A 2E
Data:   02 20 00 04 00 2E DB
         │  └──┬──┘ └──┬──┘
         │  Addr=32  Size=4
         └─ CMD_READ_RFID_MEMORY
```

**Receive:**
```
Header: 02 07 00 1A 2E
Data:   00 XX XX XX XX YY YY
         │  └────┬────┘ └─┬─ CRC
         │     4 bytes     
         └─ ACK
```

## Command Reference

### UART Commands

| Code | Command | Parameters |
|------|---------|------------|
| 0x00 | Dummy | None |
| 0x01 | Write RFID Memory | Addr[2], Size[2], Data[Size] |
| 0x02 | Read RFID Memory | Addr[2], Size[2] |
| 0x03 | Enter Sleep | None |
| 0x04 | Reset | None |

### RFID Commands (written to 0x0001)

| Code | Command | Parameters (at 0x0002) |
|------|---------|------------------------|
| 0x01 | Get UID and Type | None |
| 0x06 | Read Page | Page, Count, BufOffset |
| 0x07 | Write Page | Page, Count, BufOffset |
| 0x17 | Password Auth | BufOffset, PasswordNum |
| 0x18 | Halt | None |

## CRC Calculation Example

```cpp
uint16_t calculateCRC(const uint8_t* data, uint16_t size) {
    uint16_t crc = 0xFFFF;
    
    for (uint16_t i = 0; i < size; i++) {
        uint16_t temp = ((crc >> 8) ^ data[i]) & 0xFF;
        crc = CCITTCRCTable[temp] ^ (crc << 8);
    }
    
    return crc; // LSB first when sending
}

// Example: Calculate CRC for [0x00]
// Result: 0x5CBC
// Send as: [BC 5C] (LSB first)
```

## Timing Requirements

- **Inter-byte timeout**: Max 100ms between bytes in a packet
- **Command execution**: Varies (typically 10-100ms for RFID operations)
- **Async packet**: Usually within 2 seconds for RFID commands
- **Reset time**: ~200ms after reset command
- **Startup time**: ~100-500ms after power-on

## Common Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0x00 | NO_ERROR | Success |
| 0x01 | INVALID_COMMAND | Command byte not recognized |
| 0x02 | INVALID_PARAM | Parameter out of range |
| 0x06 | TAG_CRC_ERROR | CRC error in tag communication |
| 0x08 | NO_TAG | No tag in field |
| 0x09 | AUTH_ERROR | Authentication failed |
| 0x0D | TAG_COMM_ERROR | Tag communication error |
| 0xFF | MODULE_BUSY | Module is busy |

## Memory Layout

```
0x0000 - 0x0000  Result Register (R)
0x0001 - 0x0001  Command Register (R/W)
0x0002 - 0x0013  Command Parameters (R/W) [18 bytes]
0x0014 - 0x001D  Tag UID (R) [10 bytes]
0x001E - 0x001E  Tag Type (R)
0x001F - 0x001F  Tag UID Size (R)
0x0020 - 0x011F  Data Buffer (R/W) [256 bytes]
0x0120 - 0x0127  Password (R/W - when unlocked)
...
```

## NTAG215 Page Layout

```
Page  Address  Contents
────  ───────  ────────────────────────────
0     0x00     UID[0-2], BCC0
1     0x04     UID[3-6]
2     0x08     BCC1, Internal, Lock[0-1]
3     0x0C     Capability Container
4     0x10     ┐
...            │ User Memory
129   0x204    ┘ (504 bytes total)
130   0x208    Dynamic Lock Bytes
131   0x20C    RFID Reserved
132   0x210    Config
133   0x214    PWD (Password)
134   0x218    PACK / RFGCFG
```

## Debugging Tips

1. **Enable verbose logging**: Print all sent/received bytes in hex
2. **Verify CRC**: Manually calculate and compare CRCs
3. **Check timing**: Use micros() to measure inter-byte delays
4. **Serial monitor**: Set to "No line ending" for manual packet sending
5. **Logic analyzer**: Great for verifying UART signals (9600 8N1)

## Typical Command Sequence

```
1. Power on / Reset
2. Wait for RESP_SYSTEM_START (0x0A)
3. Optional: Send dummy command to verify communication
4. Write 0x01 to command register (Get UID)
5. Wait for RESP_ASYNC_PACKET (0x08)
6. Read result register (should be 0x00)
7. Read tag type and UID
8. Write command parameters for read/write
9. Write RFID command
10. Wait for async packet
11. Read result and data buffer
12. Repeat from step 8 for more operations
```

## Serial Monitor Testing

Send these hex strings (ensure "No line ending"):
```
Get Module Version:
02 03 00 A5 27 00 BC 5C

Read Tag Type:
02 07 00 1A 2E 02 1E 00 01 00 D1 3F
```

## Logic Analyzer Settings

- **Baud**: 9600
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **Voltage**: 3.3V
