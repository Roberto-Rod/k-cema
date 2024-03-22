===============================================================================

KT-001-0202-00 NTM Transceiver Board, Mid/High Band Extended Test Utility

===============================================================================

1 - Introduction

This test utility is used for testing the KT-000-0202-00 NTM Transceiver Board,
Mid/High Band Extended.  The test utility is run on an ST NUCLEO-L432KC board 
fitted to the KT-000-0160-00 K-CEMA RF Board, NTM MB-HB, Test Interface Board.
The test utility is compatible with KT-000-0160-00 post Rev C.1.

The firmware can be built and installed on the NUCLEO board using:
- STM32CubeIDE Version 1.4.2

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
$ADC		| Reads the KT-000-0202-00 ADC and displays the results, all ADC 
			| channels are read
			|
$BID		| Reads the KT-000-0202-00 Board ID pins and displays the read 
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
			| 127 = 31.75 dB
			|
#TCAT att	| Switches the tx coarse 20dB attenuator in/out:
			| 0 = 0 dB
			| 1 = 20 dB
			|
#RLBY en	| Enables/disables the rx LNA bypass, en values:
			| 0 = LNA
			| Any other value = Bypass
			|
#RXPS path	| Sets the rx pre-selector path, path values:
			| 0  = RX1: 5500-1050 MHz
			| 1  = RX0: 400-650 MHz
			| 2  = RX2: 950-1450 MHz
			| 3  = RX3: 1350-2250 MHz
			| 4  = RX4: 2150-3050 MHz
			| 5  = RX5: 2950-4650 MHz
			| 6  = RX6: 4550-6000 MHz
			| 7  = RX7: 5700-8000 MHz
			| 8  = RX1: 5500-1050 MHz
			| 9  = RX0: 400-650 MHz
			| 10 = RX2: 950-1450 MHz
			| 11 = RX3: 1350-2250 MHz
			| 12 = RX4: 2150-3050 MHz
			| 13 = RX5: 2950-4650 MHz
			| 14 = RX6: 4550-6000 MHz
			| 15 = RX7: 5700-8000 MHz
			|
#TXP path	| Sets the tx path, path values:
			| 0 = DDS0: 1480-1880 MHz
			| 1 = DDS1: 1850-2250 MHz
			| 2 = DDS2: 2250-3000 MHz
			| 3 = DDS3: 2400-3400 MHz
			| 4 = DDS4: 3400-4600 MHz
			| 5 = DDS5: 4600-6000 MHz
			| 6 = DDS6: 5700-8000 MHz
			| 7 = DDS7: 400-1500 MHz
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
#XTXP path	| Sets the transciever tx path, path values:
			| 0 = XCVR0: 400-6000 MHz
			| 1 = XCVR1: 5700-8000 MHz
			|
			|		
$SYNLD		| Read and display the state of the frequency synthesiser lock-
			| detect signal.
			|
#SYNFQ fq 	| Set the synthesiser RF centre frequency to the specified value in 
			| MHz, fq values:
			| fq - Frequency in MHz, range = 10800-12900 MHz, resolution = 1 MHz
			|
#SYNPD pd	| Sets synthesisier power-down bit, pd values:
			| 0 = power-down bit not asserted
			| Any other value = power-down bit asserted
			|
#SYNRG reg  | Write the specified 32-bit hexedecimal value, reg to the RF 
			| synthesiser
			|
===============================================================================