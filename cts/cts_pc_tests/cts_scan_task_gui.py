#!/usr/bin/env python3
"""
San Task GUI for the K-CEMA Integrated CTS (Confidence Test Set)

"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
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
import io
import json
import logging
import os
import sys
from threading import Thread, Event
import time
from tkinter import messagebox
import tkinter as tk

# Third-party imports -----------------------------------------------
from tk_tools import Led

# Our own imports -------------------------------------------------
from cts_serial_msg_intf import CtsSerialMsgInterface, CtsSerialTcpMsgInterface, \
    CtsScanMode, CtsScanStatus, CtsMsgId, CtsMsgPayloadLen

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_NO = "KT-956-0264-01"
SW_NAME = "K-CEMA Integrated CTS Scan Task GUI"
SW_VERSION = "v1.0.0"
CONFIG_FILENAME = "cts_scan_task_config.json"
DEFAULT_CONFIG_DATA = {
    "default_values": {
        "interface_type": "",
        "interface_address": "",
        "centre_freq_khz": "",
        "target_power_dbm": "",
        "tolerance_db": "",
        "dwell_time_ms": ""
    }
}
MAX_RF_DETECTOR_POWER_DBM = 30.0
RF_DETECTOR_RANGE_DB = 70.0


# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class CtsScanTaskGui:
    """
    Tkinter GUI application class, all the functionality needed to create, update
    and interact with the GUI window are in this class.
    """
    _ICON_FILE = "kirintec_logo.ico"

    def __init__(self):
        """
        Class constructor, initialises the Tkinter GUI window and adds all the widgets to it.

        All of the text boxes on the GUI window have associated tk.StringVar variables which
        are used to get/set the displayed text.  Text boxes used solely for reporting purposes
        are set as read-only
        """
        self._config_data = {}
        self.load_config_data()

        # Set up the Tkinter window
        self._window = tk.Tk()
        self.initialise_window()

        # Set up frames to group the widgets
        self._frame_holder = self._window
        self._frames = {
            "interface": tk.LabelFrame(self._frame_holder, borderwidth=3, relief=tk.GROOVE, text="Interface"),
            "scan_parameters": tk.LabelFrame(self._frame_holder, borderwidth=3, relief=tk.GROOVE, text="Scan Parameters"),
            "rf_power_meter": tk.LabelFrame(self._frame_holder, borderwidth=3, relief=tk.GROOVE, text="RF Power (dBm)")
        }

        # Set up the labels which will appear in the left hand column
        self._labels = {
            "interface_type": tk.Label(self._frames["interface"], text="Interface Type:"),
            "interface_address": tk.Label(self._frames["interface"], text="Interface Address:"),
            "centre_freq_khz": tk.Label(self._frames["scan_parameters"], text="Centre Frequency (kHz):"),
            "target_power_dbm": tk.Label(self._frames["scan_parameters"], text="Target RF Power (dBm):"),
            "tolerance_db": tk.Label(self._frames["scan_parameters"], text="Tolerance (dB):"),
            "rx_att_db": tk.Label(self._frames["scan_parameters"], text="Rx Attenuation (dB):"),
            "dwell_time_ms": tk.Label(self._frames["scan_parameters"], text="Dwell Time (ms):"),
            "run_scan": tk.Label(self._frames["scan_parameters"], text="Run Scan:"),
            "scan_count": tk.Label(self._frames["scan_parameters"], text="Scan Count:")
        }

        # Set up string variables for use with Tkinter widgets
        self._text_vars = {
            "interface_type": tk.StringVar(),
            "interface_address": tk.StringVar(),
            "centre_freq_khz": tk.StringVar(),
            "target_power_dbm": tk.StringVar(),
            "tolerance_db": tk.StringVar(),
            "rx_att_db": tk.StringVar(),
            "dwell_time_ms": tk.StringVar(),
            "rf_power_dbm": tk.StringVar(),
            "scan_count": tk.StringVar()
        }

        for key in self._text_vars:
            self._text_vars[key].set(self._config_data.get("default_values", {}).get(key, ""))

        # Set up action item widgets associated with the labels
        self._actions = {
            "interface_type": tk.OptionMenu(self._frames["interface"], self._text_vars["interface_type"],
                                            *["Serial", "Network"]),
            "interface_address": tk.Entry(self._frames["interface"], textvariable=self._text_vars["interface_address"]),
            "centre_freq_khz": tk.Entry(self._frames["scan_parameters"], textvariable=self._text_vars["centre_freq_khz"]),
            "target_power_dbm": tk.Entry(self._frames["scan_parameters"], textvariable=self._text_vars["target_power_dbm"]),
            "tolerance_db": tk.Entry(self._frames["scan_parameters"], textvariable=self._text_vars["tolerance_db"]),
            "rx_att_db": tk.OptionMenu(self._frames["scan_parameters"], self._text_vars["rx_att_db"],
                                       *[x for x in range(0, 32)], command=self.redraw_rf_power_meter_scale),
            "dwell_time_ms": tk.Entry(self._frames["scan_parameters"], textvariable=self._text_vars["dwell_time_ms"]),
            "run_scan":  tk.Button(self._frames["scan_parameters"], text="Start", width=20, command=self.run_scan),
            "scan_count": tk.Entry(self._frames["scan_parameters"], textvariable=self._text_vars["scan_count"],
                                   state="readonly"),
            "rf_power": tk.Entry(self._frames["rf_power_meter"], textvariable=self._text_vars["rf_power_dbm"],
                                 state="readonly"),
        }

        # Assemble the main window
        for i, key in enumerate(self._frames):
            self._frames[key].grid(column=1, row=i + 1, padx=5, pady=5, sticky="nw")

        # Assemble the Interface Frame
        self._labels["interface_type"].grid(column=1, row=1, padx=5, pady=5, sticky="ne")
        self._actions["interface_type"].grid(column=2, row=1, padx=5, pady=5, sticky="nw")
        self._labels["interface_address"].grid(column=1, row=2, padx=5, pady=5, sticky="ne")
        self._actions["interface_address"].grid(column=2, row=2, padx=5, pady=5, sticky="nw")

        # Assemble the Scan Task Frame
        for i, key in enumerate(self._labels):
            if self._labels[key].master.winfo_id() == self._frames["scan_parameters"].winfo_id():
                self._labels[key].grid(column=1, row=i + 1, padx=5, pady=5, sticky="ne")

        for i, key in enumerate(self._actions):
            if self._actions[key].master.winfo_id() == self._frames["scan_parameters"].winfo_id():
                self._actions[key].grid(column=2, row=i + 1, padx=5, pady=5, sticky="nw")

        self._text_vars["rx_att_db"].set(str(31))

        # Assemble the RF Power Meter Frame
        min_rf_power_dbm = MAX_RF_DETECTOR_POWER_DBM - RF_DETECTOR_RANGE_DB - \
            (31 - int(self._text_vars["rx_att_db"].get()))
        self._actions["rf_power"].grid(column=int(RF_DETECTOR_RANGE_DB / 5.0) + 3, row=2, padx=5, pady=5)
        for i in range(0, int(RF_DETECTOR_RANGE_DB / 5.0) + 1):
            self._labels["rf_power_value_{}".format(i)] = tk.Label(self._frames["rf_power_meter"],
                                                                   text="{:.1f}".format(min_rf_power_dbm + (i * 5)))
            self._labels["rf_power_value_{}".format(i)].grid(column=i + 2, row=1)
            self._actions["power_meter_led_{}".format(i)] = Led(self._frames["rf_power_meter"], size=40)
            self._actions["power_meter_led_{}".format(i)].grid(column=i + 2, row=2)

        self._scan_running = Event()
        self._scan_thread = Thread()

    def redraw_rf_power_meter_scale(self, rx_att_db):
        """
        Redraw the RF Power Meter scale based on the selected Rx Attenuation, Target RF Power and Tolerance
        :return: N/A
        """
        min_rf_power_dbm = MAX_RF_DETECTOR_POWER_DBM - RF_DETECTOR_RANGE_DB - (31 - int(rx_att_db))
        for i in range(0, int(RF_DETECTOR_RANGE_DB / 5.0) + 1):
            self._labels["rf_power_value_{}".format(i)]["text"] = "{:.1f}".format(min_rf_power_dbm + (i * 5))
        self._window.update()
        self._window.update_idletasks()

    def load_config_data(self):
        """
        If the JSON config file exists attempt to load config dta from it, otherwise create
        the JSON file with default values.
        @return:
        """
        config_data_loaded = True

        if os.path.exists(CONFIG_FILENAME):
            with open(CONFIG_FILENAME, 'r') as f:
                try:
                    self._config_data = json.load(f)
                    # TODO: Use JSON schema to do more robust checking
                except Exception as ex:
                    log.critical("Failed to load JSON config data! - {}".format(ex))
                    config_data_loaded = False
        else:
            config_data_loaded = False

        # Failed to load config data from JSON file so write file with default values
        if not config_data_loaded:
            log.debug("Creating default JSON configuration data file")
            with open(CONFIG_FILENAME, 'w') as f:
                self._config_data = DEFAULT_CONFIG_DATA
                json.dump(self._config_data, f, indent=4)

    def run(self):
        """
        Tkinter GUI application main loop
        :return:
        """
        self._window.mainloop()

    def initialise_window(self):
        """
        Set up the Tkinter window title and overall geometry
        :return: N/A
        """
        self._window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._window.title("{} - {} - {}".format(SW_NO, SW_NAME, SW_VERSION))
        self._window.geometry("850x470")
        if os.path.isfile(self._ICON_FILE):
            self._window.iconbitmap(default=self._ICON_FILE)

    def on_closing(self):
        if tk.messagebox.askyesno("Exit", "Do you want to quit the application?"):
            self._actions["run_scan"]["state"] = tk.DISABLED
            self._actions["run_scan"]["text"] = "Exiting..."

            # Terminate the test thread
            self._scan_running.clear()
            while self._scan_thread.is_alive():
                self._window.update()
                time.sleep(0.001)

            self._window.destroy()

    def run_scan(self):
        """
        Handles the Run (Stop) Scan button which is used to start and stop scan execution
        :return: N/A
        """

        if not self._scan_running.is_set():
            self._actions["run_scan"]["text"] = "Stop"
            self._scan_thread = Thread(target=self.run_scan_thread)
            self._scan_thread.start()
            self._scan_running.set()
        else:
            self._actions["run_scan"]["state"] = tk.DISABLED
            self._actions["run_scan"]["text"] = "Stopping..."
            self._scan_running.clear()

    def run_scan_thread(self):
        """
        Executes scan thread.
        :return: N/A
        """
        scan_count = 0
        self._text_vars["scan_count"].set(scan_count)

        try:
            interface_type = self._text_vars["interface_type"].get()
            interface_address = self._text_vars["interface_address"].get()

            while True:
                with CtsSerialMsgInterface(interface_address) if interface_type == "Serial" else \
                        CtsSerialTcpMsgInterface(interface_address) as c:
                    if c.send_start_scan(mode=CtsScanMode.ACTIVE_MONITOR,
                                         freq_khz=int(self._text_vars["centre_freq_khz"].get()),
                                         dwell_time_ms=int(self._text_vars["dwell_time_ms"].get()),
                                         tx_atten_0db5=0,
                                         rx_atten_0db5=int(float(self._text_vars["rx_att_db"].get()) * 2.0)):
                        while True:
                            cmd_pass, rx_msg = c.get_command(CtsMsgId.GET_SCAN_STATUS, CtsMsgPayloadLen.GET_SCAN_STATUS)
                            if cmd_pass:
                                pl_version, status, rf_det_pow_0dbm1, rf_det_mv, rem_dwell_time_ms = \
                                    c.unpack_get_scan_status_response(rx_msg)
                                if status == CtsScanStatus.IDLE.value:
                                    rf_det_power_dbm = float(rf_det_pow_0dbm1) / 10.0
                                    self._text_vars["rf_power_dbm"].set("{:.1f}".format(rf_det_power_dbm))

                                    target_power_dbm = float(self._text_vars["target_power_dbm"].get())
                                    tolerance_db = float(self._text_vars["tolerance_db"].get())
                                    target_power_lo_dbm = target_power_dbm - tolerance_db
                                    target_power_hi_dbm = target_power_dbm + tolerance_db

                                    for i in range(0, int(RF_DETECTOR_RANGE_DB / 5.0) + 1):
                                        led_high_power_dbm = float(self._labels["rf_power_value_{}".format(i)]["text"])
                                        led_low_power_dbm = float(led_high_power_dbm) - 5.0

                                        # Try to set the colour and turn the LED on first
                                        led_processed = False
                                        if rf_det_power_dbm > led_low_power_dbm:
                                            if led_high_power_dbm < target_power_lo_dbm:
                                                self._actions["power_meter_led_{}".format(i)].to_green(True)
                                                led_processed = True
                                            elif (led_low_power_dbm >= target_power_hi_dbm) and \
                                                    (rf_det_power_dbm > target_power_hi_dbm):
                                                self._actions["power_meter_led_{}".format(i)].to_red(True)
                                                led_processed = True
                                            elif (led_low_power_dbm < target_power_hi_dbm) and \
                                                    (rf_det_power_dbm >= target_power_lo_dbm):
                                                self._actions["power_meter_led_{}".format(i)].to_yellow(True)
                                                led_processed = True

                                        # If the LED wasn't turned just set the colour
                                        if not led_processed:
                                            if led_high_power_dbm < target_power_lo_dbm:
                                                self._actions["power_meter_led_{}".format(i)].to_green()
                                            elif led_low_power_dbm >= target_power_hi_dbm:
                                                self._actions["power_meter_led_{}".format(i)].to_red()
                                            else:
                                                self._actions["power_meter_led_{}".format(i)].to_yellow()

                                    scan_count += 1
                                    self._text_vars["scan_count"].set(scan_count)
                                    break

                    if not self._scan_running.is_set():
                        break
        except Exception as ex:
            tk.messagebox.showerror("Error!", "{}".format(ex))

        self._actions["run_scan"]["state"] = tk.ACTIVE
        self._actions["run_scan"]["text"] = "Start"
        self._scan_running.clear()


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = CtsScanTaskGui()
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
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S", stream=sys.stdout)

    main()
