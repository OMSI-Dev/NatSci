#!/usr/bin/env python3
"""
Multi-Sensor Serial to OSC Bridge
Reads sensor data in format: "1:54, 2:32, 3:11" and sends to Pure Data
Supports 1-10 sensors dynamically
"""

import serial
import re
import sys
from pythonosc import udp_client

SERIAL_PORT = sys.argv[1] if len(sys.argv) > 1 else 'COM4'
BAUD_RATE = 9600
OSC_IP = "127.0.0.1"
OSC_PORT = 4559

def parse_sensor_data(line):
    """Parse format: '1:0.543, 2:0.321, 3:1.123' into [(1, 0.543), (2, 0.321), (3, 1.123)]"""
    sensors = []
    # Split by comma and parse each sensorNum:distance pair
    for entry in line.split(','):
        entry = entry.strip()
        match = re.match(r'(\d+):([\d.]+)', entry)
        if match:
            sensor_num = int(match.group(1))
            distance = float(match.group(2))
            sensors.append((sensor_num, distance))
    return sensors

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)
    print(f"Serial: {SERIAL_PORT} | OSC: {OSC_IP}:{OSC_PORT}")
    print("Format: sensorNum:distanceMeters (e.g., '1:0.543, 2:0.321')\n")
    
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"RX: {line}")
                    
                    # Parse sensor data
                    sensors = parse_sensor_data(line)
                    
                    # Send OSC for each sensor
                    for sensor_num, distance in sensors:
                        client.send_message("/sensor", [sensor_num, distance])
                        print(f"  -> OSC: /sensor {sensor_num} {distance:.3f}m")
                        
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
