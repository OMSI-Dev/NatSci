# Where is the Water Details
## Theory of Operation

Where is the Water is an augmented reality sandbox that projects depth data onto the sandbox's surface. The Kinect v2 and the projector are stationed above the sandbox. The Kinect detects the depth of the sandbox in real time as visitors interact with it and the projector displays the live, textured feed over the sandbox to mimic mountains and rivers / valleys that are created by the visitors.

There is a wooden tool with a circular graphic on the end. When held over the sandbox, the program will create rain where the tool is held over. The rain flows based on the depth of the sandbox and creates lakes where defined by the levels in the physical sandbox. There is a button to clear the water, mimicking a drought. When the button is pushed, all the water that was projected over the sandbox at the time that the button is pushed will dissipate. Any rain that is created after the button is pushed will not be cleared until the button is pushed again, ie if a visitor is creating rain at the moment that someone pushes the button to clear it, the rain that the visitor is currently creating will remain as the rest of the water that was built up will dissipate.

The software was built in Unity and will be run just by downloading the game application and running it. Callibration will be necessary if it is set up in a new area.

Callibration:
While the game is running, hit "c" to show the sphere that adjusts the bounding circle (defining where the rain can be created / the edges of the box). Hit "m" to enable movement of the sphere, which will then follow the position of the mouse translated into the world position (ie, it will move not as usually expected). Hit "s" to enable changing the size of the sphere / ellipse. Change the size with the up, down, left, and right arrows. Hit "s" again to lock the size of the circle / ellipse. Hit "m" again to lock the position, and hit "c" again to hide the bounding circle.

While the game is running, hit "h" to show the sphere that adjusts the bounding square (defining where the rain can be created / the edges of the box). Hit "n" to enable movement of the square, which will then follow the position of the mouse translated into the world position (ie, it will move not as usually expected). Hit "a" to enable changing the size of the square / rectangle. Change the size with the up, down, left, and right arrows. Hit "a" again to lock the size of the square / rectangle. Hit "n" again to lock the position, and hit "h" again to hide the bounding square.

## Updating software

All updates of the software must be done in Unity, where the project was built. It was created using editor version 2021.3.45f1. Open the project in Unity and update the scripts as needed in Visual Studio. Visual Studio 2022 was used for creating the game.

## Project File Organization
README.md : the file you're currently reading
Hardware : contains the .zip output of the circuit board from Fusion
OMSI AR Sandbox : the Unity file and all of it's contents, including the scripts for the program

[A list providing the contents of the files and their organization.]

#### Hardware

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

	1. Stepper Motor
	2. Maglock
	
6-pin: (1 qty)

	1.Lock Light
	2.Unlock Light

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

Water / rain audio is used in the WaterSimulation.cs script with the game object AudioClip rainAudio, referenced in the OnGesturesRead() function. The audio file used is called RainLoop in the Assets/Sandbox/Testing Stuff folder. If this file is changed, it will need to be updated / reattached to the WaterSimulation.cs file on the Modes/WaterSimulation game object.
