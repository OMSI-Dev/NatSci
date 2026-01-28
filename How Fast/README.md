# How Fast Details
## Theory of Operation

There are ten tubes that are each 15 feet tall, lined up vertically and in parallel. Each tube has air flowing up through it with a coverable opening protruding from the base and a ball inside. The player covers the opening to block the air from coming out of that tube and holds their hand over until the ball reaches a predestined point in the tube. The tube on the very left has a low point to reach, where the tube on the right has a high point to reach. As one of the tubes is completed, a corresponding section of an LED lights up in the wall behind the tubes. The player does every tube in sequential order from left to right until the whole LED curve / graph is lit up. 

The LED line is representing a graph of the amount of carbon released over time in respect to industrialization. 

## Updating software

The software is built using platform.io. You can use Visual Studio Code to modify or update the software. Clone the How Fast/Software folder to your local computer, then open the folder in Visual Studio Code and let platform.io start. Upload changes to the Teensy 4.1.

## Project File Organization

README.md : basic project info, the file you're currently reading.
Hardware : Schematic and board PDFs and the PCB zip file.
Softare:
	README.md : Information about the software / code.
	include : Header files used in cource code.
	src : Source code (main.cpp).
	some other directories are used by platformio and vscode
Sound: Sound assets for gameplay.

#### Hardware

[A detailed list of all of the hardware used and the quantity of each. Go through each Phoenix connector first, specified by pin, then create a list of the rest of the hardware components.]

EXAMPLE:
**Phoenix connectors:**

2-pin: (4 qty)

	1. 5V
	
3-pin: (4 qty)

	1. LED Strip
	2. Upper Rings LEDs
	3. Lower Rings LEDS
	4. GND pins - for grounding each of the LED arrays, which each recieves separate power.
	5. 12V
	
4-pin: (11 qty)

	1-10. TOF1 - TOF10
	11. Sound

Various Components:

	3 mosfets (SMD 7460AAW44K)
	3 10K SMS Resistors
	32U4 - 5v itsyBitsy
	Stepper Motor
	Stepper Driver
	IR Sensor (CPB765WZ)
	Happ Switch
	Reed Switch
	Maglock
	24V PSU
	12V PSU
	5V across USB

#### Sensor Board

[List the sensor board and its function.]
EXMAPLE:
IR sensor board - used to set IR with resistors as well as a troubleshooting board.

## Audio

[If any audio, describe where they are located in the file organization and how to replace if needed. Include the naming scheme of the files and what part of the exhibit/component they affect.]
EXAMPLE:
They are Mp3 files stored /data/sound/ and can be updated simply by following the naming scheme and replacing old files. It is recommended making a backup before replacing any files. 
Capitalization matters. 

##### Naming scheme:

	Failure: red.mp3
	Average: orange.mp3
	Success: green.mp3
