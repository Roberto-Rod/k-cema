#!/usr/bin/env python3
"""
Production test GUI for:

- KT-000-0198-00 K-CEMA Display RCU Motherboard
- KT-000-0199-00 K-CEMA Fill Device Motherboard
- KT-950-0429-00 K-CEMA Display RCU Unit
- KT-950-0430-00 K-CEMA Fill Device Unit

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
from datetime import datetime
import io
import json
import logging
import os
import sys
from threading import Thread, Event
import time
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import tkinter as tk

# Third-party imports -----------------------------------------------


# Our own imports -------------------------------------------------
from drcu_fd_prod_test import DrcuProdTest, DrcuProdTestInfo, FdProdTest, FdProdTestInfo, DrcuFdUnitTypes

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_NO = "KT-956-0257-00"
SW_NAME = "K-CEMA DRCU and FD Production Test GUI"
SW_VERSION = "V1.2.1"
CONFIG_FILENAME = "drcu_fd_prod_test_config.json"
DEFAULT_CONFIG_DATA = {
    "default_values": {
        "test_jig_com_port": "",
        "csm_com_port": "",
        "fd_com_port": "",
        "soc_console_com_port": "",
        "assy_rev_no": "",
        "assy_serial_no": "",
        "assy_build_batch_no": "",
        "assy_type": ""
    },
    "sw_binaries": {
        "micro_test_fw": "",
        "micro_operational_fw": "",
        "platform_test_scripts": ""
    },
    "drcu_board_tests_to_run": [
        {"test_name": "offboard_supply_rail_test", "run_test": True},
        {"test_name": "program_micro_test_fw", "run_test": True},
        {"test_name": "poe_pd_pse_type_test", "run_test": True},
        {"test_name": "set_hw_config_info", "run_test": True},
        {"test_name": "batt_temp_sensor_test", "run_test": True},
        {"test_name": "board_pps_test", "run_test": True},
        {"test_name": "xchange_reset_test", "run_test": True},
        {"test_name": "board_case_switch_test", "run_test": True},
        {"test_name": "board_light_sensor_test", "run_test": True},
        {"test_name": "program_micro_operational_fw", "run_test": True},
        {"test_name": "som_bring_up", "run_test": True},
        {"test_name": "enable_som", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "som_supply_rail_test", "run_test": True},
        {"test_name": "som_ad7415_temp_sensor_test", "run_test": True},
        {"test_name": "som_nvme_test", "run_test": True},
        {"test_name": "gbe_sw_connection_test", "run_test": True},
        {"test_name": "gbe_sw_bandwidth_test", "run_test": True},
        {"test_name": "poe_pse_test", "run_test": True},
        {"test_name": "rtc_test", "run_test": True},
        {"test_name": "board_buzzer_test", "run_test": True},
        {"test_name": "function_button_test", "run_test": True},
        {"test_name": "discrete_op_test", "run_test": True},
        {"test_name": "display_backlight_test", "run_test": True},
        {"test_name": "keypad_button_test", "run_test": True},
        {"test_name": "keypad_led_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True},
        {"test_name": "disable_som", "run_test": True}
    ],
    "drcu_unit_tests_to_run": [
        {"test_name": "unit_som_bring_up", "run_test": True},
        {"test_name": "unit_set_config_info", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "function_button_test", "run_test": True},
        {"test_name": "discrete_op_test", "run_test": True},
        {"test_name": "display_backlight_test", "run_test": True},
        {"test_name": "keypad_button_test", "run_test": True},
        {"test_name": "unit_buzzer_test", "run_test": True},
        {"test_name": "unit_pps_test", "run_test": True},
        {"test_name": "check_for_sd_card", "run_test": True},
        {"test_name": "gbe_sw_connection_test", "run_test": True},
        {"test_name": "gbe_sw_bandwidth_test", "run_test": True},
        {"test_name": "unit_tamper_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True}
    ],
    "fd_board_tests_to_run": [
        {"test_name": "program_micro_test_fw", "run_test": True},
        {"test_name": "poe_pd_pse_type_test", "run_test": True},
        {"test_name": "set_hw_config_info", "run_test": True},
        {"test_name": "batt_temp_sensor_test", "run_test": True},
        {"test_name": "pvbat_monitor_test", "run_test": True},
        {"test_name": "board_case_switch_test", "run_test": True},
        {"test_name": "board_light_sensor_test", "run_test": True},
        {"test_name": "program_micro_operational_fw", "run_test": True},
        {"test_name": "som_bring_up", "run_test": True},
        {"test_name": "enable_som", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "som_supply_rail_test", "run_test": True},
        {"test_name": "som_ad7415_temp_sensor_test", "run_test": True},
        {"test_name": "som_nvme_test", "run_test": True},
        {"test_name": "gbe_bandwidth_test", "run_test": True},
        {"test_name": "fd_uart_test", "run_test": True},
        {"test_name": "rtc_test", "run_test": True},
        {"test_name": "keypad_button_test", "run_test": True},
        {"test_name": "keypad_led_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True},
        {"test_name": "disable_som", "run_test": True}
    ],
    "fd_unit_tests_to_run": [
        {"test_name": "unit_som_bring_up", "run_test": True},
        {"test_name": "unit_set_config_info", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "keypad_button_test", "run_test": True},
        {"test_name": "keypad_led_test", "run_test": True},
        {"test_name": "check_for_sd_card", "run_test": True},
        {"test_name": "gbe_bandwidth_test", "run_test": True},
        {"test_name": "fd_uart_test", "run_test": True},
        {"test_name": "unit_tamper_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True}
    ],
    "test_parameters": {
        "gbe_conn_test_duration_s": 30,
        "logging_level": "INFO",
        "results_folder": "./test_results",
        "drcu_hostname":  "rcu-000000.local",
        "fd_hostname":  "kfd-000000.local",
        "rpi4_ip6_address": ""
    },
    "serial_port_aliases": {
        "gbe_switch_serial_port": "/dev/ttymxc2"
    },
    "exe_paths": {
        "segger_jlink_win32": "",
        "segger_jlink_win64": "",
        "iperf3": "",
        "cygwin1_dll": ""
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


class CsmProdTestGui:
    """
    Tkinter GUI application class, all the functionality needed to create, update
    and interact with the GUI window are in this class.
    """
    _ICON_FILE = "kirintec_logo.ico"
    _DRCU_MOTHERBOARD_NO = "KT-000-0198-00"
    _DRCU_ASSEMBLY_NO = "KT-950-0429-00"
    _FD_MOTHERBOARD_NO = "KT-000-0199-00"
    _FD_ASSEMBLY_NO = "KT-950-0431-00"
    _TEST_TYPE = ["DRCU Motherboard", "DRCU Unit", "FD Motherboard", "FD Unit"]

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

        # Set up the Tkinter window
        self._window = tk.Tk()
        self.initialise_window()

        # Set up the labels which will appear in the left hand column
        self._label_frame = self._window
        self._labels = {
            "test_jig_com_port": tk.Label(self._label_frame, text="Test Jig COM Port:"),
            "csm_com_port": tk.Label(self._label_frame, text="DRCU CSM COM Port:"),
            "fd_com_port": tk.Label(self._label_frame, text="FD COM Port:"),
            "soc_console_com_port": tk.Label(self._label_frame, text="SoC Console COM Port:"),
            "assy_type": tk.Label(self._label_frame, text="Assembly Type:"),
            "assy_rev_no": tk.Label(self._label_frame, text="Assembly Revision No:"),
            "assy_serial_no": tk.Label(self._label_frame, text="Assembly Serial No:"),
            "assy_build_batch_no": tk.Label(self._label_frame, text="Assembly Build Batch No:"),
            "run_test": tk.Label(self._label_frame, text="Run Test:"),
            "test_result": tk.Label(self._label_frame, text="Test Result:"),
            "test_status": tk.Label(self._label_frame, text="Test Status:")
        }

        # Set up string variables for use with Tkinter widgets
        self._text_vars = {
            "test_jig_com_port": tk.StringVar(),
            "csm_com_port": tk.StringVar(),
            "fd_com_port": tk.StringVar(),
            "soc_console_com_port": tk.StringVar(),
            "assy_type": tk.StringVar(),
            "assy_rev_no": tk.StringVar(),
            "assy_serial_no": tk.StringVar(),
            "assy_build_batch_no": tk.StringVar(),
            "test_result": tk.StringVar()
        }

        for key in self._text_vars:
            self._text_vars[key].set(self._config_data.get("default_values", {}).get(key, ""))
        if self._text_vars["assy_type"].get() not in self._TEST_TYPE:
            self._text_vars["assy_type"].set("DRCU Motherboard")
        self._text_vars["test_result"].set("N/A")

        # Set up action item widgets associated with the labels
        self._action_frame = self._window
        self._actions = {
            "test_jig_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["test_jig_com_port"]),
            "csm_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["csm_com_port"]),
            "fd_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["fd_com_port"]),
            "soc_console_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["soc_console_com_port"]),
            "assy_type": tk.OptionMenu(self._action_frame, self._text_vars["assy_type"], *self._TEST_TYPE,
                                       command=self.assy_type_cmd),
            "assy_rev_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_rev_no"]),
            "assy_serial_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_serial_no"]),
            "assy_build_batch_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_build_batch_no"]),
            "run_test":  tk.Button(self._action_frame, text="Start", width=20, command=self.run_test),
            "test_result": tk.Entry(self._action_frame, textvariable=self._text_vars["test_result"],
                                    state="readonly", readonlybackground="white"),
            "test_status": ScrolledText(self._action_frame, height=24, width=100)
        }
        # Assemble the main window
        for i, key in enumerate(self._labels):
            self._labels[key].grid(column=1, row=i + 1, padx=5, pady=5, sticky="ne")

        for i, key in enumerate(self._actions):
            self._actions[key].grid(column=2, row=i + 1, padx=5, pady=5, sticky="nw")

        self.assy_type_cmd(self._text_vars["assy_type"].get())

        # Set up sys.stdout/logging to re-direct to the Test Status ScrolledText widget
        redir = StdRedirect(self._actions["test_status"])
        sys.stdout = redir

        self._logging_level = \
            getattr(logging, self._config_data.get("test_parameters", {}).get("logging_level", logging.INFO))
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout,
                            level=self._logging_level, force=True)

        self._test_running = Event()
        self._test_thread = Thread()

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
        self._window.geometry("1024x768")
        if os.path.isfile(self._ICON_FILE):
            self._window.iconbitmap(self._ICON_FILE)

    def on_closing(self):
        if tk.messagebox.askyesno("Exit", "Do you want to quit the application?"):
            self._actions["run_test"]["state"] = tk.DISABLED
            self._actions["run_test"]["text"] = "Exiting..."

            # Terminate the test thread
            self._test_running.clear()
            while self._test_thread.is_alive():
                self._window.update()
                time.sleep(0.001)

            self._window.destroy()

    @staticmethod
    def instruction_dialog(msg):
        """
        Show an information dialogue with the specified string
        :param msg: message to display in the dialog
        :return: N/A
        """
        tk.messagebox.showinfo("Instruction", msg)

    @staticmethod
    def yesno_check_dialog(msg):
        """
        Show a Yes/No dialogue with the specified string
        :param msg: message to display in the dialog
        :return: N/A
        """
        return tk.messagebox.askyesno("Manual Check", msg)

    def assy_type_cmd(self, assy_type):
        """
        Disable/enable text boxes based on selected assembly type to test.
        :return: N/A
        """
        if assy_type == "DRCU Motherboard":
            self._actions["test_jig_com_port"].configure(state="normal")
            self._actions["csm_com_port"].configure(state="normal")
            self._actions["fd_com_port"].configure(state="disabled")
            self._actions["soc_console_com_port"].configure(state="disabled")
            pass
        elif assy_type == "DRCU Unit":
            self._actions["test_jig_com_port"].configure(state="normal")
            self._actions["csm_com_port"].configure(state="normal")
            self._actions["fd_com_port"].configure(state="disabled")
            self._actions["soc_console_com_port"].configure(state="disabled")
        elif assy_type == "FD Motherboard":
            self._actions["test_jig_com_port"].configure(state="normal")
            self._actions["csm_com_port"].configure(state="disabled")
            self._actions["fd_com_port"].configure(state="normal")
            self._actions["soc_console_com_port"].configure(state="normal")
        elif assy_type == "FD Unit":
            self._actions["test_jig_com_port"].configure(state="disabled")
            self._actions["csm_com_port"].configure(state="disabled")
            self._actions["fd_com_port"].configure(state="normal")
            self._actions["soc_console_com_port"].configure(state="disabled")

    def run_test(self):
        """
        Handles the Run (Stop) Test button which is used to start and stop test execution
        @return: N/A
        """

        if not self._test_running.is_set():
            self._actions["run_test"]["text"] = "Stop"

            if self._text_vars["assy_type"].get() == "DRCU Motherboard" or \
                    self._text_vars["assy_type"].get() == "DRCU Unit":

                test_info = DrcuProdTestInfo()

                # Pull-in text box information
                test_info.test_jig_com_port = self._text_vars["test_jig_com_port"].get()
                test_info.csm_com_port = self._text_vars["csm_com_port"].get()
                test_info.assy_rev_no = self._text_vars["assy_rev_no"].get()
                test_info.assy_serial_no = self._text_vars["assy_serial_no"].get()
                test_info.assy_build_batch_no = self._text_vars["assy_build_batch_no"].get()

                # Firmware files
                test_info.micro_test_fw = self._config_data.get("sw_binaries", {}).get("micro_test_fw", "")
                test_info.micro_operational_fw = self._config_data.get("sw_binaries", {}).get("micro_operational_fw", "")
                test_info.platform_test_scripts = self._config_data.get("sw_binaries", {}).get("platform_test_scripts", "")

                # Exe paths
                exe_paths = self._config_data.get("exe_paths", {})
                test_info.segger_jlink_win64 = exe_paths.get("segger_jlink_win64", "")
                test_info.iperf3 = exe_paths.get("iperf3", "")
                test_info.cygwin1_dll = exe_paths.get("cygwin1_dll", "")

                # Build the list of test cases to run
                if self._text_vars["assy_type"].get() == "DRCU Motherboard":
                    test_info.assy_type = self._DRCU_MOTHERBOARD_NO
                    test_info.hostname = self._config_data.get("test_parameters", {}).get("drcu_hostname", "")

                    for test in self._config_data.get("drcu_board_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

                elif self._text_vars["assy_type"].get() == "DRCU Unit":
                    test_info.assy_type = self._DRCU_ASSEMBLY_NO
                    test_info.hostname = "rcu-{}.local".format(self._text_vars["assy_serial_no"].get())

                    for test in self._config_data.get("drcu_unit_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

            # elif self._text_vars["assy_type"].get() == "FD Motherboard" or \
            #        self._text_vars["assy_type"].get() == "FD Unit":
            else:

                test_info = FdProdTestInfo()

                # Pull-in text box information
                test_info.test_jig_com_port = self._text_vars["test_jig_com_port"].get()
                test_info.fd_com_port = self._text_vars["fd_com_port"].get()
                test_info.soc_console_com_port = self._text_vars["soc_console_com_port"].get()
                test_info.assy_rev_no = self._text_vars["assy_rev_no"].get()
                test_info.assy_serial_no = self._text_vars["assy_serial_no"].get()
                test_info.assy_build_batch_no = self._text_vars["assy_build_batch_no"].get()

                # Firmware files
                test_info.micro_test_fw = self._config_data.get("sw_binaries", {}).get("micro_test_fw", "")
                test_info.micro_operational_fw = self._config_data.get("sw_binaries", {}).get("micro_operational_fw",
                                                                                              "")
                test_info.platform_test_scripts = self._config_data.get("sw_binaries", {}).get("platform_test_scripts",
                                                                                               "")

                # Exe paths
                exe_paths = self._config_data.get("exe_paths", {})
                test_info.segger_jlink_win64 = exe_paths.get("segger_jlink_win64", "")
                test_info.iperf3 = exe_paths.get("iperf3", "")
                test_info.cygwin1_dll = exe_paths.get("cygwin1_dll", "")

                # Build the list of test cases to run
                if self._text_vars["assy_type"].get() == "FD Motherboard":
                    test_info.assy_type = self._FD_MOTHERBOARD_NO
                    test_info.hostname = self._config_data.get("test_parameters", {}).get("fd_hostname", "")

                    for test in self._config_data.get("fd_board_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

                elif self._text_vars["assy_type"].get() == "FD Unit":
                    test_info.assy_type = self._FD_ASSEMBLY_NO
                    test_info.hostname = "kfd-{}.local".format(self._text_vars["assy_serial_no"].get())

                    for test in self._config_data.get("fd_unit_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

            self._test_thread = Thread(target=self.run_test_thread, args=(test_info,))
            self._test_thread.start()
            self._test_running.set()
        else:
            self._actions["run_test"]["state"] = tk.DISABLED
            self._actions["run_test"]["text"] = "Stopping..."
            self._test_running.clear()

    def run_test_thread(self, test_info):
        """
        Executes test procedure thread, steps through enabled tests
        :param test_info: :type CsmProdTestInfo
        :return:
        """
        if type(test_info) is not DrcuProdTestInfo and type(test_info) is not FdProdTestInfo:
            raise ValueError("test_info type is invalid!")

        self._text_vars["test_result"].set("Test Running...")
        self._actions["test_result"]["foreground"] = "black"
        self._actions["test_result"]["readonlybackground"] = "white"
        self._actions["test_result"].update()
        self._actions["test_status"].delete("1.0", "end")

        if not os.path.exists(r".\test_results"):
            os.mkdir("test_results")

        log_filename = r"{}\{}_{}_{}.txt".format(self._config_data.get("test_parameters", {}).get("results_folder", ""),
                                                 test_info.assy_type, test_info.assy_serial_no,
                                                 datetime.now().strftime("%Y%m%d%H%M%S"))
        log_file = logging.FileHandler(log_filename, mode='w')
        log_file.setLevel(self._logging_level)
        log_file.setFormatter(logging.Formatter("%(asctime)s: %(message)s", datefmt="%H:%M:%S"))
        logging.getLogger().addHandler(log_file)

        log.info("INFO - {} - {} - {}".format(SW_NO, SW_NAME, SW_VERSION))
        log.info("INFO - Assembly No:\t{}".format(test_info.assy_type))
        log.info("INFO - Serial No:\t{}".format(test_info.assy_serial_no))
        log.info("INFO - Revision No:\t{}".format(test_info.assy_rev_no))
        log.info("INFO - Batch No:\t{}".format(test_info.assy_build_batch_no))

        ret_val = True

        try:
            if type(test_info) is DrcuProdTestInfo:
                # Create a DRCU Production Test instance
                with DrcuProdTest(test_info.test_jig_com_port, test_info.csm_com_port, test_info.hostname,
                                  self._config_data.get("serial_port_aliases", {}).get("gbe_switch_serial_port"),
                                  test_info.segger_jlink_win32 if test_info.segger_jlink_win32 != "" else None,
                                  test_info.segger_jlink_win64 if test_info.segger_jlink_win64 != "" else None,
                                  test_info.iperf3 if test_info.iperf3 != "" else None,
                                  test_info.cygwin1_dll if test_info.cygwin1_dll != "" else None) as dpt:
                    for test_case in test_info.test_case_list:
                        if not self._test_running.is_set():
                            break

                        log.debug("{} - {}".format(test_case, getattr(test_info, test_case, False)))

                        if getattr(test_info, test_case, False):
                            if test_case == "set_hw_config_info":
                                ret_val = dpt.set_hw_config_info(test_info.assy_rev_no,
                                                                 test_info.assy_serial_no,
                                                                 test_info.assy_build_batch_no) and ret_val
                            elif test_case == "unit_set_config_info":
                                ret_val = dpt.unit_set_config_info(test_info.assy_type,
                                                                   test_info.assy_rev_no,
                                                                   test_info.assy_serial_no,
                                                                   test_info.assy_build_batch_no,
                                                                   test_info.platform_test_scripts,
                                                                   self.instruction_dialog,
                                                                   DrcuFdUnitTypes.DRCU) and ret_val
                            elif test_case == "gbe_sw_bandwidth_test":
                                dur_s = self._config_data.get("test_parameters", {}).get("gbe_conn_test_duration_s", 30)
                                rpi4_ip6_address = self._config_data.get("test_parameters", {}).get("rpi4_ip6_address",
                                                                                                    "")
                                ret_val = dpt.gbe_sw_bandwidth_test(dur_s, rpi4_ip6_address) and ret_val
                            elif test_case == "enable_som":
                                ret_val = dpt.enable_som(True) and ret_val
                            elif test_case == "disable_som":
                                ret_val = dpt.enable_som(False) and ret_val
                            elif test_case == "program_micro_test_fw":
                                ret_val = dpt.program_micro(test_info.micro_test_fw) and ret_val
                            elif test_case == "program_micro_operational_fw":
                                ret_val = dpt.program_micro(test_info.micro_operational_fw) and ret_val
                            elif test_case in ["discrete_op_test", "function_button_test", "keypad_button_test",
                                               "board_light_sensor_test", "board_case_switch_test"]:
                                ret_val = getattr(dpt, test_case)(self.instruction_dialog) and ret_val
                            elif test_case in ["som_bring_up"]:
                                ret_val = getattr(dpt, test_case)(self.instruction_dialog,
                                                                  DrcuFdUnitTypes.DRCU) and ret_val
                            elif test_case in ["unit_buzzer_test", "display_backlight_test"]:
                                ret_val = getattr(dpt, test_case)(self.yesno_check_dialog) and ret_val
                            elif test_case in ["keypad_led_test", "unit_pps_test"]:
                                ret_val = getattr(dpt, test_case)(self.instruction_dialog,
                                                                  self.yesno_check_dialog) and ret_val
                            elif test_case in ["unit_som_bring_up"]:
                                ret_val = getattr(dpt, test_case)(self.instruction_dialog,
                                                                  self.yesno_check_dialog,
                                                                  DrcuFdUnitTypes.DRCU) and ret_val
                            elif test_case == "copy_test_scripts_to_som":
                                ret_val = getattr(dpt, test_case)(test_info.platform_test_scripts) and ret_val
                            else:
                                ret_val = getattr(dpt, test_case)() and ret_val

            elif type(test_info) is FdProdTestInfo:
                # Create an FD Production Test instance
                with FdProdTest(test_info.test_jig_com_port, test_info.fd_com_port, test_info.soc_console_com_port,
                                test_info.hostname,
                                test_info.segger_jlink_win32 if test_info.segger_jlink_win32 != "" else None,
                                test_info.segger_jlink_win64 if test_info.segger_jlink_win64 != "" else None,
                                test_info.iperf3 if test_info.iperf3 != "" else None,
                                test_info.cygwin1_dll if test_info.cygwin1_dll != "" else None) as fpt:
                    for test_case in test_info.test_case_list:
                        if not self._test_running.is_set():
                            break

                        log.debug("{} - {}".format(test_case, getattr(test_info, test_case, False)))

                        if getattr(test_info, test_case, False):
                            if test_case == "set_hw_config_info":
                                ret_val = fpt.set_hw_config_info(test_info.assy_rev_no,
                                                                 test_info.assy_serial_no,
                                                                 test_info.assy_build_batch_no) and ret_val
                            elif test_case == "unit_set_config_info":
                                ret_val = fpt.unit_set_config_info(test_info.assy_type,
                                                                   test_info.assy_rev_no,
                                                                   test_info.assy_serial_no,
                                                                   test_info.assy_build_batch_no,
                                                                   test_info.platform_test_scripts,
                                                                   self.instruction_dialog,
                                                                   DrcuFdUnitTypes.FILL_DEVICE) and ret_val
                            elif test_case == "gbe_bandwidth_test":
                                dur_s = self._config_data.get("test_parameters", {}).get("gbe_conn_test_duration_s", 30)
                                ret_val = fpt.gbe_bandwidth_test(dur_s) and ret_val
                            elif test_case == "enable_som":
                                ret_val = fpt.enable_som(True) and ret_val
                            elif test_case == "disable_som":
                                ret_val = fpt.enable_som(False) and ret_val
                            elif test_case == "program_micro_test_fw":
                                ret_val = fpt.program_micro(test_info.micro_test_fw) and ret_val
                            elif test_case == "program_micro_operational_fw":
                                ret_val = fpt.program_micro(test_info.micro_operational_fw) and ret_val
                            elif test_case in ["keypad_button_test", "board_light_sensor_test",
                                               "board_case_switch_test"]:
                                ret_val = getattr(fpt, test_case)(self.instruction_dialog) and ret_val
                            elif test_case in ["som_bring_up"]:
                                ret_val = getattr(fpt, test_case)(self.instruction_dialog,
                                                                  DrcuFdUnitTypes.FILL_DEVICE) and ret_val
                            elif test_case in ["keypad_led_test"]:
                                ret_val = getattr(fpt, test_case)(self.instruction_dialog,
                                                                  self.yesno_check_dialog) and ret_val
                            elif test_case in ["unit_som_bring_up"]:
                                ret_val = getattr(fpt, test_case)(self.instruction_dialog,
                                                                  self.yesno_check_dialog,
                                                                  DrcuFdUnitTypes.FILL_DEVICE) and ret_val
                            elif test_case == "copy_test_scripts_to_som":
                                ret_val = getattr(fpt, test_case)(test_info.platform_test_scripts) and ret_val
                            else:
                                ret_val = getattr(fpt, test_case)() and ret_val
            else:
                log.critical("Unknown Test Type!")
                ret_val = False

            log.info("")
            if ret_val and self._test_running.is_set():
                log.info("PASS - Overall Test Result")
                self._text_vars["test_result"].set("PASS")
                self._actions["test_result"]["foreground"] = "white"
                self._actions["test_result"]["readonlybackground"] = "green"
            elif not self._test_running.is_set():
                log.info("INFO - Test Aborted")
                self._text_vars["test_result"].set("TEST ABORTED")
                self._actions["test_result"]["foreground"] = "black"
                self._actions["test_result"]["readonlybackground"] = "white"
            else:
                log.info("FAIL - Overall Test Result")
                self._text_vars["test_result"].set("FAIL")
                self._actions["test_result"]["foreground"] = "white"
                self._actions["test_result"]["readonlybackground"] = "red"
            self._actions["test_result"].update()

        except Exception as ex:
            log.critical("Test Environment Error - {}".format(ex))
            self._text_vars["test_result"].set("Test Environment Error")
            self._actions["test_result"]["foreground"] = "white"

            self._actions["test_result"]["readonlybackground"] = "red"

        logging.getLogger().removeHandler(log_file)
        # os.chmod(log_file_name, os.S_IREAD | os.S_IRGRP | os.S_IROTH)

        self._actions["run_test"]["state"] = tk.ACTIVE
        self._actions["run_test"]["text"] = "Start"
        self._test_running.clear()


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = CsmProdTestGui()
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
