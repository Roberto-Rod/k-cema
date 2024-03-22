#!/usr/bin/env python3

# Tkinter imports
from tkinter import *
from tkinter.ttk import *

# Standard library imports
from threading import Thread
from time import sleep
from datetime import datetime, timedelta
from enum import Enum
import re
import os
import sys

# Third-party imports
from PIL import ImageTk, Image

# Local application imports
from s2p_file_reader import *
from test_limits import *
from cts_test_jig_intf import *

# Test Equipment imports
from test_equipment.power_supply_cpx400dp import *
from test_equipment.power_supply_72_xxxx import *
from test_equipment.signal_generator_hp83752a import *
from test_equipment.signal_generator_n51x3b import *
from test_equipment.spectrum_analyser_hp8563e import *
from test_equipment.spectrum_analyser_fsw import *
from test_equipment.spectrum_analyser_n90xxb import *


class iCTSTestSetupTypes(Enum):
    # Enumeration class for test set-up types
    TEST_UUT_RF_BOARD_RX_PATHS = "Rx (& Tx) Paths"
    TEST_UUT_RF_BOARD_TX_PATHS = "Tx Paths"
    TEST_UUT_RF_BOARD_NO_RF_PATHS = "No RF Paths"
    CALIBRATE_SIG_GEN_TO_UUT_RF_BOARD_ANT = "Calibrate Signal Generator to UUT RF Board Antenna Port"
    CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_IF = "Calibrate Spectrum Analyser to UUT RF Board IF Port"
    CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_ANT = "Calibrate Spectrum Analyser to UUT RF Board Antenna Port"


class iCTSRFBoardTest(Tk):
    # Determine if application is running in the normal Python environment or as a frozen exe
    if getattr(sys, 'frozen', False):
        APP_PATH = os.path.dirname(sys.executable)
        PYTHON_ENV = False
        print("Running as EXE")
    else:
        APP_PATH = os.path.dirname(__file__)
        PYTHON_ENV = True
        print("Running in Python environment")

    # Constants
    UI_VERSION = "0.3.0"
    TEST_VERSION = "0.3.0"
    APP_SW_NO = "KT-956-0264-01"
    APP_NAME = "K-CEMA iCTS RF Board Test Utility [v{}]".format(UI_VERSION)
    APP_LOGO_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "kirintec_logo.ico")
    TEST_REPORT_REL_DIR = os.path.join(APP_PATH + os.sep + "test_reports" + os.sep)
    CALIBRATION_REL_DIR = os.path.join(APP_PATH + os.sep + "calibration" + os.sep)
    SETUP_TEST_UUT_RF_BOARD_RX_PATHS = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_uut_rf_rx_paths.png")
    SETUP_TEST_UUT_RF_BOARD_TX_PATHS = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_uut_rf_tx_paths.png")
    SETUP_TEST_UUT_RF_BOARD_NO_RF_PATHS = os.path.join(
        APP_PATH + os.sep + "images" + os.sep + "setup_uut_rf_no_rf_paths.png")
    SETUP_CALIBRATE_SIG_GEN_TO_UUT_RF_BOARD_ANT_PATH = os.path.join(
        APP_PATH + os.sep + "images" + os.sep + "setup_sig_gen_to_uut_rf_ant.png")
    SETUP_CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_IF_PATH = os.path.join(
        APP_PATH + os.sep + "images" + os.sep + "setup_spec_an_to_uut_rf_if.png")
    SETUP_CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_ANT_PATH = os.path.join(
        APP_PATH + os.sep + "images" + os.sep + "setup_spec_an_to_uut_rf_ant.png")
    MIN_TEST_FREQ_HZ = int(20e6)  # 20 MHz
    MAX_TEST_FREQ_HZ = int(12.6e9)  # 12.6 GHz
    PSU_VOLTAGE_V = 12.0
    PSU_CURRENT_A = 0.3
    RX_TEST_AMPLITUDE = 2.0

    # Calibration files
    signal_generator_to_uut_rf_board_ant_s2p_file = CALIBRATION_REL_DIR + "signal_generator_to_uut_rf_board_ant.s2p"
    spectrum_analyser_to_uut_rf_board_if_s2p_file = CALIBRATION_REL_DIR + "spectrum_analyser_to_uut_rf_board_if.s2p"
    spectrum_analyser_to_uut_rf_board_ant_s2p_file = CALIBRATION_REL_DIR + "spectrum_analyser_to_uut_rf_board_ant.s2p"

    # Test objects
    psu = None
    sg = None
    sa = None
    test_limits = None
    popup = None
    now = None
    test_jig = None

    # Flags used for abort test feature
    abort_requested = False
    abort_pending = False
    test_running = False

    def __init__(self):
        super().__init__()

        # Needed for windows to show correct icon on Taskbar
        try:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_NAME)
        except ImportError:
            pass

        # Set title and icon
        self.title("{} - {}".format(self.APP_SW_NO, self.APP_NAME))
        self.iconbitmap(self.APP_LOGO_PATH)
        self.option_add("*font", "Arial 9")

        # Set the fixed window size
        window_width = 1112
        window_height = 575
        self.minsize(window_width, window_height)
        self.maxsize(window_width, window_height)

        # Get the screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Find the screen centre point
        screen_center_x = int(screen_width / 2 - window_width / 2)
        screen_center_y = int(screen_height / 2 - window_height / 2)

        # Set the position of the window to the centre of the screen
        self.geometry(f'{window_width}x{window_height}+{screen_center_x}+{screen_center_y}')

        # Populate main window with the required widgets

        # UUT Details frame and label
        self.uut_details_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.uut_details_frame.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
        self.uut_details_frame_label = Label(self.uut_details_frame, text="UUT Details", font="Arial 11 bold")
        self.uut_details_frame_label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # UUT Part Number label and entry
        self.uut_part_number = StringVar()
        self.uut_part_number.set("KT-000-0211-00")
        self.uut_part_number_label = Label(self.uut_details_frame, text="UUT Part Number:")
        self.uut_part_number_label.grid(column=0, row=1, padx=3, pady=6, sticky=NSEW)
        self.uut_part_number_entry = Entry(self.uut_details_frame, text=self.uut_part_number, state="readonly")
        self.uut_part_number_entry.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)

        # UUT Revision label and entry
        self.uut_revision = StringVar()
        self.uut_revision_label = Label(self.uut_details_frame, text="Enter the UUT Revision:")
        self.uut_revision_label.grid(column=0, row=2, padx=3, pady=6, sticky=NSEW)
        self.uut_revision_entry = Entry(self.uut_details_frame, textvariable=self.uut_revision)
        self.uut_revision_entry.grid(column=1, row=2, padx=3, pady=3, sticky=NSEW)

        # UUT Serial Number label and entry
        self.uut_serial_number = StringVar()
        self.uut_serial_number_label = Label(self.uut_details_frame, text="Enter the UUT Serial Number:")
        self.uut_serial_number_label.grid(column=0, row=3, padx=3, pady=6, sticky=NSEW)
        self.uut_serial_number_entry = Entry(self.uut_details_frame, textvariable=self.uut_serial_number)
        self.uut_serial_number_entry.grid(column=1, row=3, padx=3, pady=3, sticky=NSEW)

        # Test Modules frame and label
        self.test_modules_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.test_modules_frame.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.test_modules_frame_label = Label(self.test_modules_frame, text="Test Modules", font="Arial 11 bold")
        self.test_modules_frame_label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # Production Test button and label
        self.production_test_button = Button(self.test_modules_frame, text=">> PRODUCTION TEST <<",
                                             command=self.production_test_routine, width=26)
        self.production_test_button.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.production_test_label = Label(self.test_modules_frame, text="")
        self.production_test_label.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)

        # Built-In Test button and label
        self.built_in_test_button = Button(self.test_modules_frame, text="BUILT-IN TEST",
                                           command=self.built_in_test_routine)
        self.built_in_test_button.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.built_in_test_label = Label(self.test_modules_frame, text="")
        self.built_in_test_label.grid(column=1, row=2, padx=3, pady=3, sticky=NSEW)

        # Rx Paths button and label
        self.rx_paths_button = Button(self.test_modules_frame, text="RX PATHS", command=self.rx_paths_routine)
        self.rx_paths_button.grid(column=0, row=3, padx=3, pady=3, sticky=NSEW)
        self.rx_paths_label = Label(self.test_modules_frame, text="")
        self.rx_paths_label.grid(column=1, row=3, padx=3, pady=3, sticky=NSEW)

        # Rx Attenuation button and label
        self.rx_attenuation_button = Button(self.test_modules_frame, text="RX ATTENUATION",
                                            command=self.rx_attenuation_routine)
        self.rx_attenuation_button.grid(column=0, row=4, padx=3, pady=3, sticky=NSEW)
        self.rx_attenuation_label = Label(self.test_modules_frame, text="")
        self.rx_attenuation_label.grid(column=1, row=4, padx=3, pady=3, sticky=NSEW)

        # Tx Paths button and label
        self.tx_paths_button = Button(self.test_modules_frame, text="TX PATHS", command=self.tx_paths_routine)
        self.tx_paths_button.grid(column=0, row=5, padx=3, pady=3, sticky=NSEW)
        self.tx_paths_label = Label(self.test_modules_frame, text="")
        self.tx_paths_label.grid(column=1, row=5, padx=3, pady=3, sticky=NSEW)

        # Tx Attenuation button and label
        self.tx_attenuation_button = Button(self.test_modules_frame, text="TX ATTENUATION",
                                            command=self.tx_attenuation_routine)
        self.tx_attenuation_button.grid(column=0, row=6, padx=3, pady=3, sticky=NSEW)
        self.tx_attenuation_label = Label(self.test_modules_frame, text="")
        self.tx_attenuation_label.grid(column=1, row=6, padx=3, pady=3, sticky=NSEW)

        # Calibrate Set-Up button and label (add separator label to isolate this button from the ones above)
        self.separator_label = Label(self.test_modules_frame, text="_______________________")
        self.separator_label.grid(column=0, row=7, padx=3, pady=6, sticky=NSEW)
        self.calibrate_setup_button = Button(self.test_modules_frame, text="CALIBRATE SET-UP",
                                             command=self.calibrate_set_up_routine)
        self.calibrate_setup_button.grid(column=0, row=8, padx=3, pady=3, sticky=NSEW)
        self.calibrate_setup_label = Label(self.test_modules_frame, text="")
        self.calibrate_setup_label.grid(column=1, row=8, padx=3, pady=3, sticky=NSEW)

        # Test Equipment frame and label
        self.test_equipment_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.test_equipment_frame.grid(column=1, row=0, padx=3, pady=3, sticky=NSEW)
        self.test_equipment_frame_label = Label(self.test_equipment_frame, text="Test Equipment", font="Arial 11 bold")
        self.test_equipment_frame_label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # DC Power Supply label, combobox, button and label
        self.dc_power_supply = StringVar()
        self.dc_power_supply_label0 = Label(self.test_equipment_frame, text="DC Power Supply:")
        self.dc_power_supply_label0.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_combobox = Combobox(self.test_equipment_frame, textvariable=self.dc_power_supply)
        self.dc_power_supply_combobox["values"] = ("72-XXXX", "CPX400DP")
        self.dc_power_supply_combobox.current(0)
        self.dc_power_supply_combobox.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_button = Button(self.test_equipment_frame, text="Check",
                                             command=self.check_dc_power_supply)
        self.dc_power_supply_button.grid(column=2, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_label1 = Label(self.test_equipment_frame, text="")
        self.dc_power_supply_label1.grid(column=3, row=1, padx=3, pady=3, sticky=NSEW)

        # RF Signal Generator combobox, button and label
        self.rf_signal_generator = StringVar()
        self.rf_signal_generator_label0 = Label(self.test_equipment_frame, text="RF Signal Generator:")
        self.rf_signal_generator_label0.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_combobox = Combobox(self.test_equipment_frame, textvariable=self.rf_signal_generator)
        self.rf_signal_generator_combobox["values"] = ("N51X3B", "HP83752A")
        self.rf_signal_generator_combobox.current(0)
        self.rf_signal_generator_combobox.grid(column=1, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_button = Button(self.test_equipment_frame, text="Check",
                                                 command=self.check_rf_signal_generator)
        self.rf_signal_generator_button.grid(column=2, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_label1 = Label(self.test_equipment_frame, text="")
        self.rf_signal_generator_label1.grid(column=3, row=2, padx=3, pady=3, sticky=NSEW)

        # RF Spectrum Analyser combobox, button and label
        self.rf_spectrum_analyser = StringVar()
        self.rf_spectrum_analyser_label0 = Label(self.test_equipment_frame, text="RF Spectrum Analyser:")
        self.rf_spectrum_analyser_label0.grid(column=0, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_combobox = Combobox(self.test_equipment_frame, textvariable=self.rf_spectrum_analyser)
        self.rf_spectrum_analyser_combobox["values"] = ("N90XXB", "R&S FSW", "HP8563E")
        self.rf_spectrum_analyser_combobox.current(0)
        self.rf_spectrum_analyser_combobox.grid(column=1, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_button = Button(self.test_equipment_frame, text="Check",
                                                  command=self.check_rf_spectrum_analyser)
        self.rf_spectrum_analyser_button.grid(column=2, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_label1 = Label(self.test_equipment_frame, text="")
        self.rf_spectrum_analyser_label1.grid(column=3, row=3, padx=3, pady=3, sticky=NSEW)

        # Test Report frame and label
        self.test_report_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.test_report_frame.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)
        self.test_report_frame_label = Label(self.test_report_frame, text="Test Report", font="Arial 11 bold")
        self.test_report_frame_label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # Test Report text box
        self.test_report_text = Text(self.test_report_frame, wrap=NONE, height=20, width=100)
        self.test_report_text.bind("<Key>", lambda e: self.ctrl_event(
            e))  # Makes the Text widget read-only while allowing CTRL+C event
        self.test_report_text_xs = Scrollbar(self.test_report_frame, orient=HORIZONTAL,
                                             command=self.test_report_text.xview)
        self.test_report_text_ys = Scrollbar(self.test_report_frame, orient=VERTICAL,
                                             command=self.test_report_text.yview)
        self.test_report_text['xscrollcommand'] = self.test_report_text_xs.set
        self.test_report_text['yscrollcommand'] = self.test_report_text_ys.set
        self.test_report_text.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.test_report_text_xs.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.test_report_text_ys.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)

        # Overall Status frame and label
        self.overall_status_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.overall_status_frame.grid(column=0, columnspan=2, row=2, padx=3, pady=3, sticky=NSEW)
        self.overall_status_label = Label(self.overall_status_frame, text="TEST IDLE", font="Arial 11 bold",
                                          foreground="white", background="gray32", anchor=CENTER, width=101)
        self.overall_status_label.grid(column=1, row=0, padx=3, pady=3, sticky=NSEW)

        # Calibration folder button
        self.calibration_folder_button = Button(self.overall_status_frame, text="View Calibration Files", width=20,
                                                command=self.open_calibration_folder)
        self.calibration_folder_button.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # Reports folder button
        self.reports_folder_button = Button(self.overall_status_frame, text="View Test Reports", width=20,
                                            command=self.open_reports_folder)
        self.reports_folder_button.grid(column=2, row=0, padx=3, pady=3, sticky=NSEW)

    def ctrl_event(self, event):
        if 12 == event.state and event.keysym == 'c':
            return None
        else:
            return "break"

    def disable_event(event=None):
        pass

    def get_com_port(self):
        # This method tests each available COM port and returns the
        # first one that responds positively to a Test Jig command
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())

        com_port = None
        for port in ports:
            try:
                if port.device:
                    com_port = port.name
                    print("Checking for Test Jig on {}... ".format(com_port))
                    self.test_jig = CtsTestJigInterface(com_port, 0.25)
                    if self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_RX_MODE):
                        print("Found Test Jig on {} ".format(com_port))
                        break
                    else:
                        com_port = None
                del self.test_jig
            except:
                com_port = None

        if self.test_jig is not None:
            del self.test_jig
            self.test_jig = None

        return com_port

    def check_dc_power_supply(self):
        self.dc_power_supply_label1["text"] = "Please wait..."
        self.dc_power_supply_button["state"] = DISABLED
        self.dc_power_supply_combobox["state"] = DISABLED

        # Attempt to find the DC Power Supply in a new thread for non-blocking
        Thread(target=self.find_dc_power_supply).start()

    def find_dc_power_supply(self, button_normal_on_complete=True):
        # Create DC Power Supply object
        if self.dc_power_supply_combobox.get() == "CPX400DP":
            self.psu = PowerSupplyCPX400DP()
        elif self.dc_power_supply_combobox.get() == "72-XXXX":
            self.psu = PowerSupply72_XXXX()

        # Attempt to find and initialise the DC Power Supply
        if self.psu.find_and_initialise():
            self.dc_power_supply_label1["text"] = "Found: {}".format(self.psu.details()[:40])
        else:
            self.dc_power_supply_label1["text"] = "Not found"
            self.psu = None

        if button_normal_on_complete:
            self.dc_power_supply_button["state"] = NORMAL
            self.dc_power_supply_combobox["state"] = NORMAL

        return bool(self.psu is not None)

    def check_rf_signal_generator(self):
        self.rf_signal_generator_label1["text"] = "Please wait..."
        self.rf_signal_generator_button["state"] = DISABLED
        self.rf_signal_generator_combobox["state"] = DISABLED

        # Attempt to find the RF Signal Generator in a new thread for non-blocking
        Thread(target=self.find_rf_signal_generator).start()

    def find_rf_signal_generator(self, button_normal_on_complete=True):
        # Create RF Signal Generator object
        if self.rf_signal_generator_combobox.get() == "HP83752A":
            self.sg = SignalGeneratorHP83752A()
        elif self.rf_signal_generator_combobox.get() == "N51X3B":
            self.sg = SignalGeneratorN51X3B()

        # Attempt to find and initialise the RF Signal Generator
        if self.sg.find_and_initialise():
            self.rf_signal_generator_label1["text"] = "Found: {}".format(self.sg.details()[:40])
        else:
            self.rf_signal_generator_label1["text"] = "Not found"
            self.sg = None

        if button_normal_on_complete:
            self.rf_signal_generator_button["state"] = NORMAL
            self.rf_signal_generator_combobox["state"] = NORMAL

        return bool(self.sg is not None)

    def check_rf_spectrum_analyser(self):
        self.rf_spectrum_analyser_label1["text"] = "Please wait..."
        self.rf_spectrum_analyser_button["state"] = DISABLED
        self.rf_spectrum_analyser_combobox["state"] = DISABLED

        # Attempt to find the RF Spectrum Analyser in a new thread for non-blocking
        Thread(target=self.find_rf_spectrum_analyser).start()

    def find_rf_spectrum_analyser(self, button_normal_on_complete=True):
        # Create RF Spectrum Analyser object
        if self.rf_spectrum_analyser_combobox.get() == "N90XXB":
            self.sa = SpectrumAnalyserN90XXB()
        elif self.rf_spectrum_analyser_combobox.get() == "HP8563E":
            self.sa = SpectrumAnalyserHP8563E()
        elif self.rf_spectrum_analyser_combobox.get() == "R&S FSW":
            self.sa = SpectrumAnalyserFSW()

        # Attempt to find and initialise the RF Spectrum Analyser
        if self.sa.find_and_initialise():
            self.rf_spectrum_analyser_label1["text"] = "Found: {}".format(self.sa.details()[:40])
        else:
            self.rf_spectrum_analyser_label1["text"] = "Not found"
            self.sa = None

        if button_normal_on_complete:
            self.rf_spectrum_analyser_button["state"] = NORMAL
            self.rf_spectrum_analyser_combobox["state"] = NORMAL

        return bool(self.sa is not None)

    def open_reports_folder(self):
        path = self.TEST_REPORT_REL_DIR
        path = os.path.realpath(path)
        os.startfile(path)

    def open_calibration_folder(self):
        path = self.CALIBRATION_REL_DIR
        path = os.path.realpath(path)
        os.startfile(path)

    def lock_ui(self, lock=True):
        # Enable/disable all the interactive UI elements
        self.uut_revision_entry["state"] = DISABLED if lock else NORMAL
        self.uut_serial_number_entry["state"] = DISABLED if lock else NORMAL
        self.built_in_test_button["state"] = DISABLED if lock else NORMAL
        self.rx_paths_button["state"] = DISABLED if lock else NORMAL
        self.rx_attenuation_button["state"] = DISABLED if lock else NORMAL
        self.tx_paths_button["state"] = DISABLED if lock else NORMAL
        self.tx_attenuation_button["state"] = DISABLED if lock else NORMAL
        self.dc_power_supply_combobox["state"] = DISABLED if lock else NORMAL
        self.dc_power_supply_button["state"] = DISABLED if lock else NORMAL
        self.rf_signal_generator_combobox["state"] = DISABLED if lock else NORMAL
        self.rf_signal_generator_button["state"] = DISABLED if lock else NORMAL
        self.rf_spectrum_analyser_combobox["state"] = DISABLED if lock else NORMAL
        self.rf_spectrum_analyser_button["state"] = DISABLED if lock else NORMAL
        self.calibrate_setup_button["state"] = DISABLED if lock else NORMAL

        # Update button and label text
        if not lock:
            self.production_test_button["text"] = ">> PRODUCTION TEST <<"
            self.production_test_button["command"] = self.production_test_routine
        else:
            self.production_test_label["text"] = ""
            self.built_in_test_label["text"] = ""
            self.rx_paths_label["text"] = ""
            self.rx_attenuation_label["text"] = ""
            self.tx_paths_label["text"] = ""
            self.tx_attenuation_label["text"] = ""
            self.calibrate_setup_label["text"] = ""
            self.dc_power_supply_label1["text"] = ""
            self.rf_signal_generator_label1["text"] = ""
            self.rf_spectrum_analyser_label1["text"] = ""

    def request_abort_test(self):
        # Make sure we process a single abort request at a time
        if not self.abort_pending:
            self.production_test_button["command"] = None
            self.abort_requested = True
            self.production_test_label["text"] = "Stopping test..."
            self.abort_pending = True

            # Use a new thread for non-blocking
            Thread(target=self.wait_abort_test).start()

    def wait_abort_test(self):
        # Wait for the current test to complete
        while self.test_running:
            pass

        # Complete
        self.lock_ui(False)
        self.production_test_label["text"] = "Test incomplete"
        self.overall_status_label["text"] = "TEST INCOMPLETE"
        self.test_report_insert_text("Test was aborted\n")
        self.overall_status_label["background"] = "orange"
        self.abort_requested = False
        self.abort_pending = False

        # Attempt some clean up
        if self.popup is not None:
            self.popup.destroy()
        if self.test_jig is not None:
            del self.test_jig  # Release the serial port
        if self.sg is not None:
            self.sg.set_output_enable(False)
        if self.psu is not None:
            self.psu.set_enabled(False)

    def initialise_test_report(self, test_heading=""):
        # Set the overall status
        self.overall_status_label["text"] = "TEST IN PROGRESS (PASS)"
        self.overall_status_label["background"] = "green"

        # Clear the report
        self.test_report_text.delete('1.0', END)

        # Ensure the test report folder exists
        if not os.path.exists(self.TEST_REPORT_REL_DIR):
            os.makedirs(self.TEST_REPORT_REL_DIR)

        # Add initial info to the report, such as date/time and UUT details
        self.test_report_insert_text("{}\n\n".format(test_heading))

        self.test_report_insert_text("Test Version: {}\n\n".format(self.TEST_VERSION))
        self.now = datetime.now()
        self.test_report_insert_text("{:02d}-{:02d}-{:04d} {:02d}:{:02d}:{:02d}\n\n"
                                     .format(self.now.day, self.now.month, self.now.year, self.now.hour,
                                             self.now.minute, self.now.second))

        # Validate user entries
        uut_revision_pattern = re.compile("[A-Z][.][0-9]+$")
        uut_revision = self.uut_revision_entry.get().strip().capitalize()
        if not uut_revision_pattern.match(uut_revision):
            self.test_report_insert_text("Invalid UUT Revision entry (format is X.n)\n")
            self.request_abort_test()
            return False

        # Check serial number field isn't empty or more than 15 characters long
        if self.uut_serial_number_entry.get().strip() == "" or len(self.uut_serial_number_entry.get().strip()) > 15:
            self.test_report_insert_text("Invalid UUT Serial Number entry\n")
            self.request_abort_test()
            return False
        else:
            uut_serial_number = self.uut_serial_number.get().strip().upper()

        self.test_report_insert_text("UUT Part Number: {}\nUUT Revision: {}\nUUT Serial Number: {}\n\n"
                                     .format(self.uut_part_number_entry.get(), uut_revision, uut_serial_number))

        # Change the Production Test button to an Abort Test button
        self.production_test_button["text"] = ">> ABORT TEST <<"
        self.production_test_button["command"] = self.request_abort_test
        self.production_test_label["text"] = "Test in progress..."

        # Test limits object
        self.test_limits = TestLimits()

        return True

    def initialise_test_equipment(self, signal_generator_required, spectrum_analyser_required):
        # Connect to the test equipment
        self.test_report_insert_text("Connecting to DC Power Supply... ")
        if self.find_dc_power_supply(False):
            self.test_report_insert_text("OK\n")
        else:
            self.test_report_insert_text("Error\n")
            self.request_abort_test()
            return False

        if signal_generator_required:
            self.test_report_insert_text("Connecting to RF Signal Generator... ")
            if self.find_rf_signal_generator(False):
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False

        if spectrum_analyser_required:
            self.test_report_insert_text("Connecting to RF Spectrum Analyser... ")
            if self.find_rf_spectrum_analyser(False):
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False

        # Validate the calibration files
        s2p = S2PFileReader()
        if signal_generator_required:
            self.test_report_insert_text("Validating calibration file: {}... " \
                                         .format(
                self.signal_generator_to_uut_rf_board_ant_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
            if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3,
                                   self.signal_generator_to_uut_rf_board_ant_s2p_file) is not None \
                    and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3,
                                            self.signal_generator_to_uut_rf_board_ant_s2p_file) is not None:
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False

        if spectrum_analyser_required:
            self.test_report_insert_text("Validating calibration file: {}... " \
                                         .format(
                self.spectrum_analyser_to_uut_rf_board_if_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
            if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3,
                                   self.spectrum_analyser_to_uut_rf_board_if_s2p_file) is not None \
                    and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3,
                                            self.spectrum_analyser_to_uut_rf_board_if_s2p_file) is not None:
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False
            self.test_report_insert_text("Validating calibration file: {}... " \
                                         .format(
                self.spectrum_analyser_to_uut_rf_board_ant_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
            if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3,
                                   self.spectrum_analyser_to_uut_rf_board_ant_s2p_file) is not None \
                    and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3,
                                            self.spectrum_analyser_to_uut_rf_board_ant_s2p_file) is not None:
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False

        # Opportunity to abort here
        if self.abort_requested:
            self.test_running = False
            return False

        # Configure PSU channel 1 and enable the output
        self.test_report_insert_text(
            "Setting PSU to {} V, {} A and enabling the output... ".format(self.PSU_VOLTAGE_V, self.PSU_CURRENT_A))
        ok = self.psu.set_voltage(self.PSU_VOLTAGE_V)
        ok &= self.psu.set_current(self.PSU_CURRENT_A)
        ok &= self.psu.set_ovp(self.PSU_VOLTAGE_V * 1.1)
        ok &= self.psu.set_ocp(self.PSU_CURRENT_A * 1.1)
        ok &= self.psu.set_sense_local()
        ok &= self.psu.set_enabled(True)
        if ok:
            self.test_report_insert_text("OK\n")
        else:
            self.test_report_insert_text("Error\n")
            self.request_abort_test()
            return False

        # Attempt to open the Test Jig serial port
        sleep(1)
        ok = False
        com_port = self.get_com_port()
        if com_port is not None:
            try:
                self.test_report_insert_text("Connecting to Test Jig on {}... ".format(com_port))
                self.test_jig = CtsTestJigInterface(com_port)
                self.test_report_insert_text("OK\n\n")
                ok = True
            except:
                self.test_report_insert_text("Error\n\n")
        else:
            self.test_report_insert_text("Failed to find the Test Jig serial port\n\n")

        if not ok:
            self.request_abort_test()
            return False
        else:
            return True

    def production_test_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_production_test).start()

    def built_in_test_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_built_in_test).start()

    def rx_paths_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_rx_paths).start()

    def rx_attenuation_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_rx_attenuation).start()

    def tx_paths_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_tx_paths).start()

    def tx_attenuation_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_tx_attenuation).start()

    def calibrate_set_up_routine(self):
        # Run the routine in a new thread for non-blocking
        Thread(target=self.run_calibrate_set_up).start()

    def run_production_test(self):
        # Start test running
        self.test_running = True

        # Lock the UI down
        self.lock_ui(True)

        # Initialise the test report
        ok = self.initialise_test_report(self.production_test_button["text"])
        if not ok or self.abort_requested:
            self.test_running = False
            return False

        # Display the required set-up image
        self.show_hardware_setup(iCTSTestSetupTypes.TEST_UUT_RF_BOARD_RX_PATHS)

        # Initialise the test equipment
        ok = self.initialise_test_equipment(True, True)
        if not ok or self.abort_requested:
            self.test_running = False
            return False

        # Run each test module in turn
        if self.test_running:
            ok = self.run_built_in_test(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_rx_paths(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_rx_attenuation(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_tx_paths(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_tx_attenuation(False)
            self.test_report_insert_text("\n")

        # End the test:
        del self.test_jig  # Release the serial port
        if not self.test_running:
            return False
        else:
            self.test_running = False

            # Update the test status
            self.production_test_label["text"] = "Test complete"
            if ok:
                overall_status = "PASS"
                self.overall_status_label["text"] = "TEST PASSED"
                self.overall_status_label["background"] = "green"
            else:
                overall_status = "FAIL"
                self.overall_status_label["text"] = "TEST FAILED"
                self.overall_status_label["background"] = "red"

            # Create the test report
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}.txt". \
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,
                       self.uut_part_number_entry.get(), self.uut_revision_entry.get().capitalize(),
                       self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                f.write(self.test_report_text.get('1.0', END))

            self.lock_ui(False)
            self.psu.set_enabled(False)
            return True

    def run_built_in_test(self, standalone=True):
        # Start test running
        self.test_running = True
        self.built_in_test_label["text"] = "Test in progress..."

        fail_count = 0
        section = 1
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.built_in_test_label["text"] = "Test in progress..."

            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.built_in_test_button["text"]))

            if ok:
                # Display the required set-up image
                self.show_hardware_setup(iCTSTestSetupTypes.TEST_UUT_RF_BOARD_NO_RF_PATHS)

                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, False)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.built_in_test_button["text"]))

        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False

        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")

        # Initialise the UUT to known state
        ok = self.uut_initialise()
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # 1.1: Initial PSU Current (in mA)
        description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)
        result = int((self.psu.get_current_out() * 1000) + 0.5)
        if lower_limit <= result <= upper_limit:
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text(
            "{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result,
                                                               lower_limit, upper_limit, status))
        sub_section += 1

        # 1.2 Synth Lock Detect
        description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)
        ok, synth_locked = self.test_jig.get_synth_lock_detect()
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        result = int(1) if synth_locked else int(0)

        if lower_limit <= result <= upper_limit:
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text(
            "{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result,
                                                               lower_limit, upper_limit, status))
        sub_section += 1

        # 1.2-1.x: Test Jig ADC Data
        ok, adc_data = self.test_jig.get_adc_data()
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        for key in adc_data:
            description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)
            result = adc_data[key]
            if lower_limit <= result <= upper_limit:
                status = "Pass"
            else:
                status = "Fail"
                fail_count += 1
                self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                self.overall_status_label["background"] = "red"
            self.test_report_insert_text(
                "{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result,
                                                                   lower_limit, upper_limit, status))
            sub_section += 1

        # End the test
        if standalone:
            del self.test_jig  # Release the serial port
            self.test_running = False

        # Update the test status
        self.built_in_test_label["text"] = "Test complete (failures: {})".format(fail_count)
        if standalone:
            self.production_test_label["text"] = ""
            if fail_count == 0:
                overall_status = "PASS"
                self.overall_status_label["text"] = "TEST PASSED"
                self.overall_status_label["background"] = "green"
            else:
                overall_status = "FAIL"
                self.overall_status_label["text"] = "TEST FAILED"
                self.overall_status_label["background"] = "red"

            # Create the test report ("(P)" suffix for partial)
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt" \
                                    "".format(self.now.year, self.now.month, self.now.day, self.now.hour,
                                              self.now.minute, self.now.second, self.uut_part_number_entry.get(),
                                              self.uut_revision_entry.get().capitalize(),
                                              self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                f.write(self.test_report_text.get('1.0', END))

            self.lock_ui(False)
            self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_rx_paths(self, standalone=True):
        # Start test running
        self.test_running = True
        self.rx_paths_label["text"] = "Test in progress..."

        fail_count = 0
        section = 2
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.rx_paths_label["text"] = "Test in progress..."

            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.rx_paths_button["text"]))

            if ok:
                # Display the required set-up image
                self.show_hardware_setup(iCTSTestSetupTypes.TEST_UUT_RF_BOARD_RX_PATHS)

                # Initialise the test equipment
                ok = self.initialise_test_equipment(True, True)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.rx_paths_button["text"]))

        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False

            # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")

        # Initialise the UUT to known state
        # Select Test Jig Rx mode
        # Set Rx Attenuation to 0
        ok = self.uut_initialise()
        ok &= self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_RX_MODE)
        ok &= self.test_jig.set_rx_attenuator(0)
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Apply common Spectrum Analyser settings
        ok = self.sa.set_span_Hz(int(1e6))
        ok &= self.sa.set_attenuation_dB(0)
        ok &= self.sa.set_reference_level_dBm(-10.0)
        ok &= self.sa.set_continuous_sweep(False)
        if not ok:
            self.test_report_insert_text("TE command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # Apply common Signal Generator settings
        ok = self.sg.set_output_power_dBm(0.00)
        if not ok:
            self.test_report_insert_text("TE command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        s2p = S2PFileReader()
        rx_path_curr = -1
        IF_freq_Hz_curr = -1

        # 2.x: Loop around measuring fundamental and image levels using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)

                # The description field contains the Rx path #, the input test frequency
                # and whether the test frequency is the fundamental or image term
                descr_chunks = str(description).strip().split(", ")
                rx_path = int(re.sub('RX', '', descr_chunks[0].strip()))
                if "GHz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('GHz', '', descr_chunks[1].strip())) * 1e9)
                elif "MHz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('MHz', '', descr_chunks[1].strip())) * 1e6)
                elif "kHz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('kHz', '', descr_chunks[1].strip())) * 1e3)
                elif "Hz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('Hz', '', descr_chunks[1].strip())))
                else:
                    self.test_report_insert_text("Invalid test parameter\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                is_fundamental = True if "Fund" in descr_chunks[2] else False

                # Determine the IF and LO frequencies
                if rx_path == 0:
                    rx_path = CtsTestJigRfBoardRxPaths.RX0_20_500_MHZ
                    IF_freq_Hz = int(917e6)
                    LO_freq_Hz = test_freq_Hz + IF_freq_Hz
                elif rx_path == 1:
                    rx_path = CtsTestJigRfBoardRxPaths.RX1_500_800_MHZ
                    IF_freq_Hz = int(2310e6)
                    LO_freq_Hz = test_freq_Hz + IF_freq_Hz
                elif rx_path == 2:
                    rx_path = CtsTestJigRfBoardRxPaths.RX2_800_2000_MHZ
                    IF_freq_Hz = int(2355e6)
                    LO_freq_Hz = test_freq_Hz + IF_freq_Hz
                elif rx_path == 3:
                    rx_path = CtsTestJigRfBoardRxPaths.RX3_2000_2600_MHZ
                    IF_freq_Hz = int(915e6)
                    LO_freq_Hz = test_freq_Hz - IF_freq_Hz
                elif rx_path == 4:
                    rx_path = CtsTestJigRfBoardRxPaths.RX4_2600_4400_MHZ
                    if test_freq_Hz > int(3000e6):
                        IF_freq_Hz = int(2310e6)
                    else:
                        IF_freq_Hz = int(915e6)
                    LO_freq_Hz = test_freq_Hz - IF_freq_Hz
                elif rx_path == 5:
                    rx_path = CtsTestJigRfBoardRxPaths.RX5_4400_6000_MHZ
                    if test_freq_Hz > int(4670e6):
                        IF_freq_Hz = int(2310e6)
                    else:
                        IF_freq_Hz = int(2355e6)
                    LO_freq_Hz = test_freq_Hz - IF_freq_Hz

                # Set the Rx path (if different)
                if rx_path_curr != rx_path:
                    rx_path_curr = rx_path
                    ok = self.test_jig.set_rx_path(rx_path)
                    if not ok:
                        self.test_report_insert_text("Serial command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)

                # Set the Synth (LO) frequency (if this is a fundamental test frequency)
                if is_fundamental:
                    ok = self.test_jig.set_synth_frequency_mhz(LO_freq_Hz / int(1e6))
                    if not ok:
                        self.test_report_insert_text("Serial command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)

                    # Check Synth is locked
                    ok, synth_locked = self.test_jig.get_synth_lock_detect()
                    if not ok:
                        self.test_report_insert_text("Serial command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    if not synth_locked:
                        self.test_report_insert_text("Synth is not locked\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False

                # Update Spectrum Analyser centre (IF) frequency (if this is a fundamental test frequency, and IF is different)
                if is_fundamental and (IF_freq_Hz_curr != IF_freq_Hz):
                    IF_freq_Hz_curr = IF_freq_Hz
                    ok = self.sa.set_centre_frequency_Hz(IF_freq_Hz)
                    if not ok:
                        self.test_report_insert_text("TE command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False

                        # Update Signal Generator output frequency and amplitude, correcting the amplitude
                test_ampl_dBm = self.RX_TEST_AMPLITUDE + \
                                (s2p.get_s_parameter(test_freq_Hz, 3,
                                                     self.signal_generator_to_uut_rf_board_ant_s2p_file, True) * -1)
                ok = self.sg.set_frequency_Hz(test_freq_Hz)
                ok &= self.sg.set_output_power_dBm(test_ampl_dBm)
                if not ok:
                    self.test_report_insert_text("TE command failure\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                # Signal Generator settling time required
                if sub_section == 1:
                    ok = self.sg.set_output_enable(True)
                    if not ok:
                        self.test_report_insert_text("TE command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                sleep(1)

                # Measure the peak tone power and apply correction
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + \
                                             (s2p.get_s_parameter(IF_freq_Hz, 3,
                                                                  self.spectrum_analyser_to_uut_rf_board_if_s2p_file,
                                                                  True) * -1)))

                # Determine the test result
                if is_fundamental:
                    fundamental = peak
                    result = fundamental
                else:
                    result = peak - fundamental

                if result >= lower_limit and result <= upper_limit:
                    status = "Pass"
                else:
                    status = "Fail"
                    fail_count += 1
                    self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                    self.overall_status_label["background"] = "red"
                self.test_report_insert_text(
                    "{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description,
                                                                                   units, result, lower_limit,
                                                                                   upper_limit, status))
                sub_section += 1

                # Opportunity to abort here
                if self.abort_requested:
                    self.test_running = False
                    return False

            except IndexError:
                # We've reached the end
                break

        # End the test
        self.sa.set_continuous_sweep(True)
        self.sg.set_output_enable(False)
        if standalone:
            del self.test_jig  # Release the serial port
            self.test_running = False

        # Update the test status
        self.rx_paths_label["text"] = "Test complete (failures: {})".format(fail_count)
        if standalone:
            self.production_test_label["text"] = ""
            if fail_count == 0:
                overall_status = "PASS"
                self.overall_status_label["text"] = "TEST PASSED"
                self.overall_status_label["background"] = "green"
            else:
                overall_status = "FAIL"
                self.overall_status_label["text"] = "TEST FAILED"
                self.overall_status_label["background"] = "red"

            # Create the test report ("(P)" suffix for partial)
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt". \
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,
                       self.uut_part_number_entry.get(), self.uut_revision_entry.get().capitalize(),
                       self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                f.write(self.test_report_text.get('1.0', END))

            self.lock_ui(False)
            self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_rx_attenuation(self, standalone=True):
        # Start test running
        self.test_running = True
        self.rx_attenuation_label["text"] = "Test in progress..."

        fail_count = 0
        section = 3
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.rx_attenuation_label["text"] = "Test in progress..."

            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.rx_attenuation_button["text"]))

            if ok:
                # Display the required set-up image
                self.show_hardware_setup(iCTSTestSetupTypes.TEST_UUT_RF_BOARD_RX_PATHS)

                # Initialise the test equipment
                ok = self.initialise_test_equipment(True, True)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.rx_attenuation_button["text"]))

        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False

            # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")

        # The test frequency and associated IF/LO
        test_freq_Hz = int(1000e6)
        IF_freq_Hz = int(2355e6)
        LO_freq_Hz = int(3355e6)

        # Initialise the UUT to known state
        # Select Test Jig Rx mode
        # Set Rx Attenuation to 0
        # Set the Rx path to 2
        # Set the Synth (LO) frequency
        ok = self.uut_initialise()
        ok &= self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_RX_MODE)
        ok &= self.test_jig.set_rx_attenuator(0)
        ok &= self.test_jig.set_rx_path(CtsTestJigRfBoardRxPaths.RX2_800_2000_MHZ)
        ok &= self.test_jig.set_synth_frequency_mhz(LO_freq_Hz / int(1e6))
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Check Synth is locked
        ok, synth_locked = self.test_jig.get_synth_lock_detect()
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        if not synth_locked:
            self.test_report_insert_text("Synth is not locked\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # Apply Spectrum Analyser settings
        ok = self.sa.set_centre_frequency_Hz(IF_freq_Hz)
        ok &= self.sa.set_span_Hz(int(1e6))
        ok &= self.sa.set_attenuation_dB(0)
        ok &= self.sa.set_reference_level_dBm(-10.0)
        ok &= self.sa.set_continuous_sweep(False)
        if not ok:
            self.test_report_insert_text("TE command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        s2p = S2PFileReader()

        # Apply Signal Generator settings, correcting the amplitude
        test_ampl_dBm = self.RX_TEST_AMPLITUDE + \
                        (s2p.get_s_parameter(test_freq_Hz, 3, self.signal_generator_to_uut_rf_board_ant_s2p_file,
                                             True) * -1)
        ok = self.sg.set_frequency_Hz(test_freq_Hz)
        ok &= self.sg.set_output_power_dBm(test_ampl_dBm)
        ok &= self.sg.set_output_enable(True)
        if not ok:
            self.test_report_insert_text("TE command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # 3.1: Reference Level
        ref_level = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + \
                                          (s2p.get_s_parameter(IF_freq_Hz, 3,
                                                               self.spectrum_analyser_to_uut_rf_board_if_s2p_file,
                                                               True) * -1)))
        description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)
        result = ref_level
        if lower_limit <= result <= upper_limit:
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text(
            "{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units,
                                                                           result, lower_limit, upper_limit, status))
        sub_section += 1

        # 3.x: Loop around measuring the attenuation step changes using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)

                # The description field contains the attenution value
                try:
                    atten_dB = float(re.sub('dB State', '', description).strip())
                except:
                    self.test_report_insert_text("Invalid test parameter\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                # Apply the Rx attenuation
                atten_index = int(atten_dB / 0.5)
                ok = self.test_jig.set_rx_attenuator(atten_index)
                if not ok:
                    self.test_report_insert_text("Serial command failure\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                sleep(1)

                # Measure the peak tone power and apply correction
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() +
                                             (s2p.get_s_parameter(IF_freq_Hz, 3,
                                                                  self.spectrum_analyser_to_uut_rf_board_if_s2p_file,
                                                                  True) * -1)))
                result = ref_level - peak
                if lower_limit <= result <= upper_limit:
                    status = "Pass"
                else:
                    status = "Fail"
                    fail_count += 1
                    self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                    self.overall_status_label["background"] = "red"
                self.test_report_insert_text(
                    "{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description,
                                                                                   units, result, lower_limit,
                                                                                   upper_limit, status))
                sub_section += 1

                # Opportunity to abort here
                if self.abort_requested:
                    self.test_running = False
                    return False

            except IndexError:
                # We've reached the end
                break

        # End the test
        self.sa.set_continuous_sweep(True)
        self.sg.set_output_enable(False)
        if standalone:
            del self.test_jig  # Release the serial port
            self.test_running = False

        # Update the test status
        self.rx_attenuation_label["text"] = "Test complete (failures: {})".format(fail_count)
        if standalone:
            self.production_test_label["text"] = ""
            if fail_count == 0:
                overall_status = "PASS"
                self.overall_status_label["text"] = "TEST PASSED"
                self.overall_status_label["background"] = "green"
            else:
                overall_status = "FAIL"
                self.overall_status_label["text"] = "TEST FAILED"
                self.overall_status_label["background"] = "red"

            # Create the test report ("(P)" suffix for partial)
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt". \
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,
                       self.uut_part_number_entry.get(), self.uut_revision_entry.get().capitalize(),
                       self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                f.write(self.test_report_text.get('1.0', END))

            self.lock_ui(False)
            self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_tx_paths(self, standalone=True):
        # Start test running
        self.test_running = True
        self.tx_paths_label["text"] = "Test in progress..."

        fail_count = 0
        section = 4
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.tx_paths_label["text"] = "Test in progress..."

            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.tx_paths_button["text"]))

            if ok:
                # Display the required set-up image
                self.show_hardware_setup(iCTSTestSetupTypes.TEST_UUT_RF_BOARD_TX_PATHS)

                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, True)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.tx_paths_button["text"]))

        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False

            # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")

        # Initialise the UUT to known state
        # Select the Synth Tx path
        # Disable the Mixer
        # Select Test Jig Tx mode
        # Set Tx Attenuation to 0
        # Select the Tx path to antenna
        ok = self.uut_initialise()
        ok &= self.test_jig.set_gpo_signal(CtsTestJigGpoSignals.UUT_RF_BOARD_NTX_RX_SEL, False)
        ok &= self.test_jig.set_gpo_signal(CtsTestJigGpoSignals.UUT_RF_BOARD_RX_PATH_MIXER_EN, False)
        ok &= self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_TX_MODE)
        ok &= self.test_jig.set_tx_attenuator(0)
        ok &= self.test_jig.set_rx_path(CtsTestJigRfBoardRxPaths.TX)
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Apply common Spectrum Analyser settings
        ok = self.sa.set_span_Hz(int(1e6))
        ok &= self.sa.set_attenuation_mode(True)
        ok &= self.sa.set_reference_level_dBm(20.0)
        ok &= self.sa.set_continuous_sweep(False)
        if not ok:
            self.test_report_insert_text("TE command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        s2p = S2PFileReader()
        tx_path_curr = -1

        # 4.x: Loop around measuring fundamental and harmonic levels using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)

                # The description field contains the Tx path #, the output test frequency
                # and whether the test frequency is the fundamental or harmonic term
                descr_chunks = str(description).strip().split(", ")
                tx_path = int(re.sub('TX', '', descr_chunks[0].strip()))
                if "GHz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('GHz', '', descr_chunks[1].strip())) * 1e9)
                elif "MHz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('MHz', '', descr_chunks[1].strip())) * 1e6)
                elif "kHz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('kHz', '', descr_chunks[1].strip())) * 1e3)
                elif "Hz" in descr_chunks[1]:
                    test_freq_Hz = int(float(re.sub('Hz', '', descr_chunks[1].strip())))
                else:
                    self.test_report_insert_text("Invalid test parameter\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                is_fundamental = True if "Fund" in descr_chunks[2] else False

                # Determine the Synth output frequency and Tx divider value
                if tx_path == 0:
                    tx_path = CtsTestJigRfBoardTxPaths.TX0_20_800_MHZ
                    synth_freq_Hz = test_freq_Hz * 8
                    divide_ratio = CtsTestJigRfBoardTxDividerValues.DIVIDE_RATIO_8
                elif tx_path == 1:
                    tx_path = CtsTestJigRfBoardTxPaths.TX1_700_1500_MHZ
                    synth_freq_Hz = test_freq_Hz * 4
                    divide_ratio = CtsTestJigRfBoardTxDividerValues.DIVIDE_RATIO_4
                elif tx_path == 2:
                    tx_path = CtsTestJigRfBoardTxPaths.TX2_1200_2700_MHZ
                    synth_freq_Hz = test_freq_Hz * 2
                    divide_ratio = CtsTestJigRfBoardTxDividerValues.DIVIDE_RATIO_2
                elif tx_path == 3:
                    tx_path = CtsTestJigRfBoardTxPaths.TX3_2400_6000_MHZ
                    synth_freq_Hz = test_freq_Hz
                    divide_ratio = CtsTestJigRfBoardTxDividerValues.DIVIDE_RATIO_1

                # Set the Tx path (if different) and Tx divider value
                if tx_path_curr != tx_path:
                    tx_path_curr = tx_path
                    ok = self.test_jig.set_tx_path(tx_path)
                    ok &= self.test_jig.set_tx_divider_value(divide_ratio)
                    if not ok:
                        self.test_report_insert_text("Serial command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)

                # Set the Synth frequency (if this is a fundamental test frequency)
                if is_fundamental:
                    ok = self.test_jig.set_synth_frequency_mhz(synth_freq_Hz / int(1e6))
                    if not ok:
                        self.test_report_insert_text("Serial command failure\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)

                # Check Synth is locked
                ok, synth_locked = self.test_jig.get_synth_lock_detect()
                if not ok:
                    self.test_report_insert_text("Serial command failure\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                if not synth_locked:
                    self.test_report_insert_text("Synth is not locked\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                # Update Spectrum Analyser centre frequency
                ok = self.sa.set_centre_frequency_Hz(test_freq_Hz)
                if not ok:
                    self.test_report_insert_text("TE command failure\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                    # Measure the peak tone power and apply correction
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() +
                                             (s2p.get_s_parameter(test_freq_Hz, 3,
                                                                  self.spectrum_analyser_to_uut_rf_board_ant_s2p_file,
                                                                  True) * -1)))

                # Determine the test result
                if is_fundamental:
                    fundamental = peak
                    result = fundamental
                else:
                    result = peak - fundamental

                if lower_limit <= result <= upper_limit:
                    status = "Pass"
                else:
                    status = "Fail"
                    fail_count += 1
                    self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                    self.overall_status_label["background"] = "red"
                self.test_report_insert_text(
                    "{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description,
                                                                                   units, result, lower_limit,
                                                                                   upper_limit, status))
                sub_section += 1

                # Opportunity to abort here
                if self.abort_requested:
                    self.test_running = False
                    return False

            except IndexError:
                # We've reached the end
                break

        # End the test
        self.sa.set_continuous_sweep(True)
        if standalone:
            del self.test_jig  # Release the serial port
            self.test_running = False

        # Update the test status
        self.tx_paths_label["text"] = "Test complete (failures: {})".format(fail_count)
        if standalone:
            self.production_test_label["text"] = ""
            if fail_count == 0:
                overall_status = "PASS"
                self.overall_status_label["text"] = "TEST PASSED"
                self.overall_status_label["background"] = "green"
            else:
                overall_status = "FAIL"
                self.overall_status_label["text"] = "TEST FAILED"
                self.overall_status_label["background"] = "red"

            # Create the test report ("(P)" suffix for partial)
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt". \
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,
                       self.uut_part_number_entry.get(), self.uut_revision_entry.get().capitalize(),
                       self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                f.write(self.test_report_text.get('1.0', END))

            self.lock_ui(False)
            self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_tx_attenuation(self, standalone=True):
        # Start test running
        self.test_running = True
        self.tx_attenuation_label["text"] = "Test in progress..."

        fail_count = 0
        section = 5
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.tx_attenuation_label["text"] = "Test in progress..."

            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.tx_attenuation_button["text"]))

            if ok:
                # Display the required set-up image
                self.show_hardware_setup(iCTSTestSetupTypes.TEST_UUT_RF_BOARD_TX_PATHS)

                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, True)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.tx_attenuation_button["text"]))

        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False

        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")

        # The test frequency and associated Tx path, divide ratio and Synth output frequency
        # Using maximum frequency to avoid amplifier saturation effects
        test_freq_Hz = int(6000e6)
        tx_path = CtsTestJigRfBoardTxPaths.TX3_2400_6000_MHZ
        divide_ratio = CtsTestJigRfBoardTxDividerValues.DIVIDE_RATIO_1
        synth_freq_Hz = test_freq_Hz

        # Initialise the UUT to known state
        # Select the Synth Tx path
        # Disable the Mixer
        # Select Test Jig Tx mode
        # Set Tx Attenuation to 0
        # Select the Tx path to antenna
        # Set the Tx path
        # Set the Tx Tx divider value
        # Set the Synth output frequency
        ok = self.uut_initialise()
        ok &= self.test_jig.set_gpo_signal(CtsTestJigGpoSignals.UUT_RF_BOARD_NTX_RX_SEL, False)
        ok &= self.test_jig.set_gpo_signal(CtsTestJigGpoSignals.UUT_RF_BOARD_RX_PATH_MIXER_EN, False)
        ok &= self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_TX_MODE)
        ok &= self.test_jig.set_tx_attenuator(0)
        ok &= self.test_jig.set_rx_path(CtsTestJigRfBoardRxPaths.TX)
        ok &= self.test_jig.set_tx_path(tx_path)
        ok &= self.test_jig.set_tx_divider_value(divide_ratio)
        ok &= self.test_jig.set_synth_frequency_mhz(synth_freq_Hz / int(1e6))
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Check Synth is locked
        ok, synth_locked = self.test_jig.get_synth_lock_detect()
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        if not synth_locked:
            self.test_report_insert_text("Synth is not locked\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # Apply Spectrum Analyser settings
        ok = self.sa.set_centre_frequency_Hz(test_freq_Hz)
        ok &= self.sa.set_span_Hz(int(1e6))
        ok &= self.sa.set_attenuation_mode(True)
        ok &= self.sa.set_reference_level_dBm(20.0)
        ok &= self.sa.set_continuous_sweep(False)
        if not ok:
            self.test_report_insert_text("TE command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False

        s2p = S2PFileReader()

        # 5.1: Reference Level
        ref_level = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + \
                                          (s2p.get_s_parameter(test_freq_Hz, 3,
                                                               self.spectrum_analyser_to_uut_rf_board_ant_s2p_file,
                                                               True) * -1)))
        description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)
        result = ref_level
        if lower_limit <= result <= upper_limit:
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text(
            "{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units,
                                                                           result, lower_limit, upper_limit, status))
        sub_section += 1

        # 5.x: Loop around measuring the attenuation step changes using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section - 1, sub_section - 1)

                # The description field contains the attenution value
                try:
                    atten_dB = float(re.sub('dB State', '', description).strip())
                except:
                    self.test_report_insert_text("Invalid test parameter\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                # Apply the Rx attenuation
                atten_index = int(atten_dB / 0.5)
                ok = self.test_jig.set_tx_attenuator(atten_index)
                if not ok:
                    self.test_report_insert_text("Serial command failure\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                sleep(1)

                # Measure the peak tone power and apply correction
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() +
                                             (s2p.get_s_parameter(test_freq_Hz, 3,
                                                                  self.spectrum_analyser_to_uut_rf_board_ant_s2p_file,
                                                                  True) * -1)))
                result = ref_level - peak
                if lower_limit <= result <= upper_limit:
                    status = "Pass"
                else:
                    status = "Fail"
                    fail_count += 1
                    self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                    self.overall_status_label["background"] = "red"
                self.test_report_insert_text(
                    "{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description,
                                                                                   units, result, lower_limit,
                                                                                   upper_limit, status))
                sub_section += 1

                # Opportunity to abort here
                if self.abort_requested:
                    self.test_running = False
                    return False

            except IndexError:
                # We've reached the end
                break

        # End the test
        self.sa.set_continuous_sweep(True)
        if standalone:
            del self.test_jig  # Release the serial port
            self.test_running = False

        # Update the test status
        self.tx_attenuation_label["text"] = "Test complete (failures: {})".format(fail_count)
        if standalone:
            self.production_test_label["text"] = ""
            if fail_count == 0:
                overall_status = "PASS"
                self.overall_status_label["text"] = "TEST PASSED"
                self.overall_status_label["background"] = "green"
            else:
                overall_status = "FAIL"
                self.overall_status_label["text"] = "TEST FAILED"
                self.overall_status_label["background"] = "red"

            # Create the test report ("(P)" suffix for partial)
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt". \
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,
                       self.uut_part_number_entry.get(), self.uut_revision_entry.get().capitalize(),
                       self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                f.write(self.test_report_text.get('1.0', END))

            self.lock_ui(False)
            self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_calibrate_set_up(self):
        # Start test running
        self.test_running = True
        self.calibrate_setup_label["text"] = "Test in progress..."

        # Lock the UI down
        self.lock_ui(True)

        # Set the overall status
        self.overall_status_label["text"] = "TEST IN PROGRESS (PASS)"
        self.overall_status_label["background"] = "green"

        # Clear the report
        self.test_report_text.delete('1.0', END)

        # Add initial info to the report, such as date/time
        self.test_report_insert_text(self.calibrate_setup_button["text"] + "\n\n")

        self.test_report_insert_text("Test Version: {}\n\n".format(self.TEST_VERSION))
        self.now = datetime.now()
        self.test_report_insert_text("{:02d}-{:02d}-{:04d} {:02d}:{:02d}:{:02d}\n\n"
                                     .format(self.now.day, self.now.month, self.now.year, self.now.hour,
                                             self.now.minute, self.now.second))

        # Change the Production Test button to an Abort Test button
        self.production_test_button["text"] = ">> ABORT TEST <<"
        self.production_test_button["command"] = self.request_abort_test
        self.production_test_label["text"] = "Test in progress..."

        # Initialise the test equipment
        ok = self.initialise_test_equipment(False, False)
        if not ok or self.abort_requested:
            self.test_running = False
            return False

        s2p = S2PFileReader()

        # -----------------------------------------------------------------------------
        # PATH: SIGNAL GENERATOR TO UUT RF BOARD ANTENNA PORT
        # -----------------------------------------------------------------------------

        # Select Test Jig Rx mode
        ok = self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_RX_MODE)
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Display the required set-up image
        self.test_report_insert_text("PATH: SIGNAL GENERATOR TO UUT RF BOARD ANTENNA PORT\n")
        self.show_hardware_setup(iCTSTestSetupTypes.CALIBRATE_SIG_GEN_TO_UUT_RF_BOARD_ANT)

        # Validate calibration file
        self.test_report_insert_text("Validating calibration file: {}... "
                                     .format(
            self.signal_generator_to_uut_rf_board_ant_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
        if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3, self.signal_generator_to_uut_rf_board_ant_s2p_file) is not None \
                and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3,
                                        self.signal_generator_to_uut_rf_board_ant_s2p_file) is not None:
            self.test_report_insert_text("OK\n")
        else:
            self.test_report_insert_text("Error\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # -----------------------------------------------------------------------------
        # PATH: SPECTRUM ANALYSER TO UUT RF BOARD IF PORT
        # -----------------------------------------------------------------------------

        # Display the required set-up image
        self.test_report_insert_text("\nPATH: SPECTRUM ANALYSER TO UUT RF BOARD IF PORT\n")
        self.show_hardware_setup(iCTSTestSetupTypes.CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_IF)

        # Validate calibration file
        self.test_report_insert_text("Validating calibration file: {}... "
                                     .format(
            self.spectrum_analyser_to_uut_rf_board_if_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
        if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3, self.spectrum_analyser_to_uut_rf_board_if_s2p_file) is not None \
                and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3,
                                        self.spectrum_analyser_to_uut_rf_board_if_s2p_file) is not None:
            self.test_report_insert_text("OK\n")
        else:
            self.test_report_insert_text("Error\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # -----------------------------------------------------------------------------
        # PATH: SPECTRUM ANALYSER TO UUT RF BOARD ANTENNA PORT
        # -----------------------------------------------------------------------------

        # Select Test Jig Tx mode
        ok = self.test_jig.set_test_jig_rf_path(CtsTestJigRfPaths.RF_BOARD_TEST_TX_MODE)
        if not ok:
            self.test_report_insert_text("Serial command failure\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Display the required set-up image
        self.test_report_insert_text("\nPATH: SPECTRUM ANALYSER TO UUT RF BOARD ANTENNA PORT\n")
        self.show_hardware_setup(iCTSTestSetupTypes.CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_ANT)

        # Validate calibration file
        self.test_report_insert_text("Validating calibration file: {}... " \
                                     .format(
            self.spectrum_analyser_to_uut_rf_board_ant_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
        if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3,
                               self.spectrum_analyser_to_uut_rf_board_ant_s2p_file) is not None \
                and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3,
                                        self.spectrum_analyser_to_uut_rf_board_ant_s2p_file) is not None:
            self.test_report_insert_text("OK\n")
        else:
            self.test_report_insert_text("Error\n")
            self.test_running = False
            self.request_abort_test()
            return False

        # End the test:
        del self.test_jig  # Release the serial port
        if not self.test_running:
            return False
        else:
            self.test_running = False

            # Update the test status
            self.production_test_label["text"] = "Test complete"
            self.overall_status_label["text"] = "TEST PASSED"
            self.overall_status_label["background"] = "green"
            self.test_report_insert_text(
                "\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))

            self.lock_ui(False)
            self.psu.set_enabled(False)
            return True

    def uut_initialise(self):
        """
        Enables the power rails to the UUT
        Enables the Synth
        Selects the Synth Rx path
        Enables the Rx path mixer
        Initialises the Synth
        :return: True if all commands succeeded, else False
        """
        ret_val = True
        gpo_lines = [CtsTestJigGpoSignals.UUT_RF_BOARD_P3V3_EN,
                     CtsTestJigGpoSignals.UUT_RF_BOARD_P5V0_EN,
                     CtsTestJigGpoSignals.UUT_RF_BOARD_P3V3_TX_EN,
                     CtsTestJigGpoSignals.UUT_RF_BOARD_P5V0_TX_EN,
                     CtsTestJigGpoSignals.UUT_RF_BOARD_SYNTH_EN,
                     CtsTestJigGpoSignals.UUT_RF_BOARD_NTX_RX_SEL,
                     CtsTestJigGpoSignals.UUT_RF_BOARD_RX_PATH_MIXER_EN]

        # Set the GPO lines
        for gpo in gpo_lines:
            ret_val &= self.test_jig.set_gpo_signal(gpo, True)
            sleep(0.2)
        
        # Initialise the Synth
        ret_val &= self.test_jig.initialise_synth()

        # Delay Test Jig and UUT to settle
        sleep(1)

        return ret_val

    def test_report_insert_text(self, text=""):
        # Function ensures the vertical scroll bar moves with the text
        self.test_report_text.insert(END, text)
        self.test_report_text.see(END)

    def show_hardware_setup(self, setup_type: iCTSTestSetupTypes):
        # Create a popup window
        self.popup = Toplevel(self)

        # Set the fixed window size
        window_width = 686
        window_height = 650
        self.popup.minsize(window_width, window_height)
        self.popup.maxsize(window_width, window_height)

        # Get the main window position
        main_win_x = self.winfo_rootx()
        main_win_y = self.winfo_rooty()

        # Add offset
        main_win_x += 205
        main_win_y += -68

        # Set the position of the popup window to the centre of the main window and keep on top of everything
        self.popup.geometry(f'+{main_win_x}+{main_win_y}')
        self.popup.wm_transient(self)
        # self.popup.attributes('-topmost', True)
        self.popup.grab_set()

        # Display the set-up image and wait for button press
        self.popup.title("Set-Up: {}".format(setup_type.value))
        self.popup.iconbitmap("./images/kirintec_logo.ico")
        self.popup.option_add("*font", "Arial 9")
        self.popup.protocol("WM_DELETE_WINDOW", self.disable_event)  # Disables the window's Close button
        if setup_type == iCTSTestSetupTypes.TEST_UUT_RF_BOARD_RX_PATHS:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_TEST_UUT_RF_BOARD_RX_PATHS))
        elif setup_type == iCTSTestSetupTypes.TEST_UUT_RF_BOARD_TX_PATHS:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_TEST_UUT_RF_BOARD_TX_PATHS))
        elif setup_type == iCTSTestSetupTypes.TEST_UUT_RF_BOARD_NO_RF_PATHS:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_TEST_UUT_RF_BOARD_NO_RF_PATHS))
        elif setup_type == iCTSTestSetupTypes.CALIBRATE_SIG_GEN_TO_UUT_RF_BOARD_ANT:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_CALIBRATE_SIG_GEN_TO_UUT_RF_BOARD_ANT_PATH))
        elif setup_type == iCTSTestSetupTypes.CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_IF:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_IF_PATH))
        elif setup_type == iCTSTestSetupTypes.CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_ANT:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_CALIBRATE_SPEC_AN_TO_UUT_RF_BOARD_ANT_PATH))
        label = Label(self.popup, image=img)
        label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
        var = IntVar()
        close_button = Button(self.popup, text=">> FOLLOW THE INSTRUCTIONS THEN CLICK HERE TO CONTINUE <<",
                              command=lambda: var.set(1))
        close_button.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        close_button.wait_variable(var)
        self.popup.destroy()


if __name__ == "__main__":
    main_window = iCTSRFBoardTest()
    main_window.mainloop()
