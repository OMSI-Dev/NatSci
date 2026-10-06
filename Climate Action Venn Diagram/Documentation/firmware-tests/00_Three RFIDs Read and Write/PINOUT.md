\*theoretical pinout made by autumn 3.18.26



Antennae Module 1
	GND to GND
	TX1 to ANT2 of RFID Module 1
	TX2 to ANT1 of RFID Module 1
	GND to GND



RFID Module 1 (Group)
	nPWRDN to Pin 5 of Teensy
	UART_RX to Pin 14 (TX3) of Teensy
	UART_TX to Pin 15 (RX3) of Teensy
	TPI to Pin 2 of Teensy
	ANT2 to TX1 of Antennae Module 1
	ANT1 to TX2 of Antennae Module 1
	VDD to 3V of Teensy
	100uF capacitor between VDD and GND



Antennae Module 2
	GND to GND
	TX1 to ANT2 of RFID Module 2
	TX2 to ANT1 of RFID Module 2
	GND to GND



RFID Module 2 (Interest)
	nPWRDN to Pin 11 of Teensy
	UART_RX to Pin 17 (TX4) of Teensy
	UART_TX to Pin 16 (RX4) of Teensy
	TPI to Pin 3 of Teensy
	ANT2 to TX1 of Antennae Module 2
	ANT1 to TX2 of Antennae Module 2
	VDD to 3V of Teensy
	100uF capacitor between VDD and GND



Antennae Module 3
	GND to GND
	TX1 to ANT2 of RFID Module 3
	TX2 to ANT1 of RFID Module 3
	GND to GND

RFID Module 3 (Topic)
	nPWRDN to Pin 6 of Teensy	
	UART_RX to Pin 20 (TX5) of Teensy
	UART_TX to Pin 21 (RX5) of Teensy
	TPI to Pin 4 of Teensy
	ANT2 to TX1 of Antennae Module 3
	ANT1 to TX2 of Antennae Module 3
	VDD to 3V of Teensy
	100uF capacitor between VDD and GND



Teensy 4.0
	Pin 5 to nPWRDN of RFID Module 1
    Pin 11 to nPWRDN of RFID Module 2
	Pin 6 to nPWRDN of RFID Module 3

	Pin 10 to LED Strip Data (single strip with 3 sections)
	Pin 14 (TX3) to UART_RX of RFID Module 1
	Pin 15 (RX3) to UART_TX of RFID Module 1

	Pin 16 (RX4) to UART_TX of RFID Module 2
	Pin 17 (TX4) to UART_RX of RFID Module 2

	Pin 20 (TX5) to UART_RX of RFID Module 3
	Pin 21 (RX5) to UART_TX of RFID Module 3

	Pin 2 to TPI1 (Tag Presence Indicator 1)
	Pin 3 to TPI2 (Tag Presence Indicator 2)
	Pin 4 to TPI3 (Tag Presence Indicator 3)

	Pin 1 to Button 1 PWM
	3V to VDD of all RFID Modules

