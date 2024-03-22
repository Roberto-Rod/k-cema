#!/usr/bin/env python3
"""
Tkinter GUI application for production testing the Active Backplane board,
KT-000-0139-00.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Kirintec
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
from datetime import datetime
import io
import json
import logging
import os
import sys
from threading import Thread, Event
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import tkinter as tk

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from active_backplane_prod_test import AbProdTestInfo, AbProdTest

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_NO = "KT-956-0241-00"
SW_NAME = "K-CEMA Active Backplane Production Test GUI"
SW_VERSION = "V1.0.3"
CONFIG_FILENAME = "active_backplane_prod_test_config.json"
DEFAULT_CONFIG_DATA = {
  "default_values": {
    "test_jig_com_port": "COMx",
    "psu_com_port": "COMx",
    "managed_sw_com_port": "COMx",
    "board_under_test_com_port": "COMx",
    "assy_rev_no": "",
    "assy_serial_no": "",
    "assy_build_batch_no": ""
  },
  "sw_binaries": {
    "micro_fw": "",
    "gbe_switch_fw": ""
  },
  "tests_to_run": [
    {"test_name": "main_power_supply_test", "run_test":  True},
    {"test_name": "set_hw_config_info", "run_test": True},
    {"test_name": "program_micro", "run_test": True},
    {"test_name": "program_gbe_sw", "run_test": True},
    {"test_name": "get_sw_versions", "run_test": True},
    {"test_name": "built_in_test", "run_test": True},
    {"test_name": "discrete_test", "run_test": True},
    {"test_name": "uart_test", "run_test": True},
    {"test_name": "gbe_sw_connection_test", "run_test": True},
    {"test_name": "qsgmii_test", "run_test": True},
    {"test_name": "get_micro_mac_ip_address", "run_test": True},
    {"test_name": "get_switch_mac_address", "run_test": True}
  ],
  "test_parameters": {
    "gbe_conn_test_duration_s": 30,
    "gbe_conn_test_uports": [1, 2, 3, 7, 8],
    "gbe_conn_test_uports_full_list": [1, 2, 3, 7, 8],
    "qsgmii_test_count": 20,
    "logging_level": "INFO"
  },
  "exe_paths": {
    "segger_jlink_win32": "",
    "segger_jlink_win64": "",
    "asix_up_win32": "",
    "asix_up_win64": "",
    "iperf3": ""
  }
}

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class StdRedirect(io.StringIO):
    """
    Utility class to redirect stdout/stderr to a Tkinter text control
    """
    def __init__(self, text_ctrl):
        """ Class constructor """
        self.output = text_ctrl
        super().__init__()

    def write(self, string):
        self.output.insert(tk.END, string)
        self.output.yview(tk.END)

    def flush(self):
        pass


class AbProdTestGui:
    """
    Tkinter GUI application class, all the functionality and methods needed
    to create, update and interact with the GUI window are in this class
    """
    _ICON_FILE = "kirintec_logo.ico"
    _HW_INFO_NUM_ITEMS = 3
    _ASSEMBLY_NO = "KT-000-0139-00"
    _HW_INFO_LABELS = ["Assembly Revision No:", "Assembly Serial No:", "Assembly Build Batch No:"]
    _HW_INFO_KEYS = ["assy_rev_no", "assy_serial_no", "assy_build_batch_no"]

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

        self._config_data = {}
        self.load_config_data()

        self._window = tk.Tk()
        self.initialise_window()
        row = 0

        # Row 1 - Blank
        row += 1

        # Row 2
        row += 2

        # Test Jig COM Port Widgets
        self._tj_com_port_lbl = tk.Label(self._window, text="Test Jig Com Port:").grid(column=1, row=row, sticky="nw",
                                                                                       padx=5, pady=5)
        self._tj_com_port_var = tk.StringVar()
        self._tj_com_port_var.set(self._config_data.get("default_values", {}).get("test_jig_com_port", ""))
        self._tj_com_port_txt = tk.Entry(self._window, textvariable=self._tj_com_port_var)
        self._tj_com_port_txt.grid(column=2, row=row, sticky="nw")

        # Row 3
        row += 1

        # PSU COM Port Widgets
        self._psu_com_port_lbl = tk.Label(self._window, text="Tenma PSU Com Port:").grid(column=1, row=row, sticky="nw",
                                                                                         padx=5, pady=5)
        self._psu_com_port_var = tk.StringVar()
        self._psu_com_port_var.set(self._config_data.get("default_values", {}).get("psu_com_port", ""))
        self._psu_com_port_txt = tk.Entry(self._window, textvariable=self._psu_com_port_var)
        self._psu_com_port_txt.grid(column=2, row=row, sticky="nw")

        # Row 4
        row += 1

        # Managed Switch COM Port Widgets
        self._ms_com_port_lbl = tk.Label(self._window, text="Managed Switch Com Port:").grid(column=1, row=row,
                                                                                             sticky="nw", padx=5,
                                                                                             pady=5)
        self._ms_com_port_var = tk.StringVar()
        self._ms_com_port_var.set(self._config_data.get("default_values", {}).get("managed_sw_com_port", ""))
        self._ms_com_port_txt = tk.Entry(self._window, textvariable=self._ms_com_port_var)
        self._ms_com_port_txt.grid(column=2, row=row, sticky="nw")

        # Row 5
        row += 1

        # Managed Switch COM Port Widgets
        self._but_com_port_lbl = tk.Label(self._window, text="Board Under Test Com Port:").grid(column=1, row=row,
                                                                                                sticky="nw", padx=5,
                                                                                                pady=5)
        self._but_com_port_var = tk.StringVar()
        self._but_com_port_var.set(self._config_data.get("default_values", {}).get("board_under_test_com_port", ""))
        self._but_com_port_txt = tk.Entry(self._window, textvariable=self._but_com_port_var)
        self._but_com_port_txt.grid(column=2, row=row, sticky="nw")

        # Row 6
        row += 1

        # Hw Information Widgets
        self._hw_info_str_var = []
        self._hw_info_txt_entry = []
        self._hw_info_label = []

        for i in range(0, self._HW_INFO_NUM_ITEMS):
            str_var = tk.StringVar()
            self._hw_info_str_var.append(str_var)

            lbl_var = tk.Label(self._window, text=self._HW_INFO_LABELS[i]).grid(column=1, row=row, sticky="nw",
                                                                                padx=5, pady=5)
            self._hw_info_label.append(lbl_var)

            txt_var = tk.Entry(self._window, textvariable=self._hw_info_str_var[i])
            self._hw_info_str_var[i].set(self._config_data.get("default_values", {}).get(self._HW_INFO_KEYS[i], ""))
            txt_var.grid(column=2, row=row, sticky="nw")
            self._hw_info_txt_entry.append(txt_var)

            row += 1
        row -= 1

        # Row 9
        row += 1

        # Run Test Widgets and variables
        self._run_test_lbl = tk.Label(self._window, text="Run Test:").grid(column=1, row=row, sticky="nw",
                                                                           padx=5, pady=5)
        self._run_test_btn = tk.Button(self._window, text="Start", width=20, command=self.run_test)
        self._run_test_btn.grid(column=2, row=row, sticky="nw")

        # Row 10
        row += 1

        # Test Result Widgets
        self._test_status_lbl = tk.Label(self._window, text="Test Result").grid(column=1, row=row, sticky="nw",
                                                                                padx=5, pady=5)
        self._test_result_var = tk.StringVar()
        self._test_result_var.set("N/A")
        self._test_result_txt = tk.Entry(self._window, textvariable=self._test_result_var)
        self._test_result_txt.grid(column=2, row=row, sticky="nw")
        self._test_result_txt["readonlybackground"] = "white"
        self._test_result_txt["state"] = "readonly"

        # Row 11
        row += 1

        # Test Status Widgets
        self._test_status_lbl = tk.Label(self._window, text="Test Status:").grid(column=1, row=row, sticky="nw",
                                                                                 padx=5, pady=5)
        self._test_status_txt = ScrolledText(self._window, height=29, width=100)
        self._test_status_txt.grid(column=2, row=row, sticky="nw")

        sys.stdout = StdRedirect(self._test_status_txt)

        self._logging_level = \
            getattr(logging, self._config_data.get("test_parameters", {}).get("logging_level", logging.INFO))
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout,
                            level=self._logging_level, force=True)

        self._test_running = Event()
        self._test_thread = Thread()

    def load_config_data(self):
        """
        If the JSON config file exists attempt to load config dta from it,
        otherwise create the JSON file with default values.
        @return: N/A
        """
        config_data_loaded = True

        if os.path.exists(CONFIG_FILENAME):
            with open(CONFIG_FILENAME, 'r') as f:
                try:
                    self._config_data = json.load(f)
                    # TODO: Use JSON schema to do more robust checking
                except Exception as ex:
                    log.info("INFO: Failed to load JSON config data! - {}".format(ex))
                    config_data_loaded = False
        else:
            config_data_loaded = False

        # Failed to load config data from JSON file so write file with default values
        if not config_data_loaded:
            log.info("INFO: Creating default JSON configuration data file")
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
        self._window.geometry("1024x768")
        if os.path.isfile(self._ICON_FILE):
            self._window.iconbitmap(self._ICON_FILE)

    def on_closing(self):
        if tk.messagebox.askyesno("Exit", "Do you want to quit the application?"):
            self._run_test_btn["state"] = tk.DISABLED
            self._run_test_btn["text"] = "Exiting..."

            # Terminate the test thread
            self._test_running.clear()
            while self._test_thread.is_alive():
                self._window.update()

            self._window.destroy()

    def run_test(self):
        """
        Handle the run test button used to start/stop the test.
        @return: N/A
        """

        if not self._test_running.is_set():
            self._run_test_btn["text"] = "Stop"

            test_info = AbProdTestInfo()

            # Pull-in text box information
            test_info.tj_com_port = self._tj_com_port_var.get()
            test_info.psu_com_port = self._psu_com_port_var.get()
            test_info.tpl_sw_com_port = self._ms_com_port_var.get()
            test_info.but_com_port = self._but_com_port_var.get()
            test_info.assy_rev_no = self._hw_info_str_var[0].get()
            test_info.assy_serial_no = self._hw_info_str_var[1].get()
            test_info.assy_build_batch_no = self._hw_info_str_var[2].get()

            # Firmware files
            sw_binaries = self._config_data.get("sw_binaries", {})
            test_info.micro_fw_bin_file = sw_binaries.get("micro_fw", "")
            test_info.gbe_sw_bin_file = sw_binaries.get("gbe_switch_fw", "")

            # Exe paths
            exe_paths = self._config_data.get("exe_paths", {})
            test_info.segger_jlink_win64 = exe_paths.get("segger_jlink_win64", "")
            test_info.asix_up_win32 = exe_paths.get("asix_up_win32", "")
            test_info.asix_up_win64 = exe_paths.get("asix_up_win64", "")
            test_info.iperf3 = exe_paths.get("iperf3", "")
            test_info.cygwin1_dll = exe_paths.get("cygwin1_dll", "")

            # Build the list of test cases to run
            for test in self._config_data.get("tests_to_run"):
                setattr(test_info, test.get("test_name"), test.get("run_test", False))

            self._test_thread = Thread(target=self.run_test_thread, args=(test_info,))
            self._test_thread.start()
            self._test_running.set()
        else:
            self._run_test_btn["state"] = tk.DISABLED
            self._run_test_btn["text"] = "Stopping..."
            self._test_running.clear()

    def run_test_thread(self, test_info):
        """

        :param test_info: :type AbProdTestInfo
        :return:
        """
        if type(test_info) is not AbProdTestInfo:
            raise ValueError("test_info type is invalid!")

        self._test_result_var.set("Test Running...")
        self._test_result_txt["foreground"] = "black"
        self._test_result_txt["readonlybackground"] = "white"
        self._test_result_txt.update()
        self._test_status_txt.delete("1.0", "end")

        if not os.path.exists(r".\test_results"):
            os.mkdir("test_results")

        log_file_name = r".\test_results\KT-000-0139-00_{}_{}.txt".format(test_info.assy_serial_no,
                                                                          datetime.now().strftime("%Y%m%d%H%M%S"))
        log_file = logging.FileHandler(log_file_name, mode='w')
        log_file.setLevel(self._logging_level)
        log_file.setFormatter(logging.Formatter("%(asctime)s: %(message)s", datefmt="%H:%M:%S"))
        logging.getLogger().addHandler(log_file)

        log.info("INFO - {} - {} - {}".format(SW_NO, SW_NAME, SW_VERSION))
        log.info("INFO - Board Serial No:\t{}".format(test_info.assy_serial_no))
        log.info("INFO - Board Revision No:\t{}".format(test_info.assy_rev_no))
        log.info("INFO - Board Batch No:\t{}".format(test_info.assy_build_batch_no))

        ret_val = True

        try:
            # Create an Active Backplane Production Test instance
            with AbProdTest(test_info.tj_com_port, test_info.psu_com_port,
                            test_info.tpl_sw_com_port, test_info.but_com_port,
                            test_info.segger_jlink_win32 if test_info.segger_jlink_win32 != "" else None,
                            test_info.segger_jlink_win64 if test_info.segger_jlink_win64 != "" else None,
                            test_info.asix_up_win32 if test_info.asix_up_win32 != "" else None,
                            test_info.asix_up_win64 if test_info.asix_up_win64 != "" else None,
                            test_info.iperf3 if test_info.iperf3 != "" else None,
                            test_info.cygwin1_dll if test_info.cygwin1_dll != "" else None) as abpt:

                for test_case in test_info.test_case_list:
                    if not self._test_running.is_set():
                        break

                    if getattr(test_info, test_case, False):
                        if test_case == "set_hw_config_info":
                            ret_val = abpt.set_hw_config_info(test_info.assy_rev_no,
                                                              test_info.assy_serial_no,
                                                              test_info.assy_build_batch_no) and ret_val
                        elif test_case == "program_micro":
                            ret_val = abpt.program_micro(test_info.micro_fw_bin_file) and ret_val
                        elif test_case == "gbe_sw_connection_test":
                            duration_s = self._config_data.get("test_parameters", {}).get("gbe_conn_test_duration_s",
                                                                                          30)
                            test_ports = self._config_data.get("test_parameters", {}).get("gbe_conn_test_uports", [])
                            for uport in test_ports:
                                power_on = (uport == test_ports[0])
                                power_off = (uport == test_ports[-1])
                                ret_val = abpt.gbe_sw_connection_test(uport, duration_s,
                                                                      power_on, power_off) and ret_val
                                if not self._test_running.is_set():
                                    break
                        elif test_case == "qsgmii_test":
                            for i in range(1, self._config_data.get("test_parameters", {}).get("qsgmii_test_count",
                                                                                               20)+1):
                                ret_val = abpt.qsgmii_test(i) and ret_val
                                if not self._test_running.is_set():
                                    break
                        elif test_case == "program_gbe_sw":
                            ret_val = abpt.program_gbe_sw(test_info.gbe_sw_bin_file) and ret_val
                        else:
                            ret_val = getattr(abpt, test_case)() and ret_val

                if ret_val and self._test_running.is_set():
                    log.info("PASS - Overall Test Result")
                    self._test_result_var.set("PASS")
                    self._test_result_txt["foreground"] = "white"
                    self._test_result_txt["readonlybackground"] = "green"
                elif not self._test_running.is_set():
                    log.info("INFO - Test Aborted")
                    self._test_result_var.set("Test Aborted")
                    self._test_result_txt["foreground"] = "black"
                    self._test_result_txt["readonlybackground"] = "white"
                else:
                    log.info("FAIL - Overall Test Result")
                    self._test_result_var.set("FAIL")
                    self._test_result_txt["foreground"] = "white"
                    self._test_result_txt["readonlybackground"] = "red"
                self._test_result_txt.update()

        except Exception as ex:
            log.critical("Test Execution Error - {}".format(ex))
            self._test_result_var.set("Test Execution Error")
            self._test_result_txt["foreground"] = "white"

            self._test_result_txt["readonlybackground"] = "red"

        logging.getLogger().removeHandler(log_file)
        # os.chmod(log_file_name, os.S_IREAD | os.S_IRGRP | os.S_IROTH)

        self._run_test_btn["state"] = tk.ACTIVE
        self._run_test_btn["text"] = "Start"
        self._test_running.clear()


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = AbProdTestGui()
    the_gui.run()


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    # fmt = "%(asctime)s: %(message)s"
    # Set logging level DEBUG to see detailed information
    # logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S", stream=sys.stdout)

    main()
