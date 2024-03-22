===============================================================================
KT-000-0146-00 RCU PCB Test Tools

This folder contains tools for testing the KT-000-0146-00 K-CEMA RCU Board for 
Active Keypad.  It is assumed that the board is tested in conjunction with a 
KT-000-0147-00 K-CEMA Active Keypad or test interface that simulates this board.

The test tools consist of:

1 - RCU Test Interface Board	/rcu_test_intf_board_0146
2 - RCU Test Utility Firmware 	/rcu_pcb_0146_test_utility
3 - KT-000-0165-00 Keypad and RCU Board Test Utility /rcu_keypad_pcb_test_jig_utility

===============================================================================
1 - RCU Test Interface Board:

The RCU test interface board is used to:
- Supply power to the board under test
- Interface an EIA-485 cable to the board under test
- Generate an EIA-485 signal level 1PPS signal to the board under test
- Perform loopback testing of the board under test's XCHANGE UART
- Report the board under test's +3V3 and +12V supply rail voltages
- Report the state of the XCHANGE Reset, RCU Power Button and Zeroize Power 
  Enable discrete outputs from the board under test
- Provide a Segger J-Link SWD interface connector for the board under test

The test interface board uses an Arduino Nano to perform automatic checks and
output monitoring.

Files for the RCU test interface board are in the ./rcu_test_intf_board_0146/ 
folder:
- Schematics, "Test Interface Board Schematic.vsdx"
- Arduino Nano sketch, "rcu_test_intf_board_0146.ino"

Use the Arduino IDE to install the sketch on the Nano.

Output monitoring and automatic check results are reported via the Nano's USB 
serial adapter interface:  
- Connect the Nano to a test PC using a Mini-USB connector
- Open a serial terminal window to view the output
- Serial settings:
	- Baud = 115200
	- Data bits = 8
	- Start bits = 1
	- Stop bits = 1
	- Parity = None
	- Flow Control = None
	
===============================================================================
2 - RCU Test Utility Firmware 

The RCU test utility firmwware is found in the folder 
./rcu_pcb_0146_test_utility/  The folder contains an STM32CubeIDE project and
source code for the test utility.  

The utility is targeted at the KT-000-0146-00 ST Microelectronics 
STM32L071CZT6 microcontroller.

Different versions of the utility are 
used depending on the test interface board and verson of -0146 board:

	Version 1.x.x - KT-000-0146-00 Rev A.x with /rcu_test_intf_board_0146
			test interface board
	Version 2.x.x - KT-000-0146-00 Rev B.x onwards with 
			/rcu_test_intf_board_0146 test interface board
	Version 3.x.x - KT-000-0146-00 Rev B.x onwawrds with KT-000-0165-00 
			production test interface board (backwards 
			compatibility with /rcu_test_intf_board_0146 is
			maintained in the source code)

The test utility is run on the board under test and performs the following 
functions:
- EIA-485 ASCII comamand interface (see command description below):
	- Read/set hardware configuration information
	- Set LED patterns on -0147 board
	- Read button inputs
	- Set XCHANGE reset output
	- Enable/disable buzzer
- XCHANGE UART serial echo

Build the test utility using STM32CubeIDE.  The test utility can be installed
on the board under test's STM32L071CZT6 microcontroller using ST-Link or Segger
J-Link programmers.  J-Link scripts for erasing and programming the device can
be found in the /rcu_pcb_0146_test_utility/jlink_command_files folder.

The XCHANGE UART serial settings are:
	- Baud = 57600
	- Data bits = 8
	- Start bits = 1
	- Stop bits = 1
	- Parity = None
	- Flow Control = None
	
The EIA-485 UART serial settings are:
	- Baud = 115200
	- Data bits = 8
	- Start bits = 1
	- Stop bits = 1
	- Parity = None
	- Flow Control = None
	
The EIA-485 ASCII serial commands are listed below.  Type the command using a 
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
$BTN		| Displays the state of the keypad buttons
			|
#BZR state	| Sets the buzzer output to state:
			| 0 = disabled
			| Any other value = enabled
			|
#XRST state	| Sets the XHANGE Reset output to state:
			| 0 = de-asserted
			| Any other value = asserted
			|
#LDC event	| Sets the event that causes the LED indications to change state:
			| 0 - rising edge of 1PPS input
			| 1 - falling edge of BTN0
			| 2 - falling edge of BTN1
			| 3 - falling edge of BTN2
			| 4 - internal 2 Hz timer
			|
#LDM mode	| Sets the LED indication mode:
			| 0 - LEDs all off
			| 1 - All LEDs on single colour, repeating cycle: 
			|		off/green/red/yellow
			| 2 - A single LED is lit, lit LED incremented by change event
			| 3 - All LEDs lit in a strobing green/yellow/red pattern 

===============================================================================
3 - KT-000-0165-00 Keypad and RCU Board Test Utility

The KT-000-0165-00 Keypad and RCU Board test utility firmwware is found in the 
folder ./rcu_keypad_pcb_test_jig_utility/  The folder contains an STM32CubeIDE 
project and source code for the test utility.

The test utility is targeted at an ST Microelectronics NUCLEO-L432KC board
which is fitted to the KT-000-0165-00 test interface board.

The test utility outputs signal monitoring and automatic check results for the 
KT-000-0147-00 and KT-000-0146-00 boards to the serial ST-Link Virtual COM Port:  

- Connect the Nucleo to a test PC using a micro-USB cable
- Open a serial terminal window to view the output
- Serial settings:
	- Baud = 115200
	- Data bits = 8
	- Start bits = 1
	- Stop bits = 1
	- Parity = None
	- Flow Control = None

===============================================================================