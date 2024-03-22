===============================================================================

KT-000-0136-00 NTM Transceiver Board, Low Band Test Utility

===============================================================================

1 - Introduction

This test utility is used for testing the KT-000-0136-00 NTM Transceiver Board,
Low Band.  The test utility is run on an ST NUCLEO-L432KC board fitted
to the KT-000-0155-00 K-CEMA RF Board, NTM LB, Test Interface Board.

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
$BID		| Reads the KT-000-0136-00 Board ID pins and displays the read 
			| value as an unsigned integer value
			|
#RXPE		| Sets the Receiver Power Enable signal, en values:
			| 0 = disable power
			| Any other value = enable power
			|
$ADC		| Reads the KT-000-136-00 ADC and displays the results, all ADC 
			| channels are read
			|
#DAC val	| Set the OCXO trim DAC to specified value, val is DAC step,
			| 1 mV/DAC step, range 300 -> 3,000 mV
			|
#DACE ch val ivr g2 pd | 
			| Set DAC values and store in device non-volatile memory for
			| recall at power-up:
			| ch - Channel: 1 = A 
			|               ... 
			|				4 = D
			| val - DAC step value: 1 mV/DAC step, range 300 -> 3,000 mV
			| ivr - Internal Voltage Reference: 0 = external reference
			| 									Any other value = internal 
			|													  reference
			| g2 - Enable channel x2 gain: 0 = disable
			|							   Any other value = enable
			| pd - Power Down Mode: 0 = channel on
			|						1 = channel off with 1k pull-down
			|						2 = channel off with 100k pull-down
			|						3 = channel off with 500k pull-down
			|
$DAC ch		| Read and display data for the specified DAC channel, ch values:
			| 
			| 1 = A 
			| ... 
			| 4 = D
			|		
$LDS		| Read and display the state of the frequency synthesiser lock-
			| detect signals
			|
#SSEL syn	| Select the specified synthesister, syn values:
			| 1 = Synth 1
			| 2 = Synth 2
			|
#SFQ syn fq	| Set the RF centre frequency to the specified value in MHz using 
			| the specfied synthesiser:
			| syn - Synthesiser: 1 = Synth 1
			|					 2 = Synth 2
			| fq - Frequency in MHz, range = 45 to 495 MHz, resolution = 1 MHz
			|
#PSLR path	| Select the specified preselector path, path values:
			| 0 = "20-80 MHz"
			| 1 = "80-130 MHz",
			| 2 = "130-180 MHz"
			| 3 = "180-280 MHz"
			| 4 = "280-420 MHz"
			| 5 = "400-470 MHz"
			| 6 = "470-520 MHz"
			| 7 = "Isolation"
			|
#RATT att	| Sets the RF attenuator to the specified value, att specifies the 
			| number of 0.5 dB steps to switch in:
			| 0 = 0 dB
			| 1 = 0.5 dB
			| 2 = 1.0 dB
			| ...
			| 31 = 15.5 dB
			|
#IATT att	| Sets the IF attenuator to the specified value, att specifies the 
			| number of 0.5 dB steps to switch in:
			| 0 = 0 dB
			| 1 = 0.5 dB
			| 2 = 1.0 dB
			| ...
			| 31 = 15.5 dB
			|
#LNBY en	| Enables/disables the receive LNA bypass, en values:
			| 0 = LNA
			| Any other value = Bypass
			|
$MXL		| Read and display the mixer RF level in centi-dBm
			|
===============================================================================