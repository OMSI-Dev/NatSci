Checkpoints: 

Test 0
    - [ ]  PILL BOARD (M0 Express) connected to MAIN BOARD (Teensey 4.1) communicating
        - [ ]  PILL BOARD initialize I2C address from header pins
            - [ ]  Setup: Read header pins A-D (Pin  3,4,5,7)
            - [ ]  Function: Recognize which pins are tied HIGH
                - [ ]  Create I2C address based on the read header pin(s)
                - [ ]  Start I2C communication with determined address
    - [ ]  MAIN BOARD (Teensy 4.1) await I2C communication
        - [ ]  MAIN BOARD sends LED data to PILL BOARD via SDA/SCL once I2C communication is confirmed
        - [ ]  PILL BOARD receives LED data via SDA/SCL and sends LED data via Pin 2 to display

Reference pinouts:

**M0 Express**
Sensors to M0 Express
1. Sen1_OUT to Pin A0
2. Sen2_OUT to Pin A1
3. Sen3_OUT to Pin A2

**Teensy 4.1**
4-Pin Phoenix to Sensor 1
1. SCL to Pin 19 of Teensy 4.1
2. SDA to Pin 18 of Teensy 4.1
3. GND to GND 
4. 3.3V to 3.3V

