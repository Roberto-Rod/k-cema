This project contains Python script files for testing the serial command interface to the K-CEMA Display RCU and
Fill Device defined in ICD document KT-957-0413-00.

The following libraries must be installed in the Python environment (virtual or system):

- pip install pyserial
- pip install pythoncrc

drcu_serial_msg_intf.py - Implements the K-CEMA Display RCU serial protocol command set specified in KT-957-0413-00.

keypad.py - Utility module for testing the Keypad on a Display RCU.

keypad_button_monitor.py - Utility module for monitoring keypad button status.

keypad_led_sync_check.py - Utility module for performing a visual check that the keypad LEDs are sync'd to the 1PPS
                           input.

keypad_led_visual_check.py - Utility module for performing a visual check that the keypad LEDs are functioning correctly.

serial_message_handler.py - Handles the generic part of the serial protocol specified in KT-957-0413-00.
