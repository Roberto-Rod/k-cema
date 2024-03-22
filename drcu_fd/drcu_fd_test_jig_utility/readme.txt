===============================================================================

KT-001-0207-00 DRCU and FD Test Jig Utility

===============================================================================

1 - Introduction

This test utility is used for testing the K-CEMA DRCU and FD Motherboards and 
Units.  The test utility is run on an ST NUCLEO-L432KC board fitted to the 
KT-000-0207-00 K-CEMA DRCu and FD Test Jig.

The firmware can be built and installed on the NUCLEO board using:
- STM32CubeIDE Version 1.4.2

===============================================================================

2 - Serial Command Interface

The test utility includes an ASCII serial command interface to set/get 
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
serial terminal window and confirm it with the <ENTER> key.  

Commands can be entered in lower or upper case text, received characters are 
automatically converted to upper case when they are received.  

The <UP> and <DOW> arrow keys can be used to scroll through the command 
history.

The test utility will respond with the status of the requested command.

Command:	| Description:
			|
			|
#PPSE en	| Enable/disable the 1PPS output, en values:
			| 0 = disable
			| Any other value = enable
			|
$PPSD		| Check if a 1PSS signal is being received by the NUCLEO-L432KC.			
			|
			|
$ADC		| Reads the NUCLEO-L432KC ADC channels and display the results, all  
			| ADC channels are read
			|
$GPI		| Reads and displays the state of the NUCLEO-L432KC general purpose
			| inputs:
			| - POWER_BUTTON_N
			| - POWER_ENABLE_ZEROISE_N
			| - XCHANGE_RESET
			|
#GPO gp val | Sets the state of the specified NUCLEO-L432KC general purpose output, 
			| gp values:
			| 0 = CSM_1PPS_DIRECTION
			| 1 = SOM_RESET
			| 2 = SOM_SD_BOOT_ENABLE
			| val values:
			| 0 = output low
			| Any other value = output high			
			
===============================================================================