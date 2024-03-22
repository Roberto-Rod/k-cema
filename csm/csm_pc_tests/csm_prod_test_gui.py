#!/usr/bin/env python3
"""
KT-000-0139- Active Backplane board Production Test.

Classes and functions implementing production test cases for the KT-000-0139-00
Active Backplane board.

Hardware/software compatibility:
- KT-000-0164-00 K-CEMA Active Backplane Test Interface Board

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


# Our own imports -------------------------------------------------
from csm_prod_test import CsmProdTest, CsmProdTestInfo, MpCsmProdTest, MpCsmProdTestInfo, UnitTypes

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_NO = "KT-956-0235-00"
SW_NAME = "K-CEMA Vehicle & Manpack CSM Production Test GUI"
SW_VERSION = "v2.3.1"
CONFIG_FILENAME = "csm_prod_test_config.json"
DEFAULT_CONFIG_DATA = {
    "default_values": {
        "test_jig_com_port": "",
        "psu_com_port": "",
        "managed_sw_com_port": "",
        "master_com_port": "",
        "rcu_com_port": "",
        "assy_rev_no": "",
        "assy_serial_no": "",
        "assy_build_batch_no": "",
        "assy_type": ""
    },
    "sw_binaries": {
        "zeroise_test_fpga": "",
        "zeroise_test_fw": "",
        "mp_zeroise_test_fw": "",
        "zeroise_operational_fw": "",
        "mp_zeroise_operational_fw": "",
        "platform_test_scripts": "",
        "gbe_switch_fw": "KT-956-0195-00.bin",
        "mp_gbe_switch_fw": "KT-956-0195-02.bin"
    },
    "board_tests_to_run": [
        {"test_name": "over_under_voltage_lockout_test", "run_test": True},
        {"test_name": "external_power_off_test", "run_test": True},
        {"test_name": "over_voltage_test", "run_test": True},
        {"test_name": "program_zeroise_test_fw", "run_test": True},
        {"test_name": "zeroise_psu_rail_test", "run_test": True},
        {"test_name": "battery_signal_test", "run_test": False},
        {"test_name": "rtc_test", "run_test": True},
        {"test_name": "case_switch_test", "run_test": True},
        {"test_name": "power_cable_detect_test", "run_test": True},
        {"test_name": "light_sensor_test", "run_test": True},
        {"test_name": "keypad_test", "run_test": True},
        {"test_name": "program_zeroise_fpga_test_image", "run_test": True},
        {"test_name": "zeroise_fpga_test", "run_test": True},
        {"test_name": "erase_zeroise_fpga_test_image", "run_test": True},
        {"test_name": "program_som", "run_test": True},
        {"test_name": "program_gbe_sw_fw", "run_test": True},
        {"test_name": "poe_pse_test", "run_test": False},
        {"test_name": "qsgmii_test", "run_test": True},
        {"test_name": "power_up_board_linux", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "set_config_info", "run_test": True},
        {"test_name": "gbe_sw_connection_test", "run_test": True},
        {"test_name": "som_built_in_test", "run_test": True},
        {"test_name": "external_pps_test", "run_test": True},
        {"test_name": "internal_pps_test", "run_test": True},
        {"test_name": "rf_mute_test", "run_test": True},
        {"test_name": "power_off_override_test", "run_test": True},
        {"test_name": "ptp_phy_test", "run_test": True},
        {"test_name": "uart_test", "run_test": True},
        {"test_name": "tmp442_test", "run_test": True},
        {"test_name": "ad7415_test", "run_test": True},
        {"test_name": "eui48_id_test", "run_test": True},
        {"test_name": "print_som_mac_ipv4_address", "run_test": True},
        {"test_name": "super_flash_mount_test", "run_test": False},
        {"test_name": "gps_lock_test", "run_test": True},
        {"test_name": "tcxo_adjust_test", "run_test": True},
        {"test_name": "som_i2c_device_detect_test", "run_test": True},
        {"test_name": "som_eia422_intf_test", "run_test": True},
        {"test_name": "buzzer_test", "run_test": True},
        {"test_name": "pb_controller_irq_test", "run_test": True},
        {"test_name": "gbe_chassis_gnd_test", "run_test": True},
        {"test_name": "power_kill_test", "run_test": True},
        {"test_name": "program_zeroise_operational_fw", "run_test": True},
        {"test_name": "expansion_slot_1_test", "run_test": True},
        {"test_name": "expansion_slot_2_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True},
        {"test_name": "power_supply_off", "run_test": True}
    ],
    "mp_board_tests_to_run": [
        {"test_name": "over_under_voltage_lockout_test", "run_test": True},
        {"test_name": "external_power_off_test", "run_test": True},
        {"test_name": "pb_controller_supply_test", "run_test": True},
        {"test_name": "over_voltage_test", "run_test": True},
        {"test_name": "ntm_pfi_test", "run_test": True},
        {"test_name": "set_ntm_hw_config_info", "run_test": True},
        {"test_name": "board_fan_test", "run_test": True},
        {"test_name": "program_zeroise_test_fw", "run_test": True},
        {"test_name": "zeroise_psu_rail_test", "run_test": True},
        {"test_name": "battery_signal_test", "run_test": False},
        {"test_name": "rtc_test", "run_test": True},
        {"test_name": "case_switch_test", "run_test": True},
        {"test_name": "light_sensor_test", "run_test": True},
        {"test_name": "keypad_test", "run_test": True},
        {"test_name": "program_zeroise_fpga_test_image", "run_test": True},
        {"test_name": "zeroise_fpga_test", "run_test": True},
        {"test_name": "erase_zeroise_fpga_test_image", "run_test": True},
        {"test_name": "program_som", "run_test": True},
        {"test_name": "program_gbe_sw_fw", "run_test": True},
        {"test_name": "qsgmii_test", "run_test": True},
        {"test_name": "power_up_board_linux", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "set_config_info", "run_test": True},
        {"test_name": "gbe_sw_connection_test", "run_test": True},
        {"test_name": "som_built_in_test", "run_test": True},
        {"test_name": "external_pps_test", "run_test": True},
        {"test_name": "internal_pps_test", "run_test": True},
        {"test_name": "rf_mute_test", "run_test": True},
        {"test_name": "ptp_phy_test", "run_test": True},
        {"test_name": "uart_test", "run_test": True},
        {"test_name": "tmp442_test", "run_test": True},
        {"test_name": "ad7415_test", "run_test": True},
        {"test_name": "eui48_id_test", "run_test": True},
        {"test_name": "print_som_mac_ipv4_address", "run_test": True},
        {"test_name": "super_flash_mount_test", "run_test": False},
        {"test_name": "gps_lock_test", "run_test": True},
        {"test_name": "tcxo_adjust_test", "run_test": True},
        {"test_name": "som_i2c_device_detect_test", "run_test": True},
        {"test_name": "som_eia422_intf_test", "run_test": True},
        {"test_name": "buzzer_test", "run_test": True},
        {"test_name": "pb_controller_irq_test", "run_test": True},
        {"test_name": "gbe_chassis_gnd_test", "run_test": False},
        {"test_name": "power_kill_test", "run_test": True},
        {"test_name": "program_zeroise_operational_fw", "run_test": True},
        {"test_name": "expansion_slot_1_test", "run_test": True},
        {"test_name": "expansion_slot_2_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True},
        {"test_name": "power_supply_off", "run_test": True}
    ],
    "unit_tests_to_run": [
        {"test_name": "external_power_off_test", "run_test": True},
        {"test_name": "unit_set_config_info", "run_test": True},
        {"test_name": "power_up_board_linux", "run_test": True},
        {"test_name": "copy_test_scripts_to_som", "run_test": True},
        {"test_name": "check_for_sd_card", "run_test": True},
        {"test_name": "unit_tamper_test", "run_test": True},
        {"test_name": "unit_keypad_test", "run_test": True},
        {"test_name": "unit_pb_controller_irq_test", "run_test": True},
        {"test_name": "unit_buzzer_test", "run_test": True},
        {"test_name": "unit_uart_test", "run_test": True},
        {"test_name": "gbe_sw_connection_test", "run_test": True},
        {"test_name": "external_pps_test", "run_test": True},
        {"test_name": "rf_mute_test", "run_test": True},
        {"test_name": "power_off_override_test", "run_test": True},
        {"test_name": "gps_lock_test", "run_test": True},
        {"test_name": "gbe_chassis_gnd_test", "run_test": True},
        {"test_name": "remove_test_scripts", "run_test": True},
        {"test_name": "power_supply_off", "run_test": True}
    ],
    "test_parameters": {
        "gbe_conn_test_duration_s": 30,
        "gbe_conn_test_uports": [3, 5, 8],
        "gbe_conn_test_uports_full_list": [3, 5, 8],
        "gbe_uport_2_test_switch_map": {1: 20, 2: 20, 3: 17, 5: 18, 8: 19, 9: 25, 10: 25},
        "mp_gbe_conn_test_uports": [1, 2, 4, 5, 6, 7, 9],
        "mp_gbe_conn_test_uports_full_list": [1, 2, 4, 5, 6, 7, 9],
        "mp_gbe_uport_2_test_switch_map": {1: 21, 2: 22, 4: 17, 5: 18, 6: 19, 7: 20, 9: 25, 10: 25},
        "qsgmii_test_count": 20,
        "logging_level": "INFO",
        "results_folder": "./test_results",
        "csm_hostname":  "csm-000000.local",
        "csm_username": "root",
        "rpi4_ip6_address": ""
    },
    "serial_port_aliases": {
        "console_serial_port": "/dev/ttyConsole",
        "zeroise_micro_serial_port": "/dev/ttyZerMicro",
        "csm_slave_serial_port": "/dev/ttyCSMSlave",
        "rcu_serial_port": "/dev/ttyRCU",
        "programming_serial_port": "/dev/ttyProg",
        "gnss1_serial_port": "/dev/ttyGNSS1",
        "gbe_switch_serial_port": "/dev/ttyEthSw",
        "exp_slot_1_serial_port": "/dev/ttyExp1",
        "exp_slot_2_serial_port": "/dev/ttyExp2"
    },
    "exe_paths": {
        "segger_jlink_win32": "",
        "segger_jlink_win64": "",
        "flash_pro": "",
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
    _CSM_MOTHERBOARD_NO = "KT-000-0140-00"
    _CSM_ASSEMBLY_NO = "KT-950-0351-00"
    _MP_CSM_MOTHERBOARD_NO = "KT-000-0180-00"
    _MP_KBAN_CSM_MOTHERBOARD_NO = "KT-000-0180-01"
    _TEST_TYPES = ["Vehicle Motherboard", "Vehicle Motherboard Part 1", "Vehicle Motherboard Part 2", "Vehicle Unit",
                   "Manpack Motherboard -00", "Manpack Motherboard -00 Part 1", "Manpack Motherboard -00 Part 2",
                   "Manpack Motherboard -01", "Manpack Motherboard -01 Part 1", "Manpack Motherboard -01 Part 2"]

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
            "psu_com_port": tk.Label(self._label_frame, text="Tenma PSU COM Port:"),
            "managed_sw_com_port": tk.Label(self._label_frame, text="Managed Switch COM Port:"),
            "master_com_port": tk.Label(self._label_frame, text="Master COM Port:"),
            "rcu_com_port": tk.Label(self._label_frame, text="RCU COM Port:"),
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
            "psu_com_port": tk.StringVar(),
            "managed_sw_com_port": tk.StringVar(),
            "master_com_port": tk.StringVar(),
            "rcu_com_port": tk.StringVar(),
            "assy_type": tk.StringVar(),
            "assy_rev_no": tk.StringVar(),
            "assy_serial_no": tk.StringVar(),
            "assy_build_batch_no": tk.StringVar(),
            "test_result": tk.StringVar()
        }

        for key in self._text_vars:
            self._text_vars[key].set(self._config_data.get("default_values", {}).get(key, ""))
        if self._text_vars["assy_type"].get() not in self._TEST_TYPES:
            self._text_vars["assy_type"].set("Vehicle Motherboard")
        self._text_vars["test_result"].set("N/A")

        # Set up action item widgets associated with the labels
        self._action_frame = self._window
        self._actions = {
            "test_jig_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["test_jig_com_port"]),
            "psu_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["psu_com_port"]),
            "managed_sw_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["managed_sw_com_port"]),
            "master_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["master_com_port"]),
            "rcu_com_port": tk.Entry(self._action_frame, textvariable=self._text_vars["rcu_com_port"]),
            "assy_type": tk.OptionMenu(self._action_frame, self._text_vars["assy_type"], *self._TEST_TYPES),
            "assy_rev_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_rev_no"]),
            "assy_serial_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_serial_no"]),
            "assy_build_batch_no": tk.Entry(self._action_frame, textvariable=self._text_vars["assy_build_batch_no"]),
            "run_test":  tk.Button(self._action_frame, text="Start", width=20, command=self.run_test),
            "test_result": tk.Entry(self._action_frame, textvariable=self._text_vars["test_result"],
                                    state="readonly", readonlybackground="white"),
            "test_status": ScrolledText(self._action_frame, height=24, width=100)
        }

        # Make the test_status Scrolled Text read only whilst allowing CTRL-C
        self._actions["test_status"].bind("<Key>", lambda e: self.test_status_ctrl_events(e))

        # Assemble the main window
        for i, key in enumerate(self._labels):
            self._labels[key].grid(column=1, row=i + 1, padx=5, pady=5, sticky="ne")

        for i, key in enumerate(self._actions):
            self._actions[key].grid(column=2, row=i + 1, padx=5, pady=5, sticky="nw")

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

            self._window.destroy()

    def test_status_ctrl_events(self, event):
        """
        Handle Ctrl-key events for the text status ScrolledText widget.  Allows the test result report to be
        copied and pasted from the box.
        :param event: Key press event
        :return: None or "break" depending on key press
        """
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

    def run_test(self):
        """
        Handles the Run (Stop) Test button which is used to start and stop test execution
        @return: N/A
        """

        if not self._test_running.is_set():
            self._actions["run_test"]["text"] = "Stop"

            test_type = self._text_vars["assy_type"].get()

            if test_type == "Vehicle Motherboard" or test_type == "Vehicle Motherboard Part 1" or \
                    test_type == "Vehicle Motherboard Part 2" or test_type == "Vehicle Unit":

                test_info = CsmProdTestInfo()

                # Firmware files
                test_info.zeroise_test_fw = self._config_data.get("sw_binaries", "").get("zeroise_test_fw", "")
                test_info.zeroise_operational_fw = self._config_data.get("sw_binaries", "").get("zeroise_operational_fw", "")
                test_info.gbe_switch_fw = self._config_data.get("sw_binaries", "").get("gbe_switch_fw", "")

                # Build the list of test cases to run
                if test_type == "Vehicle Motherboard":
                    test_info.assy_type = self._CSM_MOTHERBOARD_NO
                    test_info.csm_hostname = self._config_data.get("test_parameters", "").get("csm_hostname", "")

                    for test in self._config_data.get("board_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

                elif test_type == "Vehicle Motherboard Part 1":
                    test_info.assy_type = self._CSM_MOTHERBOARD_NO
                    test_info.csm_hostname = self._config_data.get("test_parameters", "").get("csm_hostname", "")

                    for test in self._config_data.get("board_tests_to_run"):
                        if test.get("test_name", "") in test_info.motherboard_part1_test_case_list:
                            setattr(test_info, test.get("test_name"), test.get("run_test", False))
                        else:
                            setattr(test_info, test.get("test_name"), False)

                elif test_type == "Vehicle Motherboard Part 2":
                    test_info.assy_type = self._CSM_MOTHERBOARD_NO
                    test_info.csm_hostname = self._config_data.get("test_parameters", "").get("csm_hostname", "")

                    for test in self._config_data.get("board_tests_to_run"):
                        if test.get("test_name", "") in test_info.motherboard_part2_test_case_list:
                            setattr(test_info, test.get("test_name"), test.get("run_test", False))
                        else:
                            setattr(test_info, test.get("test_name"), False)

                elif test_type == "Vehicle Unit":
                    test_info.assy_type = self._CSM_ASSEMBLY_NO
                    test_info.csm_hostname = "csm-{}.local".format(self._text_vars["assy_serial_no"].get())

                    for test in self._config_data.get("unit_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

            else:   # Must be a Manpack Test
                test_info = MpCsmProdTestInfo()

                # Firmware files
                test_info.zeroise_test_fw = self._config_data.get("sw_binaries", "").get("mp_zeroise_test_fw", "")
                test_info.zeroise_operational_fw = self._config_data.get("sw_binaries", "").get("mp_zeroise_operational_fw", "")
                test_info.gbe_switch_fw = self._config_data.get("sw_binaries", "").get("mp_gbe_switch_fw", "")

                # Set Assembly Type
                assy_type = self._text_vars["assy_type"].get()

                if "Manpack Motherboard -01" in assy_type:
                    test_info.assy_type = self._MP_KBAN_CSM_MOTHERBOARD_NO
                else:
                    test_info.assy_type = self._MP_CSM_MOTHERBOARD_NO

                # Build the list of test cases to run
                if assy_type == "Manpack Motherboard -00" or assy_type == "Manpack Motherboard -01":
                    for test in self._config_data.get("mp_board_tests_to_run"):
                        setattr(test_info, test.get("test_name"), test.get("run_test", False))

                elif assy_type == "Manpack Motherboard -00 Part 1" or assy_type == "Manpack Motherboard -01 Part 1":
                    for test in self._config_data.get("mp_board_tests_to_run"):
                        if test.get("test_name", "") in test_info.motherboard_part1_test_case_list:
                            setattr(test_info, test.get("test_name"), test.get("run_test", False))
                        else:
                            setattr(test_info, test.get("test_name"), False)

                elif self._text_vars["assy_type"].get() == "Manpack Motherboard -00 Part 2" or \
                        self._text_vars["assy_type"].get() == "Manpack Motherboard -01 Part 2":
                    for test in self._config_data.get("mp_board_tests_to_run"):
                        if test.get("test_name", "") in test_info.motherboard_part2_test_case_list:
                            setattr(test_info, test.get("test_name"), test.get("run_test", False))
                        else:
                            setattr(test_info, test.get("test_name"), False)

            # Common initialisation for all test types...

            # Pull-in text box information
            test_info.tj_com_port = self._text_vars["test_jig_com_port"].get()
            test_info.psu_com_port = self._text_vars["psu_com_port"].get()
            test_info.tpl_sw_com_port = self._text_vars["managed_sw_com_port"].get()
            test_info.master_com_port = self._text_vars["master_com_port"].get()
            test_info.rcu_com_port = self._text_vars["rcu_com_port"].get()
            test_info.assy_rev_no = self._text_vars["assy_rev_no"].get()
            test_info.assy_serial_no = self._text_vars["assy_serial_no"].get()
            test_info.assy_build_batch_no = self._text_vars["assy_build_batch_no"].get()

            # Firmware files
            test_info.zeroise_test_fpga = self._config_data.get("sw_binaries", "").get("zeroise_test_fpga", "")
            test_info.platform_test_scripts = self._config_data.get("sw_binaries", "").get("platform_test_scripts", "")

            # Exe paths
            exe_paths = self._config_data.get("exe_paths", {})
            test_info.segger_jlink_win64 = exe_paths.get("segger_jlink_win64", "")
            test_info.flash_pro = exe_paths.get("flash_pro", "")
            test_info.iperf3 = exe_paths.get("iperf3", "")
            test_info.cygwin1_dll = exe_paths.get("cygwin1_dll", "")

            # CSM Login details
            test_info.csm_hostname = self._config_data.get("test_parameters", "").get("csm_hostname", "")
            test_info.csm_username = self._config_data.get("test_parameters", "").get("csm_username", "")

            t = Thread(target=self.run_test_thread, args=(test_info,))
            t.start()
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
        if type(test_info) is not CsmProdTestInfo and type(test_info) is not MpCsmProdTestInfo:
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
            if type(test_info) is CsmProdTestInfo:
                # Create a CSM Production Test instance
                with CsmProdTest(test_info.tj_com_port, test_info.psu_com_port, test_info.tpl_sw_com_port,
                                 test_info.master_com_port, test_info.rcu_com_port,
                                 test_info.csm_hostname, test_info.csm_username,
                                 self._config_data.get("serial_port_aliases", {}).get("zeroise_micro_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("csm_slave_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("rcu_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("programming_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("gnss1_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("gbe_switch_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("exp_slot_1_serial_port"),
                                 self._config_data.get("serial_port_aliases", {}).get("exp_slot_2_serial_port"),
                                 test_info.segger_jlink_win32 if test_info.segger_jlink_win32 != "" else None,
                                 test_info.segger_jlink_win64 if test_info.segger_jlink_win64 != "" else None,
                                 test_info.flash_pro if test_info.flash_pro != "" else None,
                                 test_info.iperf3 if test_info.iperf3 != "" else None,
                                 test_info.cygwin1_dll if test_info.cygwin1_dll != "" else None) as cpt:
                    for test_case in test_info.test_case_list:
                        if not self._test_running.is_set():
                            break

                        log.debug("{} - {}".format(test_case, getattr(test_info, test_case, False)))

                        if getattr(test_info, test_case, False):
                            if test_case == "set_config_info":
                                ret_val = cpt.set_config_info(test_info.assy_type,
                                                              test_info.assy_rev_no,
                                                              test_info.assy_serial_no,
                                                              test_info.assy_build_batch_no) and ret_val
                            elif test_case == "unit_set_config_info":
                                ret_val = cpt.unit_set_config_info(test_info.assy_type,
                                                                   test_info.assy_rev_no,
                                                                   test_info.assy_serial_no,
                                                                   test_info.assy_build_batch_no,
                                                                   test_info.platform_test_scripts) and ret_val
                            elif test_case == "gbe_sw_connection_test":
                                log.info("")
                                log.info("GbE Switch Connection Test")
                                dur_s = self._config_data.get("test_parameters", {}).get("gbe_conn_test_duration_s", 30)
                                rpi4_ip6_addr = self._config_data.get("test_parameters", {}).get("rpi4_ip6_address", "")

                                # 1 = EXP0 Cu; 2 = EXP1 Cu; 3 = RCU; 5 = CSM Slave; 8 = Programming;
                                # 9 = EXP0 SFP; 10 = EXP1 SFP
                                uport_2_test_switch_map = self._config_data.get("test_parameters", {}).get(
                                    "gbe_uport_2_test_switch_map", [])

                                for uport in self._config_data.get("test_parameters", {}).get("gbe_conn_test_uports", []):
                                    test_sw_port = uport_2_test_switch_map.get(str(uport))
                                    ret_val = cpt.gbe_sw_connection_test(uport, 6, test_sw_port,
                                                                         dur_s, rpi4_ip6_addr) and ret_val
                                    if not self._test_running.is_set():
                                        break
                            elif test_case == "qsgmii_test":
                                log.info("")
                                log.info("GbE Switch QSGMII Test")
                                rpi4_ip6_addr = self._config_data.get("test_parameters", {}).get("rpi4_ip6_address", "")
                                test_cnt = self._config_data.get("test_parameters", {}).get("qsgmii_test_count", 20) + 1

                                for i in range(1, test_cnt):
                                    ret_val = cpt.qsgmii_test(i, rpi4_ip6_addr) and ret_val
                                    if not self._test_running.is_set():
                                        break
                            elif test_case == "power_up_board_linux":
                                ret_val = cpt.power_up_board(linux_run_check=True) and ret_val
                            elif test_case == "program_zeroise_test_fw":
                                ret_val = cpt.program_zeroise_micro(test_info.zeroise_test_fw) and ret_val
                            elif test_case == "program_zeroise_operational_fw":
                                ret_val = cpt.program_zeroise_micro(test_info.zeroise_operational_fw) and ret_val
                            elif test_case == "program_zeroise_fpga_test_image":
                                ret_val = cpt.program_zeroise_fpga(test_info.zeroise_test_fpga) and ret_val
                            elif test_case == "erase_zeroise_fpga_test_image":
                                ret_val = cpt.program_zeroise_fpga(test_info.zeroise_test_fpga, erase=True) and ret_val
                            elif test_case == "program_gbe_sw_fw":
                                ret_val = cpt.program_gbe_sw_fw(fw_file=test_info.gbe_switch_fw) and ret_val
                            elif test_case == "case_switch_test" or test_case == "light_sensor_test" or \
                                    test_case == "unit_pb_controller_irq_test":
                                ret_val = getattr(cpt, test_case)(self.instruction_dialog) and ret_val
                            elif test_case == "unit_buzzer_test":
                                ret_val = getattr(cpt, test_case)(self.yesno_check_dialog) and ret_val
                            elif test_case == "unit_keypad_test":
                                ret_val = getattr(cpt, test_case)(self.instruction_dialog,
                                                                  self.yesno_check_dialog) and ret_val
                            elif test_case == "copy_test_scripts_to_som":
                                ret_val = getattr(cpt, test_case)(test_info.platform_test_scripts) and ret_val
                            elif test_case == "expansion_slot_1_test" or test_case == "expansion_slot_2_test":
                                slot_no = 1 if '1' in test_case else 2
                                gbe_conn_test_duration_s = self._config_data.get("test_parameters",
                                                                                 {}).get("gbe_conn_test_duration_s", 30)
                                rpi4_ip6_addr = self._config_data.get("test_parameters", {}).get("rpi4_ip6_address", "")
                                ret_val = cpt.expansion_slot_test(instruction_dialog_func=self.instruction_dialog,
                                                                  slot_no=slot_no,
                                                                  gbe_conn_test_duration_s=gbe_conn_test_duration_s,
                                                                  rpi4_ip6_addr=rpi4_ip6_addr) and ret_val
                            else:
                                ret_val = getattr(cpt, test_case)() and ret_val
            elif type(test_info) is MpCsmProdTestInfo:
                # Create a Manpack CSM Production Test instance
                if test_info.assy_type == self._MP_KBAN_CSM_MOTHERBOARD_NO:
                    unit_type = UnitTypes.MANPACK_KBAN
                else:
                    unit_type = UnitTypes.MANPACK

                with MpCsmProdTest(test_info.tj_com_port, test_info.psu_com_port, test_info.tpl_sw_com_port,
                                   test_info.master_com_port, test_info.rcu_com_port,
                                   test_info.csm_hostname, test_info.csm_username,
                                   self._config_data.get("serial_port_aliases", {}).get("zeroise_micro_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("csm_slave_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("rcu_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("programming_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("gnss1_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("gbe_switch_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("exp_slot_1_serial_port"),
                                   self._config_data.get("serial_port_aliases", {}).get("exp_slot_2_serial_port"),
                                   unit_type,
                                   test_info.segger_jlink_win32 if test_info.segger_jlink_win32 != "" else None,
                                   test_info.segger_jlink_win64 if test_info.segger_jlink_win64 != "" else None,
                                   test_info.flash_pro if test_info.flash_pro != "" else None,
                                   test_info.iperf3 if test_info.iperf3 != "" else None,
                                   test_info.cygwin1_dll if test_info.cygwin1_dll != "" else None) as cpt:
                    for test_case in test_info.test_case_list:
                        if not self._test_running.is_set():
                            break

                        log.debug("{} - {}".format(test_case, getattr(test_info, test_case, False)))

                        if getattr(test_info, test_case, False):
                            if test_case == "set_config_info":
                                ret_val = cpt.set_config_info(test_info.assy_type,
                                                              test_info.assy_rev_no,
                                                              test_info.assy_serial_no,
                                                              test_info.assy_build_batch_no) and ret_val
                            elif test_case == "set_ntm_hw_config_info":
                                ret_val = cpt.set_ntm_hw_config_info(test_info.assy_rev_no,
                                                                     test_info.assy_serial_no,
                                                                     test_info.assy_build_batch_no) and ret_val
                            elif test_case == "gbe_sw_connection_test":
                                log.info("")
                                log.info("GbE Switch Connection Test")
                                dur_s = self._config_data.get("test_parameters", {}).get("gbe_conn_test_duration_s",
                                                                                         30)
                                rpi4_ip6_addr = self._config_data.get("test_parameters", {}).get("rpi4_ip6_address", "")

                                # 1 = EXP1 Cu; 2 = EXP2 Cu; 3 = Programming; 4 = RCU; 5 = NTM1; 6 = NTM2; 7 = NTM3;
                                # 8 = SoM; 9 = EXP1 SFP; 10 = EXP2 SFP; 11 = PTP PHY (100BASE-FX to SoM)
                                uport_2_test_switch_map = self._config_data.get("test_parameters", {}).get(
                                    "mp_gbe_uport_2_test_switch_map", [])

                                for uport in self._config_data.get("test_parameters", {}).get(
                                        "mp_gbe_conn_test_uports", []):
                                    test_sw_port = uport_2_test_switch_map.get(str(uport))
                                    ret_val = cpt.gbe_sw_connection_test(uport, 3, test_sw_port,
                                                                         dur_s, rpi4_ip6_addr) and ret_val
                                    if not self._test_running.is_set():
                                        break
                            elif test_case == "qsgmii_test":
                                log.info("")
                                log.info("GbE Switch QSGMII Test")
                                rpi4_ip6_addr = self._config_data.get("test_parameters", {}).get("rpi4_ip6_address", "")
                                test_cnt = self._config_data.get("test_parameters", {}).get("qsgmii_test_count", 20) + 1

                                for i in range(1, test_cnt):
                                    ret_val = cpt.qsgmii_test(i, rpi4_ip6_addr) and ret_val
                                    if not self._test_running.is_set():
                                        break
                            elif test_case == "power_up_board_linux":
                                ret_val = cpt.power_up_board(linux_run_check=True) and ret_val
                            elif test_case == "program_zeroise_test_fw":
                                ret_val = cpt.program_zeroise_micro(test_info.zeroise_test_fw) and ret_val
                            elif test_case == "program_zeroise_operational_fw":
                                ret_val = cpt.program_zeroise_micro(test_info.zeroise_operational_fw) and ret_val
                            elif test_case == "program_zeroise_fpga_test_image":
                                ret_val = cpt.program_zeroise_fpga(test_info.zeroise_test_fpga) and ret_val
                            elif test_case == "erase_zeroise_fpga_test_image":
                                ret_val = cpt.program_zeroise_fpga(test_info.zeroise_test_fpga, erase=True) and ret_val
                            elif test_case == "program_gbe_sw_fw":
                                ret_val = cpt.program_gbe_sw_fw(fw_file=test_info.gbe_switch_fw) and ret_val
                            elif test_case == "over_under_voltage_lockout_test" or test_case == "over_voltage_test" or \
                                    test_case == "case_switch_test" or test_case == "light_sensor_test":
                                ret_val = getattr(cpt, test_case)(self.instruction_dialog) and ret_val
                            elif test_case == "copy_test_scripts_to_som":
                                ret_val = getattr(cpt, test_case)(test_info.platform_test_scripts) and ret_val
                            elif test_case == "expansion_slot_1_test" or test_case == "expansion_slot_2_test":
                                slot_no = 1 if '1' in test_case else 2
                                ret_val = cpt.expansion_slot_test(slot_no) and ret_val
                            else:
                                ret_val = getattr(cpt, test_case)() and ret_val
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
