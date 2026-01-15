#!/usr/bin/env python3
"""
Projector Control Script for PV710UL
Usage:
    python projector_control.py on
    python projector_control.py off
    python projector_control.py status
"""

import requests
import sys
import time

PROJECTOR_IP = "10.10.51.100"
BASE_URL = f"http://{PROJECTOR_IP}/cgi-bin/pjctrl.cgi.elf"

POWER_ON = "D=%05%02%00%00%00%00"
POWER_OFF = "D=%05%02%01%00%00%00"
STATUS_CHECK = "D=%06%00%BF%00%00%01%02"


def send_command(command):
    """Send a command to the projector"""
    try:
        url = f"{BASE_URL}?{command}"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return data
            except:
                print(f"Response: {response.text}")
                return None
        else:
            print(f"Error: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None

def power_on():
    """Turn projector on"""
    print("Sending POWER ON command...!!!")
    result = send_command(POWER_ON)
    
    if not result:
        print("Failed power on")
        return
    
    print("Waiting for projector...")
    
    for i in range(15):  # Check 15 times (30 seconds total)
        time.sleep(2)
        
        status = send_command(STATUS_CHECK)
        if status and len(status) > 6 and status[6] in [3, 4]:
            print(f"Power on success after {(i+1)*2} seconds!")
            return
    
    print("Timeout- projector may be st")

def power_off():
    """Turn projector off"""
    print("Sending POWER OFF command...")
    result = send_command(POWER_OFF)
    if result:
        print("Power off success!")
    else:
        print("Failed power off")


def get_power_state():
    """Get current power state of projector"""
    result = send_command(STATUS_CHECK)
    if result and len(result) > 6:
        power_state = result[6]
        # 3 or 4 = Power On, other values = Power Off/Standby
        if power_state in [3, 4]:
            return True  # ON
        else:
            return False  # OFF/STANDBY
    return None  # Unknown/Error
    

def main():
    command = sys.argv[1].lower() #for calling script in terminal with a command following
    
    if command == "on":
        power_on()
    elif command == "off":
        power_off()
    elif command == "status":
        get_power_state()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
