===============================================================================
KT-000-0139-00 Active Backplane PCB Test Tools

This folder contains tools for testing the KT-000-0139-00 K-CEMA Active 
Backplane, 5-Bay.  

The test tools consist of:

1 - Arduino sketch to read EUI-48 MAC address from Microchip 24AA025E48 IC,
    for further details see:
    http://confluence.kirintec.local/display/KEW/KT-000-0139-00+Rev+A.1+MAC+Addresses  

2 - ST NUCLEO-L432KC firmware utility for the KT-000-0165-00 Active Backplane
    test jig.

3 - Test scripts includes Python scripts used for Active Backplane testing

===============================================================================
2 - Active Backplane Test Jig Utility

The Active Backplane Test Jig Utility is found in the folder 
./ab_pcb_test_utility.  The folder contains an STM32CubeIDE project source code
for the utility.

The utility is targeted at a NUCLEO-L432KC board which is fitted to the Arduino
Nano header on the KT-000-0165-00 test jig.

The test utility has an ASCII serial command interface to perform the following
functions:
- Read/set hardware configuration information on the KT-000-0139-00 board
  under test
- Send a 1PPS signal to the KT-000-0139-00 board under test
- Set the Rack Address discrete input to the KT-00-0139-00 board under test
- Set the DCDC Off discrete input to the KT-000-0139-00 board under test
- Set the System Reset discrete input to the KT-000-0139-00 board under test
- Monitor the +3V3 rail of the KT-000-0139-00 board under test
- Read the Micro and Switch EUI-48 MAC IDs from the KT-000-0139-00 board under 
  test

Build the test utility using STM32CubeIDE.  The test utility can be installed
on the NUCLEO-L432KC using the board's built-in ST-LINK programmer.  

The ST-LINK Virtual COM port UART serial settings are:
	- Baud = 115200
	- Data bits = 8
	- Start bits = 1
	- Stop bits = 1
	- Parity = None
	- Flow Control = None
	
The ASCII serial commands are listed below.  Type the command using a serial 
terminal emulator and confirm it with the ENTER key.  Commands can be entered 
in lower or upper case text, received characters are automatically converted 
to upper case when they are received.  The test utility will respond with the 
status of the requested command.

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
			| str can be up to 16 characters in length, the 16th character  
			| will automatically be set to '\0' to null terminate the string.
			|
$PPS		| Reports if the 1PPS ouptut from the KT-000-0139-00 test firmware
			| is being received (Replaced by #PPS in V3.0.0 onwards)
			|
#PPS val	| Enable 1PPS output to the KT-000-0139-00 board under test, val:
			| 0 = disable 1PPS signal (idle low)
			| 1 = enable 1PPS signal
			| (Added in V3.0.0 onwards)
			|
#RADR val	| Set the KT-000-0139-00 Rack Address signal to val:
			| 0 = LOW
			| Any other value = HIGH
			|
#DCDC val	| Set the KT-000-0139-00 DC-DC Off signal to val:
			| 0 = DC-DC off
			| Any other value = DC-DC on
			|
#SRST val	| Set the KT-000-0139-00 System Reset signal to val, note this
			| signal shoud be asserted before using commands to access the 
			| hardware configuration information IC:
			| 0 = Reset de-asserted
			| Any other value = Reset asserted
			|
$ADC		| Display the current values of the +3V3 and STM32 VREFINT ADC railsc
			| (Added in V3.0.0 onwards)
			|
$MAC	 	| Display the micro and switch EUI-48 MAC addresses
			| (Added in V3.0.0 onwards)
			|

===============================================================================