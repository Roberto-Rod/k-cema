===============================================================================

KT-000-0143-00 EMA Power Conditioning Module, NTM Interface Test Utility

===============================================================================

1 - Introduction

This test utility is used for testing the NTM (KT-000-0134-00) interface of the 
KT-000-0143-00 EMA Power Conditioning Module.  The test utility is run on an 
ST NUCLEO-L432KC board fitted to the KT-000-0150-00 K-CEMA EMA PCM-NTM Breakout
Board.

The firmware can be built and installed on the NUCLEO board using:
- STM32CubeIDE Version 1.3.1 or greater

===============================================================================

2 - Serial Command Interface

The test utility includes an ASCII serial command interface to set/get board
parameters and signals.  

To use the serial interface:
- Connect the NUCLEO board to a test PC using a Micro-USB connector
- Open a serial terminal window to view the output and send commands
- Serial settings:
	- Baud = 115200
	- Data bits = 8
	- Start bits = 1
	- Stop bits = 1
	- Parity = None
	- Flow Control = None
	
The ASCII serial commands are listed below.  Type the command using a 
serial terminal window and confirm it with the ENTER key.  Commands can be 
entered in lower or upper case text, received characters are automatically 
converted to upper case when they are received.  The test utility will respond
with the status of the requested command.

Command:	| Description:
			|
$HCI		| Displays hardware configuration information
			|
#RHCI		| Clears the hardware configuraion information stored in EEPROM 
			| and stores an empty image in the EEPROM
			|
#SHCI id str| Sets the hardware configuration information item id to str.  
			| id can be one of the following:
			| 0 - Assembly Part No.
			| 1 - Assembly Revision No.
			| 2 - Assembly Serial No.
			| 3 - Assembly Build Date/Batch No.
			| str can be up to 16 characters in length, the 16th character will 
			| automatically be set to '\0' to null terminate the string.
			|
$RDAC 		| Read and display the RDAC value from the digital potentiometer
			| used to adjust the +28V DC-DC converter output voltage
			|
#RDAC val 	| Set the RDAC value of the digital potentiometer used to adjust
			| the +28V DC-DC converter output voltage, range of values for val
			| is 0 to 1023
			|
#RSRDAC 	| Resets the digital potentiometer used to adjust the +28V DC-DC 
			| converter output voltage to power-on-reset values
			|
$50TP		| Read and display the last value stored to 50TP non-volatile
			| memory in the digital potentiometer used to adjust the +28V DC-DC
			| converter output voltage
			|
#50TP		| Store the current RDAC value of the digital potentiometer used to 
			| adjust the +28V DC-DC converter output voltage to 50TP non-
			| volatile memory, this value will be recalled next time the device
			| is reset
			|
#INIFAN		| Initialise the EMC2104 fan controller in the same manner as 
			| employed by the EMA application.  For further details see the 
			| following Confluence page:
			| http://confluence.kirintec.local/display/KEW/Microchip+EMC2104+Fan+Controller+Usage
			|
#FPT tmp	| Push the specified temperature to the fan controller, this value
			| will be used by the automatic fan speed control algorithm, tmp
			| values in the range -128 to +127 deg C
			|
#FDS pwm	| Configure the EMC2104 fan controller to operate in direct-speed
			| mode and set the PWM to the specified value, pwm values in the 
			| range 0 (0 %) to 255 (100 %)
			|
$FSP		| Read and display fan speed information from the EMC2104 fan 
			| controller
			|
$FTT		| Read and display the current fan tachometer target information
			| from the EMC2104 fan controller
			|
$TMP		| Read and display the temperature of the EMC2104 fan controller
			| internal temperature sensor
			|
$FST		| Read and display the EMC2104 fan controller status register
			|
$DOP		| Read and display the value of the KT-000-0143-00 discrete output
			| signals:
			| FAN_ALERT_N
			| RF_MUTE_N
			| PFI_N
			|
$1PPS		| Samples the 1PPS output from the KT-000-0143-00 to determine if 
			| the signal is present
			|
===============================================================================