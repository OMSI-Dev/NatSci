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

*Refer to the above chart and diagram.*

To be finished by autumn, last updated 2026-10-06
