===============================================================================

KT-001-0140-00 Central Servces Motherboard, Zeroise Processor Test Utility

===============================================================================

1 - Introduction

This tets utility is used for the testing the KT-000-0140-00 Central Services
Motherboard.  The test utility is run on the STM32L071CZT microcontroller 
fitted to the board.

The firmware can be built and installed on the NUCLEO board using:
- STM32CubeIDE Version 1.3.1 or greater

===============================================================================

2 - Serial Command Interface

The test utility includes an ASCII serial command interface to set/get board
parameters and signals.  

To use the serial interface:
- Connect the KT-000-0140-00 RCU EIA-422 interface to a test PC using an FTDI
  USB-RS422-WE (or similar) cable
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
#BZR en		| Enable/disable the +12V buzzer supply, en values:
			| 0 = disable
			| Any other value = enable
			|	
$GPI		| Reads and displays the value of the all the STM32 zeroise 
			| microcontroller's general purpose input signals
			|
#GPO gp val | Sets the state of the specified STM32 zeroise microncontroller
			| general purpose output, gp values:
			| 0 = ZER_PWR_HOLD
			| 1 = ZER_FPGA_PWR_EN
			| 2 = ZER_I2C_SOM_EN
			| 3 = ZER_I2C_FPGA_EN
			| 4 = ZER_FPGA_RST
			| 5 = RCU_MICRO_TX_EN
			| val values:
			| 0 = output low
			| Any other value = output high
			|
#ZGPO val	| Sets the GPO in the Zeroise FPGA connected to TP23 to the
			| specified value, also enables the 1 MHz clock output to TP22,
			| val:
			| 0 = TP23 output low; TP22 1 MHz output disabled
			| Any other value = TP23 output high; TP22 1 MHz output enabled
			|
$RAT		| Reads and returns the following registers from the anti-tamper
			| and power cable discconect detect M41ST87W devices:
			| - Flags
			| - Tamper 1
			| - Tamper 2
			|
#SAT dv ch en| Enables the specified M41ST87W device channel in normally open
			| connect mode with polarity, connect to GND.  This command clears
			| and then sets the Tamper Enabe bit so it can be used to reset a 
			| detected tamper event on a channel.
			| dv (device) values:
			| 0 = anti-tamper device
			| 1 = power cable disconnect detect device
			| ch (channel) values:
			| 0 = M41ST87W channel 1
			| 1 = M41ST87W channel 2
			| 0 = disable
			| Any other value = enable
			|
#LED id		| Turns the specified keypad LED ON, all LEDs are OFF, id values:
			| 0 = LED0
			| 1 = LED1
			| ....
			| 29 = LED29
			|
#LEDA col	| Sets all the keypad LEDs to the specified colour, col values:
			| 0 = Off
			| 1 = Green
			| 2 = Red
			| 3 = Yellow
			| 
===============================================================================