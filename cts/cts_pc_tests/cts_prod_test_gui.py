#!/usr/bin/env python3
"""
Production test GUI for:

- KT-000-0206-00 K-CEMA Integrated CTS Digital Board

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
import re
import sys
from threading import Thread, Event
import time
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
import tkinter as tk
from queue import Queue

# Third-party imports -----------------------------------------------
import pyvisa
from signal_generator_marconi_202x import SUPPORTED_MODELS as MACRCONI_202X_SUPPORTED_MODELS
from signal_generator_keysight_n5x import SUPPORTED_MODELS as KEYSIGHT_N5X_SUPPORTED_MODELS
from signal_generator import instantiate_visa_sig_gen_class
from visa_test_equipment import VisaTestEquipment

# Our own imports -------------------------------------------------
from cts_prod_test import CtsProdTest, CtsProdTestInfo

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_NO = "KT-956-0264-00"
SW_NAME = "K-CEMA Integrated CTS Production Test GUI"
SW_VERSION = "V1.1.1"
SUPPORTED_SIG_GENS = MACRCONI_202X_SUPPORTED_MODELS + KEYSIGHT_N5X_SUPPORTED_MODELS
CONFIG_FILENAME = "cts_prod_test_config.json"
DEFAULT_CONFIG_DATA = {
    "default_values": {
        "psu_com_port": "",
        "test_jig_com_port": "",
        "digital_board_com_port": "",
        "csm_hostname": "",
        "assy_rev_no": "",
        "assy_serial_no": "",
        "assy_build_batch_no": "",
        "assy_type": ""
    },
    "input_files": {
        "micro_test_fw": "",
        "micro_operational_fw": "",
        "csm_platform_test_scripts": "",
        "cts_ant_s2p_file": ""
    },
    "digital_board_tests_to_run": [
        {"test_name": "power_supply_on", "run_test": True},
        {"test_name": "set_hw_config_info", "run_test": True},
        {"test_name": "program_micro_test_fw", "run_test": True},
        {"test_name": "board_adc_test", "run_test": True},
        {"test_name": "board_temp_sensor_test", "run_test": True},
        {"test_name": "board_mac_address_test", "run_test": True},
        {"test_name": "board_ping_test", "run_test": True},
        {"test_name": "board_pps_test", "run_test": True},
        {"test_name": "board_loop_back_test", "run_test": True},
        {"test_name": "board_if_path_test", "run_test": False},
        {"test_name": "board_if_path_test_auto", "run_test": True},
        {"test_name": "program_micro_operational_fw", "run_test": True},
        {"test_name": "power_supply_off", "run_test": True}
    ],
    "test_parameters": {
        "logging_level": "INFO",
        "results_folder": "./test_results",
        "cts_hostname":  "cts-000000.local",
    },
    "signal_generator_parameters": {
        "if_916_5_mhz_dbm": 0.0,
        "if_2310_mhz_dbm": 0.0,
        "if_2355_mhz_dbm": 0.0
    },
    "exe_paths": {
        "segger_jlink_win32": "",
        "segger_jlink_win64": ""
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


class ProgressDialog(simpledialog.SimpleDialog):
    def __init__(self, master, text='', title=None, class_=None):
        super().__init__(master=master, text=text, title=title, class_=class_)
        self.default = None
        self.cancel = None 
        self._bar = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self._bar.pack(expand=True, fill=tk.X, side=tk.BOTTOM)
        self._queue = Queue()
        self.root.after(200, self._update)

    def set_progress(self, value):
        self._queue.put(value)

    def _update(self):
        while self._queue.qsize():
            try:
                self._bar['value'] = self._queue.get(0)
            except Queue.Empty:
                pass
        self.root.after(200, self._update)


class CtsProdTestGui:
    """
    Tkinter GUI application class, all the functionality needed to create, update
    and interact with the GUI window are in this class.
    """
    _ICON_FILE = "kirintec_logo.ico"
    _DIGITAL_BOARD_NO = "KT-000-0206-00"
    _TEST_TYPE = ["Digital Board"]

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
            "psu_com_port": tk.Label(self._label_frame, text="PSU COM Port:"),
            "test_jig_com_port": tk.Label(self._label_frame, text="Test Jig COM Port:"),
            "digital_board_com_port": tk.Label(self._label_frame, text="Digital Board COM Port:"),
            "sig_gen_": tk.Label(self._label_frame, text="Signal Generator:"),
            "csm_hostname": tk.Label(self._label_frame, text="CSM Hostname:"),
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
            "psu_com_port": tk.StringVar(),
            "test_jig_com_port": tk.StringVar(),
            "digital_board_com_port": tk.StringVar(),
            "sig_gen": tk.StringVar(),
            "csm_hostname": tk.StringVar(),
            "assy_type": tk.StringVar(),
            "assy_rev_no": tk.StringVar(),
            "assy_serial_no": tk.StringVar(),
            "assy_build_batch_no": tk.StringVar(),
            "test_result": tk.StringVar()
        }

        for key in self._text_vars:
            self._text_vars[key].set(self._config_data.get("default_values", {}).get(key, ""))
        if self._text_vars["assy_type"].get() not in self._TEST_TYPE:
            self._text_vars["assy_type"].set("Digital Board")
        self._text_vars["test_result"].set("N/A")

        self._sig_gens = self.find_sig_gens()
        if len(self._sig_gens) > 0:
            self._text_vars["sig_gen"].set(self._sig_gens[0])

        # Set up action item widgets associated with the labels
        self._action_frame = self._window
        self._actions = {
            "psu_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["psu_com_port"]),
            "test_jig_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["test_jig_com_port"]),
            "digital_board_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["digital_board_com_port"]),
            "sig_gen": tk.OptionMenu(self._action_frame, self._text_vars["sig_gen"], self._sig_gens),
            "csm_hostname": tk.Entry(self._action_frame, textvariable=self._text_vars["csm_hostname"]),
            "assy_type": tk.OptionMenu(self._action_frame, self._text_vars["assy_type"], *self._TEST_TYPE, command=self.assy_type_cmd),
            "assy_rev_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_rev_no"]),
            "assy_serial_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_serial_no"]),
            "assy_build_batch_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_build_batch_no"]),
            "run_test":  tk.Button(self._action_frame, text="Start", width=20, command=self.run_test),
            "test_result": tk.Entry(self._action_frame, textvariable=self._text_vars["test_result"],
                                    state="readonly", readonlybackground="white"),
            "test_status": ScrolledText(self._action_frame, height=24, width=100,)
        }

        # Make the test_status Scrolled Text read only whilst allowing CTRL-C
        self._actions["test_status"].bind("<Key>", lambda e: self.test_status_ctrl_events(e))

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
            self._window.iconbitmap(default=self._ICON_FILE)

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

    def test_status_ctrl_events(self, event):
        if event.state == 12 and event.keysym == 'c':
            return None
        elif event.state == 12 and event.keysym == 'a':
            self._actions["test_status"].tag_add("start", "1.0", "end")
            return None
        else:
            return "break"

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
        if assy_type == "Digital Board":
            self._actions["psu_com_port"].configure(state="normal")
            self._actions["test_jig_com_port"].configure(state="normal")
            self._actions["digital_board_com_port"].configure(state="normal")
            self._actions["sig_gen"].configure(state="normal")
            self._actions["csm_hostname"].configure(state="disabled")
            pass
        elif assy_type == "Assembly (CSM)":
            self._actions["psu_com_port"].configure(state="normal")
            self._actions["test_jig_com_port"].configure(state="disabled")
            self._actions["digital_board_com_port"].configure(state="disabled")
            self._actions["sig_gen"].configure(state="normal")
            self._actions["csm_hostname"].configure(state="normal")

    def find_sig_gens(self):
        """
        Creates a list of available supported VISA Signal Generator addresses.
        :return list of detected Signal Generators supported by the application :type list of String objects
        """
        ret_val = []
        resource_manager = pyvisa.ResourceManager()
        pb = ProgressDialog(self._window, text="Searching for Signal Generators...", title="Search Progress")

        def _do_find():
            resources = resource_manager.list_resources()
            for i, resource in enumerate(resources):
                try:
                    with VisaTestEquipment(resource)as s:
                        if s.initialise_device(SUPPORTED_SIG_GENS):
                            ret_val.append("{} {} [{}]".format(s.manufacturer, s.model, resource))
                except:
                    pass
                pb.set_progress(((i + 1) * 100) / len(resources))
            pb.done(0)

        t = Thread(target=_do_find)
        t.start()
        pb.go()

        return ret_val

    def run_test(self):
        """
        Handles the Run (Stop) Test button which is used to start and stop test execution
        :return: N/A
        """

        if not self._test_running.is_set():
            self._actions["run_test"]["text"] = "Stop"

            test_info = CtsProdTestInfo()

            # Pull-in text box and option menu information
            test_info.psu_com_port = self._text_vars["psu_com_port"].get()
            test_info.test_jig_com_port = self._text_vars["test_jig_com_port"].get()
            test_info.digital_board_com_port = self._text_vars["digital_board_com_port"].get()
            test_info.csm_hostname = self._text_vars["csm_hostname"].get()
            test_info.assy_rev_no = self._text_vars["assy_rev_no"].get()
            test_info.assy_serial_no = self._text_vars["assy_serial_no"].get()
            test_info.assy_build_batch_no = self._text_vars["assy_build_batch_no"].get()

            sig_gen_resource_name = re.findall("\[(.*)]", self._text_vars["sig_gen"].get())
            if len(sig_gen_resource_name) > 0:
                sig_gen_resource_name = sig_gen_resource_name[-1]
            else:
                sig_gen_resource_name = ""
            test_info.sig_gen_resource_name = sig_gen_resource_name

            # RF Calibration Data
            test_info.if_916_5_mhz_dbm = self._config_data.get("signal_generator_parameters", {}).get("if_916_5_mhz_dbm", 0.0)
            test_info.if_2310_mhz_dbm = self._config_data.get("signal_generator_parameters", {}).get("if_2310_mhz_dbm", 0.0)
            test_info.if_2355_mhz_dbm = self._config_data.get("signal_generator_parameters", {}).get("if_2355_mhz_dbm", 0.0)

            # Input files
            test_info.micro_test_fw = self._config_data.get("input_files", {}).get("micro_test_fw", "")
            test_info.micro_operational_fw = self._config_data.get("input_files", {}).get("micro_operational_fw", "")
            test_info.csm_platform_test_scripts = self._config_data.get("input_files", {}).get("csm_platform_test_scripts", "")
            test_info.cts_ant_s2p_file = self._config_data.get("input_files", {}).get("cts_ant_s2p_file", "")

            # Exe paths
            exe_paths = self._config_data.get("exe_paths", {})
            test_info.segger_jlink_win64 = exe_paths.get("segger_jlink_win64", "")
            test_info.iperf3 = exe_paths.get("iperf3", "")
            test_info.cygwin1_dll = exe_paths.get("cygwin1_dll", "")

            # Build the list of test cases to run
            if self._text_vars["assy_type"].get() == "Digital Board":
                test_info.assy_type = self._DIGITAL_BOARD_NO
                test_info.hostname = self._config_data.get("test_parameters", {}).get("cts_hostname", "")

                for test in self._config_data.get("digital_board_tests_to_run"):
                    setattr(test_info, test.get("test_name"), test.get("run_test", False))
            elif self._text_vars["assy_type"].get() == "Assembly (CSM)":
                test_info.assy_type = self._DIGITAL_BOARD_NO
                test_info.hostname = self._config_data.get("test_parameters", {}).get("cts_hostname", "")

                for test in self._config_data.get("digital_board_tests_to_run"):
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
        :param test_info: :type CtsProdTestInfo
        :return:
        """
        if type(test_info) is not CtsProdTestInfo:
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
            # Create a CTS Production Test instance
            with CtsProdTest(test_info.psu_com_port, test_info.test_jig_com_port,
                             test_info.digital_board_com_port, test_info.hostname,
                             test_info.segger_jlink_win32 if test_info.segger_jlink_win32 != "" else None,
                             test_info.segger_jlink_win64 if test_info.segger_jlink_win64 != "" else None) as cpt:
                for test_case in test_info.cts_test_case_list:
                    if not self._test_running.is_set():
                        break

                    log.debug("{} - {}".format(test_case, getattr(test_info, test_case, False)))

                    if getattr(test_info, test_case, False):
                        if test_case == "set_hw_config_info":
                            ret_val = cpt.set_hw_config_info(test_info.assy_rev_no,
                                                             test_info.assy_serial_no,
                                                             test_info.assy_build_batch_no) and ret_val
                        elif test_case == "program_micro_test_fw":
                            ret_val = cpt.program_micro(test_info.micro_test_fw) and ret_val
                        elif test_case == "program_micro_operational_fw":
                            ret_val = cpt.program_micro(test_info.micro_operational_fw) and ret_val
                        elif test_case in ["board_if_path_test_auto"]:
                            sig_gen = instantiate_visa_sig_gen_class(test_info.sig_gen_resource_name)
                            ret_val = getattr(cpt, test_case)(sig_gen,
                                                              test_info.if_916_5_mhz_dbm,
                                                              test_info.if_2310_mhz_dbm,
                                                              test_info.if_2355_mhz_dbm) and ret_val
                        elif test_case in ["board_if_path_test"]:
                            ret_val = getattr(cpt, test_case)(self.instruction_dialog) and ret_val
                        elif test_case in []:
                            ret_val = getattr(cpt, test_case)(self.yesno_check_dialog) and ret_val
                        elif test_case in []:
                            ret_val = getattr(cpt, test_case)(self.instruction_dialog,
                                                              self.yesno_check_dialog) and ret_val
                        else:
                            ret_val = getattr(cpt, test_case)() and ret_val

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
    the_gui = CtsProdTestGui()
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
