# Energy Transitions for OMSI's Natural Sciences Hall

## Summary of interactives
The `Energy Transitions` project involves a simulated energy grid system that adapts to varying inputs (types of energy) placed by a participant. 

Two identical city stations are present; two circuit boards, firmware/software copies, and interactive landscapes.
 

## Objectives of interactives
The result of a participant's performance varies on the arrangement of energy types to their specific locations. 

Once an energy switch is pulled, cities surrounding the landscape will have different LED animations indicating the level of success. 

The results are lenient, a red cityscape indicates no correct feedback, yellow indicates at least one correct input, and rainbow signals success at all points of input.

## Checkpoints
1. Read orientation of magnets at all three sensor modules on the circuit board (with stability)
2. Compare orientation to onboard header address, determine if registered piece is `correct`
3. Once the switch is pulled, poll all sensor boards for correctness, send `RESULTS` game state to sensor and city boards
4. Light all LEDs on sensor and city boards according to the polled results. 
5. Timeout and reset game state to `IDLE`

# Hardware Assembly
## Magnet Sensor Boards
<img src = "Documentation/Photos/City Components and Pill Containers.jpeg" width="500" alt="City Components and Pill Containers.jpeg"><img src = "Documentation/Photos/Magnet Sensor PCBs.jpeg" width="500" alt="">

These magnet sensor boards have three onboard sensors. These sensors are one of the few components that we configured to be pre-assembled. 

**JST Connectors**
**If populating new boards**, note that standard JST female connectors will not fit properly. The width of the pins themselves will **not** fit the footprint of the current onboard connector. Either modify the footprint, or acquire the proper connectors.

**Header Pins**

<img src = "Documentation/Gameplay Design/Game Piece Polarities and Addresses.png" width="600" alt="">
<img src = "Documentation/Gameplay Design/Top-down diagram.png" width="500" alt="">

A four-row column of 2-pin header connectors help uniquely address each board. Bridging a combination of **one** or **two** of these headers will help identify the location of a magnet sensor board in relation to the `gameplay landscape`. 

Refer to the above chart and diagram.

## Telegraph Inputs
The telegraph inputs are [TODO (yet to be sourced)](github.com), 12V manual momentary contact switch. 

The telegraph works in a series of resistors to bring the logic level voltage down to 3.3V, which can be read by the `Teensy 4.0`. 

```
12V -> 560 Ω -> Pin 14 of Teensy 4.0 -> 220 Ω -> GND
                                          |
                                          V
                                         GND
```

## PT8211 and the Teensy 4.0
A `PT8211` audio shield [from PJRC](https://www.pjrc.com/store/pt8211_kit.html) is mounted on a `Teensy 4.0`, hosted on a custom circuit board.

PRJC's original `PT8211` shield design is for the `Teensy 3.x` footprint. The `Teensy 4.0` is used in this project to fit this requirement. 

Physical modifications are needed if a `Teensy 4.1` board is used. 

### Assembling the PT8211 shield
PRJC's `PT8211 T4` variation is used for  `morse code`. 

Refer to [this guide](https://www.pjrc.com/store/pt8211_kit.html), and ensure the `T4` variation is used. 


# Summary of components
1. Custom circuit board with parts:
```
    a) (*) Teensy 4.0 w/ PT8211 header to amp 
    b) (X1) terminal for LED output 
        - (R5) 10K resistor
        - (Q5) N-Channel mosfet
    c) (X2) terminal for 12V 
        - (C1) 10uF capacitor 
        - (D2) RED LED 
        - (R1) 500 Ohm resistor
        - (Q2) P-Channel mosfet
    d) (X3) terminal for 5V 
        - (C2) 10uF capacitor to 3.3V
        - (C3) 100nF capacitor to 5V
        - (D3) Red LED
        - (R4) 150 Ohm resistor 
        - (Q3) P-Channel mosfet
        - (CR1) 3.3V contage regulator
    e) (X4) Terminal for button output connection 
        - (D4) Green LED 
        - (R6) 10K Ohm resistor to 3.3V
        - (R7) 150 Ohm resistor 
        - (Q6) P-Channel mosfet
    c) (J1) terminal for button input/output line
        - (J2) JST connection 
        - (J3) JST connection
        
```
    (*)= mounted, not soldered on
    
2. Audio output parts:
```
    a) ZK-502T amplifier to speaker
    b) speaker
    c) 24V 5A power supply
```

3. Interactives:
```
    a) 2x buttons
    b) 2x LED fixtures
```

## TODO FIRMWARE

1. Verify functionality with LED modules. Assemble LED circuit board and test against it. 

## TODO Hardware

1. None for now (-:

## Time management

Sept 21-24 Telegraph


