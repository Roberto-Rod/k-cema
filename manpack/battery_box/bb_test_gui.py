#!/usr/bin/env python3
"""
Tkinter GUI application for interfacing with the NEO Battery Box, ICD KT-957-0413-00
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
None

"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import logging
import sys
from threading import Thread, Event
import time
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from bb_serial_msg_intf import BbSerialMsgInterface
# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_VERSION = "V1.0.0"
DEFAULT_COM_PORT = "COM22"
DEFAULT_BAUD_RATE = 115200

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class BbTestGui:
    """
    Tkinter GUI application class, all the functionality and methods needed
    to create, update and interact with the GUI window are in this class
    """
    BATT_PARAMS_STR = \
        "Batt | Serial No | Design Capacity (mAh)\n" \
        "1A   | {:<9d} | {:<21d}\n" \
        "1B   | {:<9d} | {:<21d}\n" \
        "2A   | {:<9d} | {:<21d}\n" \
        "2B   | {:<9d} | {:<21d}\n\n" \
        "Batt | V (mV) | I (mA) | SoC (%) | Temp (0.1 K) | Rem En (mAh)\n" \
        "1A   | {:<6d} | {:<6d} | {:<7d} | {:<12d} | {:<12d}\n" \
        "1B   | {:<6d} | {:<6d} | {:<7d} | {:<12d} | {:<12d}\n" \
        "2A   | {:<6d} | {:<6d} | {:<7d} | {:<12d} | {:<12d}\n" \
        "2B   | {:<6d} | {:<6d} | {:<7d} | {:<12d} | {:<12d}\n\n" \
        "Batt | EC | FD | FC | D  | I  | RT | RC | TD | OT | TC | OC\n" \
        "1A   | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d}\n" \
        "1A   | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d}\n" \
        "1A   | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d}\n" \
        "1A   | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d} | {:<2d}\n\n" \
        "EC - Error Code; FD - Fully Discharged; FC - Fully Charged; D - Discharging;\n" \
        "I - Initialised; RT - Remaining Time; RC - Remaining Capacity; TD - Terminate Discharge;\n" \
        "OT - Over Temperature; TC - Terminate Charge; OC - Over Charged"

    TEST_STR = BATT_PARAMS_STR.format(1, 1000,
                                      2, 2000,
                                      3, 3000,
                                      4, 4000,
                                      11, 12, 13, 14, 15,
                                      21, 22, 23, 24, 25,
                                      31, 32, 33, 34, 35,
                                      41, 42, 43, 44, 45,
                                      1, True, False, True, False, True, False, True, False, True, False,
                                      2, True, False, True, False, True, False, True, False, True, False,
                                      3, True, False, True, False, True, False, True, False, True, False,
                                      4, True, False, True, False, True, False, True, False, True, False)

    def __init__(self):
        """
        Class constructor, initialises the Tkinter GUI window and adds all the widgets to it.

        All of the text boxes on the GUI window have associated tk.StringVar variables which
        are used to get/set the displayed text.  Text boxes used solely for reporting purposes
        are set as read-only
        """
        # Set logging level to DEBUG initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.DEBUG
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

        # Set up the Tkinter window
        self._window = tk.Tk()
        self.initialise_window()

        # Set up the buttons which will appear in the left hand column
        self._button_frame = self._window
        self._buttons = {
            "com_port": tk.Label(self._button_frame, text="COM Port:"),
            "bad_ping": tk.Button(self._button_frame, text="Bad Msg ID Ping", command=self.bad_ping),
            "bad_crc": tk.Button(self._button_frame, text="Bad CRC Ping", command=self.bad_crc),
            "bad_len": tk.Button(self._button_frame, text="Short Length Ping", command=self.bad_len),
            "ping": tk.Button(self._button_frame, text="Ping", command=self.ping_cmd),
            # "poll_battery_parameters": tk.Checkbutton(self._button_frame, text="Poll Battery Parameters")
            "get_sw_version": tk.Button(self._button_frame, text="Get Software Version", command=self.get_sw_ver_cmd),
            "get_battery_parameters": tk.Button(self._button_frame, text="Poll Battery Parameters",
                                                command=self.get_batt_params_cmd),
        }

        # Set up string variables for use with Tkinter widgets
        self._text_vars = {
            "com_port": tk.StringVar(),
            "bad_ping": tk.StringVar(),
            "bad_crc": tk.StringVar(),
            "bad_len": tk.StringVar(),
            "ping": tk.StringVar(),
            "get_sw_version": tk.StringVar(),
        }

        for key in self._text_vars:
            self._text_vars[key].set("N/A")
        self._text_vars["com_port"].set(DEFAULT_COM_PORT)

        # Set up the text entry widgets which will appear in the middle column
        self._entry_frame = self._window
        self._entry_default_width = 30
        self._entries = {
            "com_port": tk.Entry(self._entry_frame, textvariable=self._text_vars["com_port"],
                                 width=self._entry_default_width),
            "bad_ping": tk.Entry(self._entry_frame, textvariable=self._text_vars["bad_ping"],
                                 width=self._entry_default_width, state="readonly"),
            "bad_crc": tk.Entry(self._entry_frame, textvariable=self._text_vars["bad_crc"],
                                width=self._entry_default_width, state="readonly"),
            "bad_len": tk.Entry(self._entry_frame, textvariable=self._text_vars["bad_len"],
                                width=self._entry_default_width, state="readonly"),
            "ping": tk.Entry(self._entry_frame, textvariable=self._text_vars["ping"],
                             width=self._entry_default_width, state="readonly"),
            "get_sw_version": tk.Entry(self._entry_frame, textvariable=self._text_vars["get_sw_version"],
                                       width=self._entry_default_width, state="readonly"),
            "get_battery_parameters": ScrolledText(self._entry_frame, font=("Courier New", 10), height=32, width=90),
        }

        self._entries["get_battery_parameters"].insert(tk.INSERT, "N/A")
        self._entries["get_battery_parameters"]["state"] = tk.DISABLED

        # Assemble the main window
        for i, key in enumerate(self._buttons):
            self._buttons[key].grid(column=1, row=i + 1, padx=5, pady=5, sticky="ne")

        for i, key in enumerate(self._entries):
            self._entries[key].grid(column=2, row=i + 1, padx=5, pady=5, sticky="nw")

        self._polling_batt_parameters = Event()
        self._polling_batt_thread = Thread()

    def run(self):
        """
        Tkinter GUI application main loop
        :return: N/A
        """
        self._window.mainloop()

    def initialise_window(self):
        """
        Set up the Tkinter window title and overall geometry
        :return: N/A
        """
        self._window.title("K-CEMA NEO Battery Box Test GUI - {}".format(SW_VERSION))
        self._window.geometry("1024x768")
        self._window.iconbitmap("kirintec_logo.ico")

    def bad_ping(self):
        """
        Send a valid message header with invalid Msg ID
        """
        self._text_vars["bad_ping"].set("Pinging with invalid Msg ID...")
        self._entries["bad_ping"].update()

        try:
            with BbSerialMsgInterface(self._text_vars["com_port"].get(), DEFAULT_BAUD_RATE) as bbsi:
                if bbsi.send_bad_ping(bad_id=True):
                    self._text_vars["bad_ping"].set("Ping Success - Unexpected")
                else:
                    self._text_vars["bad_ping"].set("Ping Fail - Expected")
        except Exception as ex:
            self._text_vars["bad_ping"].set("{}".format(ex))

    def bad_crc(self):
        """
        Send an invalid message header with corrupted CRC
        """
        self._text_vars["bad_crc"].set("Pinging with bad CRC...")
        self._entries["bad_crc"].update()

        try:
            with BbSerialMsgInterface(self._text_vars["com_port"].get(), DEFAULT_BAUD_RATE) as bbsi:
                if bbsi.send_bad_ping(bad_crc=True):
                    self._text_vars["bad_crc"].set("Ping Success - Unexpected")
                else:
                    self._text_vars["bad_crc"].set("Ping Fail - Expected")
        except Exception as ex:
            self._text_vars["bad_crc"].set("{}".format(ex))

    def bad_len(self):
        """
        Send an invalid message header with too few bytes
        """
        self._text_vars["bad_len"].set("Pinging with short header...")
        self._entries["bad_len"].update()

        try:
            with BbSerialMsgInterface(self._text_vars["com_port"].get(), DEFAULT_BAUD_RATE) as bbsi:
                if bbsi.send_bad_ping(short_msg=True):
                    self._text_vars["bad_len"].set("Ping Success - Unexpected")
                else:
                    self._text_vars["bad_len"].set("Ping Fail - Expected")
        except Exception as ex:
            self._text_vars["bad_len"].set("{}".format(ex))

    def ping_cmd(self):
        """
        Command handler for the "Ping" button, sends a Ping message to the
        Battery Box and processes the response reporting success or failure
        :return: N/A
        """
        self._text_vars["ping"].set("Pinging...")
        self._entries["ping"].update()

        try:
            with BbSerialMsgInterface(self._text_vars["com_port"].get(), DEFAULT_BAUD_RATE) as bbsi:
                if bbsi.send_ping():
                    self._text_vars["ping"].set("Ping Success")
                else:
                    self._text_vars["ping"].set("Ping Fail")
        except Exception as ex:
            self._text_vars["ping"].set("{}".format(ex))

    def get_sw_ver_cmd(self):
        """
        Command handler for the "Get Software Version" button, sends a Get Software Version
        request to the Battery Box and processes the response reporting the
        received software version if the request is successful or an appropriate fault message
        :return: N/A
        """
        self._text_vars["get_sw_version"].set("Reading Sw Version...")
        self._entries["get_sw_version"].update()

        try:
            with BbSerialMsgInterface(self._text_vars["com_port"].get(), DEFAULT_BAUD_RATE) as bbsi:
                result, sw_ver_info = bbsi.get_software_version()
                if result:
                    self._text_vars["get_sw_version"].set("{}.{}.{}:{}".format(sw_ver_info.sw_major,
                                                                               sw_ver_info.sw_minor,
                                                                               sw_ver_info.sw_patch,
                                                                               sw_ver_info.sw_build))
                else:
                    self._text_vars["get_sw_version"].set("Sw Version Read Fail")
        except Exception as ex:
            self._text_vars["get_sw_version"].set("{}".format(ex))

    def get_batt_params_cmd(self):
        """
        Starts/stops polling the dynamic and static battery parameters
        :return: N/A
        """
        if not self._polling_batt_parameters.is_set():
            self._buttons["get_battery_parameters"]["text"] = "Stop Polling..."

            t = Thread(target=self.poll_batt_parameters)
            t.start()
            self._polling_batt_parameters.set()
        else:
            self._buttons["get_battery_parameters"]["text"] = tk.DISABLED
            self._buttons["get_battery_parameters"]["text"] = "Stopping..."
            self._polling_batt_parameters.clear()

    def poll_batt_parameters(self):
        """
        Thread that handles polling dynamic and static battery parameters
        :return: N/A
        """
        self._entries["get_battery_parameters"]["state"] = tk.NORMAL
        self._entries["get_battery_parameters"].delete("1.0", "end")
        self._entries["get_battery_parameters"].insert(tk.INSERT, "Reading Battery Parameters...")
        self._entries["get_battery_parameters"].update()
        self._entries["get_battery_parameters"]["state"] = tk.DISABLED

        try:
            with BbSerialMsgInterface(self._text_vars["com_port"].get(), DEFAULT_BAUD_RATE) as bbsi:
                get_dynamic_battery_count_pass = 0
                get_dynamic_battery_count_fail = 0
                get_static_battery_count_pass = 0
                get_static_battery_count_fail = 0
                while self._polling_batt_parameters.is_set():
                    time.sleep(0.5)
                    result1, bdp = bbsi.get_dynamic_battery_parameters()
                    result2, bsp = bbsi.get_static_battery_parameters()

                    if result1 and result2:
                        self._entries["get_battery_parameters"]["state"] = tk.NORMAL
                        batt_param_str = \
                            self.BATT_PARAMS_STR.format(
                                bsp.battery_1a_serial_no, bsp.battery_1a_design_capacity,
                                bsp.battery_1b_serial_no, bsp.battery_1b_design_capacity,
                                bsp.battery_2a_serial_no, bsp.battery_2a_design_capacity,
                                bsp.battery_2b_serial_no, bsp.battery_2b_design_capacity,
                                bdp.battery_1a_voltage, bdp.battery_1a_current, bdp.battery_1a_state_of_charge,
                                bdp.battery_1a_temperature,bdp.battery_1a_remaining_energy,
                                bdp.battery_1b_voltage, bdp.battery_1b_current, bdp.battery_1b_state_of_charge,
                                bdp.battery_1b_temperature, bdp.battery_1b_remaining_energy,
                                bdp.battery_2a_voltage, bdp.battery_2a_current, bdp.battery_2a_state_of_charge,
                                bdp.battery_2a_temperature, bdp.battery_2a_remaining_energy,
                                bdp.battery_2b_voltage, bdp.battery_2b_current, bdp.battery_2b_state_of_charge,
                                bdp.battery_2b_temperature, bdp.battery_2b_remaining_energy,
                                bdp.battery_1a_status.error_code, bdp.battery_1a_status.fully_discharged,
                                bdp.battery_1a_status.fully_charged, bdp.battery_1a_status.discharging,
                                bdp.battery_1a_status.initialised, bdp.battery_1a_status.remaining_time,
                                bdp.battery_1a_status.remaining_capacity, bdp.battery_1a_status.terminate_discharge,
                                bdp.battery_1a_status.over_temperature, bdp.battery_1a_status.terminate_charge,
                                bdp.battery_1a_status.over_charged, bdp.battery_1b_status.error_code,
                                bdp.battery_1b_status.fully_discharged, bdp.battery_1b_status.fully_charged,
                                bdp.battery_1b_status.discharging, bdp.battery_1b_status.initialised,
                                bdp.battery_1b_status.remaining_time, bdp.battery_1b_status.remaining_capacity,
                                bdp.battery_1b_status.terminate_discharge, bdp.battery_1b_status.over_temperature,
                                bdp.battery_1b_status.terminate_charge, bdp.battery_1b_status.over_charged,
                                bdp.battery_2a_status.error_code, bdp.battery_2a_status.fully_discharged,
                                bdp.battery_2a_status.fully_charged, bdp.battery_2a_status.discharging,
                                bdp.battery_2a_status.initialised, bdp.battery_2a_status.remaining_time,
                                bdp.battery_2a_status.remaining_capacity, bdp.battery_2a_status.terminate_discharge,
                                bdp.battery_2a_status.over_temperature, bdp.battery_2a_status.terminate_charge,
                                bdp.battery_2a_status.over_charged, bdp.battery_2b_status.error_code,
                                bdp.battery_2b_status.fully_discharged, bdp.battery_2b_status.fully_charged,
                                bdp.battery_2b_status.discharging, bdp.battery_2b_status.initialised,
                                bdp.battery_2b_status.remaining_time, bdp.battery_2b_status.remaining_capacity,
                                bdp.battery_2b_status.terminate_discharge, bdp.battery_2b_status.over_temperature,
                                bdp.battery_2b_status.terminate_charge, bdp.battery_2b_status.over_charged)
                        self._entries["get_battery_parameters"].delete("1.0", "end")
                        self._entries["get_battery_parameters"].insert(tk.INSERT, batt_param_str)
                    else:
                        self._entries["get_battery_parameters"]["state"] = tk.NORMAL
                        self._entries["get_battery_parameters"].delete("1.0", "end")
                        self._entries["get_battery_parameters"].insert(tk.INSERT, "Battery Parameter Read Fail")
                        # self._entries["get_battery_parameters"].insert(tk.INSERT, self.TEST_STR)

                    if result1:
                        get_dynamic_battery_count_pass += 1
                    else:
                        get_dynamic_battery_count_fail += 1

                    if result2:
                        get_static_battery_count_pass += 1
                    else:
                        get_static_battery_count_fail += 1

                    self._entries["get_battery_parameters"].insert(
                        tk.INSERT, "\n\nGet Dynamic Pass:\t{}\n"
                                   "Get Dynamic Fail:\t{}\n"
                                   "Get Static Pass:\t{}\n"
                                   "Get Static Fail:\t{}\n".format(get_dynamic_battery_count_pass,
                                                                   get_dynamic_battery_count_fail,
                                                                   get_static_battery_count_pass,
                                                                   get_static_battery_count_fail))
                    self._entries["get_battery_parameters"]["state"] = tk.DISABLED

        except Exception as ex:
            self._entries["get_battery_parameters"]["state"] = tk.NORMAL
            self._entries["get_battery_parameters"].delete("1.0", "end")
            self._entries["get_battery_parameters"].insert(tk.INSERT, "{}".format(ex))
            self._entries["get_battery_parameters"]["state"] = tk.DISABLED

        self._buttons["get_battery_parameters"]["state"] = tk.ACTIVE
        self._buttons["get_battery_parameters"]["text"] = "Poll Battery Parameters"
        self._polling_batt_parameters.clear()


# -----------------------------------------------------------------------------
# FUNCTIONS#
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = BbTestGui()
    the_gui.run()


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level DEBUG to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main()
