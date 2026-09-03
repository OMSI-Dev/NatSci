## Serial Format
```
1:0.543, 2:0.321, 3:1.123, 4:0.445
```
Format: `sensorNum:distanceMeters` (comma-separated, supports 1-10 sensors)

## Usage

1. `pip install -r requirements.txt`
2. `pio run -t upload`
3. `python serial_to_osc.py COM4`
4. Pure Data: `[netreceive -u -b 4559]` → `[oscparse]` → `[unpack s i i]` → `[print]`

## OSC Message

`/sensor sensorNum distanceMeters` - Example: `/sensor 1 0.543`

Python script auto-detects number of active sensors.

## Troubleshooting
- In powershell, run:

`Get-CimInstance -ClassName Win32_SerialPort | Select-Object Name, DeviceID | Format-Table -AutoSize`