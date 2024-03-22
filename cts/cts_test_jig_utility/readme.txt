===============================================================================

KT-001-0206/0211-00 CTS Digital and RF Board Test Jig Utility

===============================================================================

1 - Introduction

This test utility is used for testing the KT-001-0206/0211-00 CTS Digital and 
RF Boards.  The test utility is run on an ST NUCLEO-L432KC board fitted to the 
KT-000-0214-00 K-CEMA Integrated CTS Test Jig.

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

The test utility will respond with the status of the requested command.

Command:	| Description:
			|
#RXATT att	| Sets the RF board rx attenuator to the specified value, att specifies the
			| number of 0.5 dB steps to switch in:
			| 0 = 0.0 dB
			| 1 = 0.5 dB
			| 2 = 1.0 dB
			| ...
			| 63 = 31.5 dB		
			|	
#RXP path	| Sets the RF board rx path, path values:
			| 0 = 20-500 MHz
			| 1 = 500-800 MHz
			| 2 = 800-2000 MHz
			| 3 = 2000-6500 MHz
			| 4 = 2600-4400 MHz
			| 5 = 4400-6000 MHz
			| 6 = Isolation 
			| 7 = TX
			|
#TXATT att	| Sets the RF board tx attenuator to the specified value, att specifies the
			| number of 0.5 dB steps to switch in:
			| 0 = 0.0 dB
			| 1 = 0.5 dB
			| 2 = 1.0 dB
			| ...
			| 63 = 31.5 dB		
			|
#TXP path	| Sets the RF board tx path, path values:
			| 0 = 20-800 MHz
			| 1 = 700-1500 MHz
			| 2 = 1200-2700 MHz
			| 3 = 2400-6000 MHz
			|			
#TXD div	| Sets the RF board tx divider, div values:
			| 0 = Divide ratio 1
			| 1 = Divide ratio 2
			| 3 = Divide ratio 4
			| 7 = Divide ratio 8
			|				
#GPO gp val | Sets the state of the specified STM32 zeroise microncontroller
			| general purpose output, gp values:
			| 0 = UUT_RB_SYNTH_EN
			| 1 = UUT_RB_SYNTH_nTX_RX_SEL
			| 2 = UUT_RB_RX_PATH_MIXER_EN
			| 3 = UUT_RB_P3V3_EN
			| 4 = UUT_RB_P5V0_EN
			| 5 = UUT_RB_P3V3_TX_EN
			| 6 = UUT_RB_P5V0_TX_EN 
			| 7 = UUT_DB_CTS_PWR_EN
			| 8 = UUT_DB_P12V_IN_EN
			| 9 = UUT_DB_P3V3_IN_EN
			| val values:
			| 0 = output low
			| Any other value = output high
			|		
#TRFP path	| Sets the test board RF path, path values:
			| 0 = Digital Board Test Rx Mode
			| 1 = RF Board Test Rx Mode
			| 2 = RF Board Test Tx Mode
			| 	
#PPSE en	| Enable/disable the 1PPS output, en values:
			| 0 = disable
			| Any other value = enable
			|
#PPSS src	| Set the 1PPS source, src values:
			| 0 = internal (STM32)
			| Any other value = external (Test Jig J9)	
			|
$ADC		| Reads the NUCLEO-L432KC ADC channels and display the results, all  
			| ADC channels are read
			|
$SYNLD		| Read and display the state of the frequency synthesiser lock-
			| detect signal.
			|
#SYNFQ fq 	| Set the synthesiser RF centre frequency to the specified value in 
			| MHz, fq values:
			| fq - Frequency in MHz, range = 54 -6800 MHz, resolution = 1 MHz
			|
#SYNPD pd	| Sets synthesisier power-down bit, pd values:
			| 0 = power-down bit not asserted
			| Any other value = power-down bit asserted
			|
#SYNRG reg  | Write the specified 32-bit hexedecimal value, reg to the RF 
			| synthesiser		
			|
#SYNI		| Intialie the RF synthesiser to its default state.			
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
#ILB en		| Sets the test jig I2C loopbaack enable signal, en values:
		 	| 0 = disable
			| Any other value = enable
			|
#EWRB a b	| Write byte value b (hex) to test jig I2C EEPROM address a (hex)
			|
$ERDB a 	| Read and return byte from test jig I2C EEPROM address a (hex)
			|
$ERDP pa 	| Read and return page of bytes from test jig I2C EEPROM at page 
			| address pa (hex)
			|			
===============================================================================