===============================================================================

KT-001-0137-00 NTM Transceiver Board, Mid/High Band Test Utility

===============================================================================

1 - Introduction

This test utility is used for testing the KT-000-0137-00 NTM Transceiver Board,
Mid/High Band.  The test utility is run on an ST NUCLEO-L432KC board fitted
to the KT-000-0160-00 K-CEMA RF Board, NTM MB-HB, Test Interface Board.

The firmware can be built and installed on the NUCLEO board using:
- STM32CubeIDE Version 1.3.1

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
$ADC		| Reads the KT-000-137-00 ADC and displays the results, all ADC 
			| channels are read
			|
$BID		| Reads the KT-000-0137-00 Board ID pins and displays the read 
			| value as an unsigned integer value
			|
#DATT en	| Enables/disables the DDS 20 dB attenuator, en values:
			| 0 = disabled
			| Any other value = enabled
			|
#TFAT att	| Sets the tx fine attenuator to the specified value, att specifies
			| the number of 0.25 dB steps to switch in:
			| 0 = 0 dB
			| 1 = 0.25 dB
			| 2 = 0.50 dB
			| ...
			| 31 = 7.75 dB
			|
#TCAT att	| Sets the tx coarse attenuator to the specified value, att specifies
			| the number of 3 dB steps to switch in:
			| 0 = 0 dB
			| 1 = 3 dB
			| 2 = 6 dB
			| ...
			| 15 = 45 dB
			|
#RLBY en	| Enables/disables the rx LNA bypass, en values:
			| 0 = LNA
			| Any other value = Bypass
			|
#RXPS path	| Sets the rx pre-selector path, path values:
			| 0 = 400-600 MHz
			| 1 = 600-1000 MHz
			| 2 = 1000-1400 MHz
			| 3 = 1400-2200 MHz
			| 4 = 2200-3000 MHz
			| 5 = 3000-4600 MHz
			| 6 = 4600-6000 MHz
			| 7 = Isolation
			|
#TXP path	| Sets the tx  path, path values:
			| 0 = MB: 400-1500 MHz
			| 1 = MB: 1400-1880 MHz
			| 2 = MB: 1850-2250 MHz
			| 3 = MB: 2250-2500 MHz
			| 4 = MB: 2500-2700 MHz
			| 5 = MB: 2700-3000 MHz
			| 6 = Invalid Band 0
			| 7 = Invalid Band 1
			| 8 = HB: 2400-3400 MHz
			| 9 = HB: 3400-4600 MHz
			| 10 = HB: 4600-6000 MHz
			| 11 = Invalid Band 2
			| 12 = Invalid Band 3
			| 13 = Invalid Band 4
			| 14 = Invalid Band 5
			| 15 = Invalid Band 6
			|
#RXEN en	| Sets rx enable signal, en values:
			| 0 = disabled
			| Any other value = enabled
			|
#TXEN en	| Sets tx enable signal, en values:
			| 0 = disabled
			| Any other value = enabled			
			|
#XRST rst	| Sets transceiver reset signal, rst values:
			| 0 = reset de-asserted
			| Any other value = reset asserted
			|
$XVID		| Reads and returns the transceiver Vendor ID
			|
$GINT		| Reads and returns the state of the GP interrupt signal
			|
===============================================================================