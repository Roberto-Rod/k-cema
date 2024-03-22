This project contains Python script files for testing the serial command interface to the NEO Battery Box defined in
ICD document KT-957-0413-00.

The following libraries must be installed in the Python environment (virtual or system):

- pip install pyserial
- pip install pythoncrc
- pip install py2exe

bb_simulator.py - Simulates the NEO battery box, run using command "python -s 'COMx'".  Connect to a second PC running
                  the Battery Box Test GUI or connect two serial ports on a single PC together.

bb_test_gui.py - Tkinter GUI for testing the NEO Battery Box serial interface, run using the command
                 "python bb_test_gui.py".  The default COM port can be changed by modifying the DEFAULT_COM_PORT
                  constant at the top of the file.

bb_test_gui_setup.py - Use to compile the GUI as a Windows exe using py2exe, "python bb_test_gui_setup.py py2exe".

bb_serial_msg_intf.py - Implements the NEO Battery Box serial protocol command set specified in KT-957-0413-00.

serial_message_handler.py - Handles the generic part of the serial protocol specified in KT-957-0413-00.
