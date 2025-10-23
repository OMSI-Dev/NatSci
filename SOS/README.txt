# SOS Details

## ## Theory of Operation

Science On a Sphere (SOS) is a globe-based visualization system. These scripts synchronizes displayed content on the SOS with surrounding monitors and a nowPlaying kiosk.

## ## Updating software

The software is built using Python 3.14. Python libraries pillow and pywin32 must be installed before running. 

## ##Project File Organization

config.txt : configuration file for the SOS powerpoint controller

[engine.py](http://engine.py) : main engine that connects to SOS server, reads the current clip name, and synchronizes/controls a powerpoint presentation

noaa_042013.txt : slide database mapping dataset/display names to slide numbers

[parsers.py](http://parsers.py) : utility functions to parse configuartion files and the slide database, and to append new entries to the database

### >> Hardware

[A detailed list of all of the hardware used and the quantity of each. Go through each Phoenix connector first, specified by pin, then create a list of the rest of the hardware components.]

EXAMPLE:
**Phoenix connectors:**

2-pin: (4 qty)

	1. 24V
	2. Safety Switch
	3. Accel Sensor (1 pair)


3-pin: (3 qty)

	1. IR In
	2. Reed In
	3. 12v In


4-pin: (2 qty)

```
1. Stepper Motor
2. Maglock

```

6-pin: (1 qty)

```
1.Lock Light
2.Unlock Light

```

Various Components:

```
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

```

### Sensor Board

[List the sensor board and its function.]

EXAMPLE:
IR sensor board - used to set IR with resistors as well as a troubleshooting board.

## Audio

[If any audio, describe where they are located in the file organization and how to replace if needed. Include the naming scheme of the files and what part of the exhibit/component they affect.]

EXAMPLE:
They are Mp3 files stored /data/sound/ and can be updated simply by following the naming scheme and replacing old files. It is recommended making a backup before replacing any files.
Capitalization matters.

### Naming scheme:

```
Failure: red.mp3
Average: orange.mp3
Success: green.mp3

```

## Images/video

[If any images or videos, describe where they are located in the file organization and how to replace them if needed. Include the naming scheme and what part of the exhibit/component they affect.]

EXAMPLE:
The images are saved as PNG and the video is MP4, both are stored /data/images.  by following the naming scheme and replacing old files. It is recommended making a backup before replacing any files. Capitalization matters.

### Naming scheme:

```
Arrow Failure: redArrow.gif
Arrow Average: yellowArrow.gif
Arrow Success: greenArrow.gif
Head Failure: 3_en.png
Head Average:  2_en.png
Head Success:  1_en.png

```
