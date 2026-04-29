import serial
from pythonosc import udp_client
import time

# === CONFIG ===
SERIAL_PORT = "/dev/ttyUSB0"  # Your ESP32 serial port
BAUD_RATE = 115200
OSC_IP = "127.0.0.1"          
OSC_PORT = 4559               # OSC port
OSC_PATH = "/vl53/distance"

# === SETUP ===
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)

# === MAIN LOOP ===
while True:
    line = ser.readline().decode().strip()
    if line.isdigit():  # Only handle valid numbers
        distance = int(line)
        print(f"Distance: {distance} mm")  # For debugging
        client.send_message(OSC_PATH, distance)
    time.sleep(0.02)  # ~50Hz update
