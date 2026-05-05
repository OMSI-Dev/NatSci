#!/usr/bin/env python3
"""
Serial to OSC Bridge
Reads sensor data from serial and sends to Pure Data on port 4559
"""

import serial
import sys
from pythonosc import udp_client

SERIAL_PORT = sys.argv[1] if len(sys.argv) > 1 else 'COM4'
BAUD_RATE = 9600
OSC_IP = "127.0.0.1"
OSC_PORT = 4559

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)
    print(f"Serial: {SERIAL_PORT} | OSC: {OSC_IP}:{OSC_PORT}")
    
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"RX: {line}")
                    try:
                        # Parse multiple sensors: "1:0.121, 2:0.543, 3:0.789"
                        if ':' in line:
                            # Split by comma for multiple sensors
                            entries = line.split(',')
                            for entry in entries:
                                entry = entry.strip()
                                if ':' in entry:
                                    parts = entry.split(':')
                                    sensor_id = int(parts[0])
                                    value = float(parts[1])
                                    client.send_message("/sensor", [sensor_id, value])
                                    print(f"  -> OSC: /sensor {sensor_id} {value}")
                        else:
                            # Plain number
                            value = float(line)
                            client.send_message("/sensor", value)
                            print(f"  -> OSC: /sensor {value}")
                    except (ValueError, IndexError):
                        print(f"  (could not parse, skipping)")
                        
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
