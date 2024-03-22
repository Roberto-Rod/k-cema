#!/usr/bin/env python3

# Tkinter imports
from tkinter import *
from tkinter.ttk import *

# Standard library imports
from threading import Thread
from time import sleep
from  datetime import datetime, timedelta
from nbconvert import PythonExporter
import papermill as pm
import nbformat, re, os, sys, subprocess

# Third-party imports
# Requires the foillowing packages installed on the PC: pillow, numpy, seaborn, nbconvert
from PIL import ImageTk, Image

# Local application imports
# Requires the foillowing packages installed on the PC: fabric, decorator
from ssh import *
from s2p_file_reader import *
from test_limits_production import *
from test_limits_engineering import *

# Test Equipment imports
from test_equipment.power_supply_cpx400dp import *
from test_equipment.power_supply_qpx1200sp import *
from test_equipment.power_supply_72_xxxx import *
from test_equipment.signal_generator_hp83752a import *
from test_equipment.signal_generator_n51x3b import *
from test_equipment.spectrum_analyser_hp8563e import *
from test_equipment.spectrum_analyser_fsw import *
from test_equipment.spectrum_analyser_n90xxb import *

class NTMMBeHBRFBoardTest(Tk):
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
    DEBUG_MODE = False          # Set True to remove EMA boot time from test, PSU control is bypassed, EMA is assumed to be powered, booted and transceiver initialised
    ENGINEERING_MODE = False    # Set True to run an extended set of tests using the engineering test limits file
    UI_VERSION = "1.0.0"
    TEST_VERSION = "1.0.0"
    APP_NAME = "NTM MB-eHB RF Board Test Utility [v{}]".format(UI_VERSION)
    APP_LOGO_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "kirintec_logo.ico")
    TEST_REPORT_REL_DIR = os.path.join(APP_PATH + os.sep + "test_reports" + os.sep)
    CALIBRATION_REL_DIR = os.path.join(APP_PATH + os.sep + "calibration" + os.sep)
    PLOTS_REL_DIR = os.path.join(APP_PATH + os.sep + "plots" + os.sep)
    SETUP_TX_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_tx.png")
    SETUP_RX_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_rx.png")
    SETUP_OBS_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_obs.png")
    SETUP_TX_RX_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_tx_rx.png")
    SETUP_TX_OBS_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_tx_obs.png")
    SETUP_NO_RF_PATH = os.path.join(APP_PATH + os.sep + "images" + os.sep + "setup_no_rf.png")
    OCPI_IQ_CAPTURE_NB_IN_FILENAME = "ocpi_iq_capture.ipynb"
    OCPI_IQ_CAPTURE_NB_IN_PATH = os.path.join(APP_PATH + os.sep + OCPI_IQ_CAPTURE_NB_IN_FILENAME)
    OCPI_IQ_CAPTURE_NB_OUT_FILENAME = "output_" + OCPI_IQ_CAPTURE_NB_IN_FILENAME
    OCPI_IQ_CAPTURE_NB_OUT_PATH = os.path.join(APP_PATH + os.sep + OCPI_IQ_CAPTURE_NB_OUT_FILENAME)
    OCPI_IQ_CAPTURE_DATA_OUT_PATH = os.path.join(APP_PATH + os.sep + "capture.iq")
    OCPI_IQ_CAPTURE_PLOT_OUT_PATH = os.path.join(APP_PATH + os.sep + "fft_plot.png")
    EMA_HOSTNAME = "EMA-000000"
    ROOT_PASSWORD = "gbL^58TJc"
    EMA_BOOT_DELAY_S = 65
    XCVR_INIT_DELAY_S = 60
    MIN_TEST_FREQ_HZ = int(400e6)   # 400 MHz
    MAX_TEST_FREQ_HZ = int(8e9)     # 8 GHz
    PSU_VOLTAGE_V = 28.0
    PSU_CURRENT_A = 3.0

    # EMA SSH commands
    EMA_TEST_INITIALISE_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_initialise_ema.py -v"
    EMA_XCVRTOOL_CMD = "killall xcvrtool;/run/media/mmcblk0p2/test/xcvrtool &"
    EMA_INITIALISE_XCVR_CMD = "(echo initialise | nc 127.0.0.1:7000 &); sleep 1; killall nc"
    EMA_TEST_REBOOT_CMD = "/sbin/reboot"
    EMA_TEST_GET_REG_DGTR_CTRL_CMD = "/sbin/devmem 0x40080584 32"
    EMA_TEST_GET_LTC2991_0_CH_VOLTS_CMD = "cd /run/media/mmcblk0p2/test/;python3 ltc2991.py"
    EMA_TEST_GET_LTC2991_1_CH_VOLTS_CMD = "cd /run/media/mmcblk0p2/test/;python3 ltc2991.py 5"
    EMA_TEST_SET_TX_PATH_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_tx_set_path.py {} -v"
    EMA_TEST_SET_RX_PATH_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_rx_set_path.py {} -v"
    EMA_TEST_SET_SYNTH_PATH_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_set_synth_path.py {} -v"
    EMA_TEST_SET_XCVR_TX_PATH_CMD = "(echo set tx path {} | nc 127.0.0.1:7000 &);sleep 1;killall nc"
    EMA_TEST_SET_XCVR_TX_ATT_CMD = "(echo set tx att {} | nc 127.0.0.1:7000 &);sleep 1;killall nc"
    EMA_TEST_SET_XCVR_TX_MODE_CMD = "(echo tx mode | nc 127.0.0.1:7000 &);sleep 1;killall nc"
    EMA_TEST_SET_XCVR_FREQ_CMD = "(echo set frequency {} | nc 127.0.0.1:7000 &);sleep 1;killall nc"
    EMA_TEST_SET_XCVR_SYNTH_CMD = "(echo set synth {} | nc 127.0.0.1:7000 &);sleep 1;killall nc"
    EMA_TEST_SET_TEST_TONE_CMD = "/sbin/devmem 0x4001C040 32 0x1;/sbin/devmem 0x4001C000 32 0x2"
    EMA_TEST_SET_TEST_TONE_AMP_CMD = "/sbin/devmem 0x4001D000 32 0x20000"
    EMA_TEST_SET_RX_LNA_BYPASS_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_rx_set_lna_bypass.py True -v"
    EMA_TEST_SET_RX_LNA_ENABLE_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_rx_set_lna_bypass.py False -v"
    EMA_TEST_SET_CONFIG_DATA_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_set_hardware_config.py {} {} {} {}"
    EMA_TEST_GET_CONFIG_DATA_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_get_hardware_config.py {}"
    EMA_TEST_SET_XCVR_TX_ENABLE_CMD = "/sbin/devmem 0x40015000 32 0x3"
    EMA_TEST_SET_XCVR_TX_DISABLE_CMD = "/sbin/devmem 0x40015000 32 0x1"
    EMA_TEST_SET_XCVR_RESET_CMD = "/sbin/devmem 0x40015000 32 0x0"
    EMA_TEST_SET_TX_ATTENUATION_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_dblr_set_att.py {} {} -v"
    EMA_TEST_SET_DDS_TONE_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_dds_tone.py {} -v"
    EMA_TEST_RESET_DDS_CMD = "cd /run/media/mmcblk0p2/test/;python3 sys_test_initialise_dds.py"

    # Calibration files
    uut_to_signal_generator_s2p_file = CALIBRATION_REL_DIR + "uut_to_signal_generator.s2p"
    uut_to_spectrum_analyser_s2p_file = CALIBRATION_REL_DIR + "uut_to_spectrum_analyser.s2p"

    # Equipment set-up types
    setup_type = {}
    setup_type[0] = "Tx"
    setup_type[1] = "Rx"
    setup_type[2] = "Obs"
    setup_type[3] = "Tx, Rx"
    setup_type[4] = "Tx, Obs"
    setup_type[5] = "No RF"

    # Test objects
    psu = None
    sg = None
    sa = None
    ema_ssh = None
    devmem = None
    test_limits = None
    popup = None
    now = None

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
        self.title(self.APP_NAME)
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

        # UUT Part Number label and combobox
        self.uut_part_number = StringVar()
        self.uut_part_number_label = Label(self.uut_details_frame, text="Select the UUT Part Number:")
        self.uut_part_number_label.grid(column=0, row=1, padx=3, pady=6, sticky=NSEW)
        self.uut_part_number_combobox = Combobox(self.uut_details_frame, textvariable=self.uut_part_number)
        self.uut_part_number_combobox["values"] = ("KT-000-0202-00", "KT-000-0202-01")
        self.uut_part_number_combobox.current(0)
        self.uut_part_number_combobox.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)

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
        self.production_test_button = Button(self.test_modules_frame, text=">> PRODUCTION TEST <<", command=self.production_test_routine, width=26)
        self.production_test_button.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.production_test_label = Label(self.test_modules_frame, text="")
        self.production_test_label.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)

        # Built-In Test button and label
        self.built_in_test_button = Button(self.test_modules_frame, text="BUILT-IN TEST", command=self.built_in_test_routine)
        self.built_in_test_button.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.built_in_test_label = Label(self.test_modules_frame, text="")
        self.built_in_test_label.grid(column=1, row=2, padx=3, pady=3, sticky=NSEW)

        # Hardware Configuration Data button and label
        self.hardware_config_data_button = Button(self.test_modules_frame, text="HARDWARE CONFIG DATA", command=self.hardware_config_data_routine)
        self.hardware_config_data_button.grid(column=0, row=3, padx=3, pady=3, sticky=NSEW)
        self.hardware_config_data_label = Label(self.test_modules_frame, text="")
        self.hardware_config_data_label.grid(column=1, row=3, padx=3, pady=3, sticky=NSEW)

        # DDS Tx Paths button and label
        self.dds_tx_paths_button = Button(self.test_modules_frame, text="DDS TX PATHS", command=self.dds_tx_paths_routine)
        self.dds_tx_paths_button.grid(column=0, row=4, padx=3, pady=3, sticky=NSEW)
        self.dds_tx_paths_label = Label(self.test_modules_frame, text="")
        self.dds_tx_paths_label.grid(column=1, row=4, padx=3, pady=3, sticky=NSEW)

        # DDS Tx Attenuation button and label
        self.dds_tx_attenuation_button = Button(self.test_modules_frame, text="DDS TX ATTENUATION", command=self.dds_tx_attenuation_routine)
        self.dds_tx_attenuation_button.grid(column=0, row=5, padx=3, pady=3, sticky=NSEW)
        self.dds_tx_attenuation_label = Label(self.test_modules_frame, text="")
        self.dds_tx_attenuation_label.grid(column=1, row=5, padx=3, pady=3, sticky=NSEW)

        # Transceiver Tx Paths button and label
        self.transceiver_tx_paths_button = Button(self.test_modules_frame, text="XCVR TX PATHS", command=self.xcvr_tx_paths_routine)
        self.transceiver_tx_paths_button.grid(column=0, row=6, padx=3, pady=3, sticky=NSEW)
        self.transceiver_tx_paths_label = Label(self.test_modules_frame, text="")
        self.transceiver_tx_paths_label.grid(column=1, row=6, padx=3, pady=3, sticky=NSEW)

        # Rx Paths button and label
        self.rx_paths_button = Button(self.test_modules_frame, text="RX PATHS", command=self.rx_paths_routine)
        self.rx_paths_button.grid(column=0, row=7, padx=3, pady=3, sticky=NSEW)
        self.rx_paths_label = Label(self.test_modules_frame, text="")
        self.rx_paths_label.grid(column=1, row=7, padx=3, pady=3, sticky=NSEW)

        # Observation Rx Paths button and label
        self.observation_rx_paths_button = Button(self.test_modules_frame, text="OBSERVATION RX PATHS", command=self.obs_rx_paths_routine)
        self.observation_rx_paths_button.grid(column=0, row=8, padx=3, pady=3, sticky=NSEW)
        self.observation_rx_paths_label = Label(self.test_modules_frame, text="")
        self.observation_rx_paths_label.grid(column=1, row=8, padx=3, pady=3, sticky=NSEW)

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
        self.dc_power_supply_combobox["values"] = ("72-XXXX", "CPX400DP", "QPX1200SP")
        self.dc_power_supply_combobox.current(0)
        self.dc_power_supply_combobox.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_button = Button(self.test_equipment_frame, text="Check", command=self.check_dc_power_supply)
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
        self.rf_signal_generator_button = Button(self.test_equipment_frame, text="Check", command=self.check_rf_signal_generator)
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
        self.rf_spectrum_analyser_button = Button(self.test_equipment_frame, text="Check", command=self.check_rf_spectrum_analyser)
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
        self.test_report_text.bind("<Key>", lambda e: self.ctrlEvent(e)) # Makes the Text widget read-only while allowing CTRL+C event
        self.test_report_text_xs = Scrollbar(self.test_report_frame, orient=HORIZONTAL, command=self.test_report_text.xview)
        self.test_report_text_ys = Scrollbar(self.test_report_frame, orient=VERTICAL, command=self.test_report_text.yview)
        self.test_report_text['xscrollcommand'] = self.test_report_text_xs.set
        self.test_report_text['yscrollcommand'] = self.test_report_text_ys.set
        self.test_report_text.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.test_report_text_xs.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.test_report_text_ys.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)

        # Overall Status frame and label
        self.overall_status_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.overall_status_frame.grid(column=0, columnspan=2, row=2, padx=3, pady=3, sticky=NSEW)
        self.overall_status_label = Label(self.overall_status_frame, text="TEST IDLE", font="Arial 11 bold", foreground="white", background="gray32", anchor=CENTER, width=101)
        self.overall_status_label.grid(column=1, row=0, padx=3, pady=3, sticky=NSEW)

        # Calibration folder button
        self.calibration_folder_button = Button(self.overall_status_frame, text="View Calibration Files", width=20, command=self.open_calibration_folder)
        self.calibration_folder_button.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
                
        # Reports folder button
        self.reports_folder_button = Button(self.overall_status_frame, text="View Test Reports", width=20, command=self.open_reports_folder)
        self.reports_folder_button.grid(column=2, row=0, padx=3, pady=3, sticky=NSEW)
    
    def ctrlEvent(self, event):
        if (12 == event.state and event.keysym == 'c'):
            return None
        else:
            return "break"
        
    def disable_event(event=None):
        pass
            
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
        elif self.dc_power_supply_combobox.get() == "QPX1200SP":
            self.psu = PowerSupplyQPX1200SP()
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
        self.uut_part_number_combobox["state"] = DISABLED if lock else NORMAL
        self.uut_revision_entry["state"] = DISABLED if lock else NORMAL
        self.uut_serial_number_entry["state"] = DISABLED if lock else NORMAL
        self.built_in_test_button["state"] = DISABLED if lock else NORMAL
        self.hardware_config_data_button["state"] = DISABLED if lock else NORMAL
        self.dds_tx_paths_button["state"] = DISABLED if lock else NORMAL
        self.dds_tx_attenuation_button["state"] = DISABLED if lock else NORMAL
        self.transceiver_tx_paths_button["state"] = DISABLED if lock else NORMAL
        self.rx_paths_button["state"] = DISABLED if lock else NORMAL
        self.observation_rx_paths_button["state"] = DISABLED if lock else NORMAL
        self.dc_power_supply_combobox["state"] = DISABLED if lock else NORMAL
        self.dc_power_supply_button["state"] = DISABLED if lock else NORMAL
        self.rf_signal_generator_combobox["state"] = DISABLED if lock else NORMAL
        self.rf_signal_generator_button["state"] = DISABLED if lock else NORMAL
        self.rf_spectrum_analyser_combobox["state"] = DISABLED if lock else NORMAL
        self.rf_spectrum_analyser_button["state"] = DISABLED if lock else NORMAL

        # Update button and label text
        if not lock:
            self.production_test_button["text"] = ">> PRODUCTION TEST <<"
            self.production_test_button["command"] = self.production_test_routine
        else:
            self.production_test_label["text"] = ""
            self.built_in_test_label["text"] = ""
            self.hardware_config_data_label["text"] = ""
            self.dds_tx_paths_label["text"] = ""
            self.dds_tx_attenuation_label["text"] = ""
            self.transceiver_tx_paths_label["text"] = ""
            self.rx_paths_label["text"] = ""
            self.observation_rx_paths_label["text"] = ""
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
        if self.sg is not None:
            self.sg.set_output_enable(False)
        if self.psu is not None:
            self.psu.set_enabled(False)
        if os.path.exists(self.OCPI_IQ_CAPTURE_NB_IN_PATH[:-5]+"py"):
            os.remove(self.OCPI_IQ_CAPTURE_NB_IN_PATH[:-5]+"py")
        if os.path.exists(self.OCPI_IQ_CAPTURE_NB_OUT_PATH):
            os.remove(self.OCPI_IQ_CAPTURE_NB_OUT_PATH)
        if os.path.exists(self.OCPI_IQ_CAPTURE_DATA_OUT_PATH):
            os.remove(self.OCPI_IQ_CAPTURE_DATA_OUT_PATH)
        if os.path.exists(self.OCPI_IQ_CAPTURE_PLOT_OUT_PATH):
            os.remove(self.OCPI_IQ_CAPTURE_PLOT_OUT_PATH)

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
                                     .format(self.now.day, self.now.month, self.now.year, self.now.hour, self.now.minute, self.now.second))
        
        # Validate user entries
        uut_revision_pattern = re.compile("[A-Z][.][0-9]+$")
        uut_revision = self.uut_revision_entry.get().capitalize()
        if not uut_revision_pattern.match(uut_revision):
            self.test_report_insert_text("Invalid UUT Revision entry (format is X.n)\n")
            self.request_abort_test()
            return False
        
        # Check serial number field isn't empty or more than 15 characters long
        if self.uut_serial_number_entry.get() == "" or len(self.uut_serial_number_entry.get()) > 15:
            self.test_report_insert_text("Invalid UUT Serial Number entry\n")
            self.request_abort_test()
            return False
        else:
            uut_serial_number = self.uut_serial_number.get().upper()

        self.test_report_insert_text("UUT Part Number: {}\nUUT Revision: {}\nUUT Serial Number: {}\n\n"
                                     .format(self.uut_part_number_combobox.get(), uut_revision, uut_serial_number))
        
        # Change the Production Test button to an Abort Test button
        self.production_test_button["text"] = ">> ABORT TEST <<"
        self.production_test_button["command"] = self.request_abort_test
        self.production_test_label["text"] = "Test in progress..."

        # Test limits object
        if not self.ENGINEERING_MODE:
            self.test_limits = TestLimitsProduction()
        else:
            self.test_limits = TestLimitsEngineering()

        return True

    def initialise_test_equipment(self, signal_generator_required, spectrum_analyser_required, transceiver_initialise_required):
        # Connect to the test equipment
        self.test_report_insert_text("Connecting to DC Power Supply... ")
        if not self.DEBUG_MODE:
            if self.find_dc_power_supply(False):
                self.test_report_insert_text("OK ({})\n".format(self.psu.details()))
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False
        else:
            self.test_report_insert_text("OK (Debug)\n")
        
        if signal_generator_required:
            self.test_report_insert_text("Connecting to RF Signal Generator... ")
            if self.find_rf_signal_generator(False):
                self.test_report_insert_text("OK ({})\n".format(self.sg.details()))
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False
            
        if spectrum_analyser_required:
            self.test_report_insert_text("Connecting to RF Spectrum Analyser... ")
            if self.find_rf_spectrum_analyser(False):
                self.test_report_insert_text("OK ({})\n".format(self.sa.details()))
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False
        
        # Validate the calibration files
        s2p = S2PFileReader()
        if signal_generator_required:
            self.test_report_insert_text("Validating calibration file: {}... ".format(self.uut_to_signal_generator_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
            if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3, self.uut_to_signal_generator_s2p_file) is not None\
                and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3, self.uut_to_signal_generator_s2p_file) is not None:
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False

        if spectrum_analyser_required:
            self.test_report_insert_text("Validating calibration file: {}... ".format(self.uut_to_spectrum_analyser_s2p_file.removeprefix(self.CALIBRATION_REL_DIR)))
            if s2p.get_s_parameter(self.MIN_TEST_FREQ_HZ, 3, self.uut_to_spectrum_analyser_s2p_file) is not None\
                and s2p.get_s_parameter(self.MAX_TEST_FREQ_HZ, 3, self.uut_to_spectrum_analyser_s2p_file) is not None:
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
        ok = False
        self.test_report_insert_text("Setting PSU to {} V, {} A and enabling the output... ".format(self.PSU_VOLTAGE_V, self.PSU_CURRENT_A))
        if not self.DEBUG_MODE:
            ok = self.psu.set_voltage(self.PSU_VOLTAGE_V)
            ok &= self.psu.set_current(self.PSU_CURRENT_A)
            ok &= self.psu.set_ovp(self.PSU_VOLTAGE_V * 1.1)
            ok &= self.psu.set_ocp(self.PSU_CURRENT_A * 1.1)
            ok &= self.psu.set_sense_local()
            # Small delay here to ensure EMA is fully power cycled, if it was on before
            sleep(1)
            ok &= self.psu.set_enabled(True)
            if ok:
                self.test_report_insert_text("OK\n")
            else:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False
        else:
            ok = True
            self.test_report_insert_text("OK (Debug)\n")

        # Wait for EMA to boot then open an SSH session with it        
        self.ema_ssh = SSH(self.EMA_HOSTNAME)
        # Is the EMA already booted i.e. running in debug mode?
        if self.ema_ssh.is_connected():
            self.test_report_insert_text("Connecting to {}... OK\n".format(self.EMA_HOSTNAME))
            ok = True
        # No, so wait
        else:
            # Don't do anything yet other than append dots to show alive
            for s in range(self.EMA_BOOT_DELAY_S):                
                self.test_report_text.delete("end-1c linestart", END)
                self.test_report_insert_text("\n")
                self.test_report_insert_text("Waiting for EMA to boot... {}".format(self.EMA_BOOT_DELAY_S - s))
                sleep(1)
                # Opportunity to abort here
                if self.abort_requested:
                    self.test_report_insert_text("\n")
                    self.test_running = False
                    return False        
            self.test_report_text.delete("end-1c linestart", END)
            self.test_report_insert_text("\n")
            self.test_report_insert_text("Waiting for EMA to boot... OK\n")
            self.test_report_insert_text("Connecting to {}... ".format(self.EMA_HOSTNAME))
            ok = False
            for attempt in range(5): # Then attempt to connect every 3 seconds, for max. 15 seconds
                self.ema_ssh = SSH(self.EMA_HOSTNAME)
                if self.ema_ssh.is_connected():
                    self.test_report_insert_text("OK\n")
                    ok = True
                    break
                sleep(3)

        if not ok:
            self.test_report_insert_text("Error\n")
            self.request_abort_test()
            return False
        
        # Initialise the EMA ready for testing
        self.test_report_insert_text("Initialising {}... ".format(self.EMA_HOSTNAME))
        if "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_INITIALISE_CMD)).strip():
            self.test_report_insert_text("OK\n")
        else:
            # Catch the annoying socket exception error and reconnect
            for attempt in range(5):
                self.ema_ssh = SSH(self.EMA_HOSTNAME)
                if self.ema_ssh.is_connected():
                    break
                sleep(3)
            if "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_INITIALISE_CMD)).strip():
                self.test_report_insert_text("OK\n")
            else:                
                self.test_report_insert_text("Error\n\n")
                self.request_abort_test()
                return False

        if transceiver_initialise_required and not self.DEBUG_MODE:
            # Launch transceiver tool
            self.test_report_insert_text("Launching transceiver tool... OK\n")
            self.ema_ssh.send_command(self.EMA_XCVRTOOL_CMD)
            sleep(1)

            # Initialise transceiver
            self.ema_ssh.send_command(self.EMA_INITIALISE_XCVR_CMD)
            # Append dots to show alive while waiting
            for s in range(self.XCVR_INIT_DELAY_S):                
                self.test_report_text.delete("end-1c linestart", END)
                self.test_report_insert_text("\n")
                self.test_report_insert_text("Waiting for transceiver to initialise... {}".format(self.XCVR_INIT_DELAY_S - s))
                sleep(1)
                # Opportunity to abort here
                if self.abort_requested:
                    self.test_report_insert_text("\n")
                    self.test_running = False
                    return False        
            self.test_report_text.delete("end-1c linestart", END)
            self.test_report_insert_text("\n")
            self.test_report_insert_text("Initialising transceiver... OK\n")

            # Drop SSH connection and reconnect to ensure that the connection is alive after transceiver intialisation
            self.test_report_insert_text("Re-connecting to {}... ".format(self.EMA_HOSTNAME))
            del self.ema_ssh
            ok = False
            for attempt in range(5):  # Then attempt to connect every 3 seconds, for max. 15 seconds
                self.ema_ssh = SSH(self.EMA_HOSTNAME)
                if self.ema_ssh.is_connected():
                    self.test_report_insert_text("OK\n")
                    ok = True
                    break
                sleep(3)
            if not ok:
                self.test_report_insert_text("Error\n")
                self.request_abort_test()
                return False

        self.test_report_insert_text("\n")
        return True

    def production_test_routine(self):
        # Run the the test in a new thread for non-blocking
        Thread(target=self.run_production_test).start()

    def built_in_test_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_built_in_test).start()

    def hardware_config_data_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_hardware_config_data).start()

    def dds_tx_paths_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_dds_tx_paths).start()

    def dds_tx_attenuation_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_dds_tx_attenuation).start()

    def xcvr_tx_paths_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_xcvr_tx_paths).start()

    def rx_paths_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_rx_paths).start()

    def obs_rx_paths_routine(self):
        # Run the the test module in a new thread for non-blocking
        Thread(target=self.run_obs_rx_paths).start()

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
        self.show_hardware_setup(self.setup_type[3])
    
        # Initialise the test equipment
        ok = self.initialise_test_equipment(True, True, True)
        if not ok or self.abort_requested:
            self.test_running = False
            return False
            
        # Run each test module in turn
        if self.test_running:
            ok = self.run_built_in_test(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_hardware_config_data(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_dds_tx_paths(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_dds_tx_attenuation(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_xcvr_tx_paths(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            ok &= self.run_rx_paths(False)
            self.test_report_insert_text("\n")
        if self.test_running:
            # Display the required set-up change
            # Uncomment next line when test is implemented!
            #self.show_hardware_setup(self.setup_type[4])
            ok &= self.run_obs_rx_paths(False)
        
        # End the test:
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}.txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                        f.write(self.test_report_text.get('1.0', END))        
            
            self.lock_ui(False)
            if not self.DEBUG_MODE:
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
                self.show_hardware_setup(self.setup_type[5])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, False, True)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.built_in_test_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False
        
        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")                

        # 1.1: Initial PSU Current (in mA)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1) 
        if not self.DEBUG_MODE:
            result = int((self.psu.get_current_out() * 1000) + 0.5)
        else:
            result = 925
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.2 Daughter ID (expected response before shifting and masking is 0xE0000000)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = int(self.ema_ssh.send_command(self.EMA_TEST_GET_REG_DGTR_CTRL_CMD).strip(), 0) >> 28 & 0x03
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1
        
        # Select paths DDS0, RX0 and Rx Bypass
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_PATH_CMD.format(0))).strip()
        ok &= "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_RX_PATH_CMD.format(0))).strip()
        ok &= "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_RX_LNA_BYPASS_CMD)).strip()
        self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_DISABLE_CMD)
        if not ok:
            self.test_report_insert_text("EMA command failure (select paths)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Read LTC2991_0 channels
        ltc2991_0_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_0_CH_VOLTS_CMD)).strip().split()

        # 1.3 +1V3 Rail
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[4])))
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.4 +1V8 Rail
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[8])))
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.5 +3V3 Rail
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[36])))
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.6 +5V0 Rail
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[12]) * 3.7))
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.7 -2V5 Rail
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[16]) * 3.7 - 8.91))
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.8 -3V3 Rail
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[20]) * 3.7 - 8.91))
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1
        
        # 1.9 LNA 1 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[24]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.10 LNA 2 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[28]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # Read LTC2991_1 channels
        ltc2991_1_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_1_CH_VOLTS_CMD)).strip().split()

        # 1.11 GB 2 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[4]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.12 GB 3 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[8]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.13 GB 4 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[12]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.14 GB 5 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[16]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.15 GB 6 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[20]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.16 GB 7 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[24]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.17 GB 8 VDD (off)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[28]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # Opportunity to abort here
        if self.abort_requested:
            self.test_running = False
            return False
        
        # Select paths DDS4, RX7, Rx LNA and XCVR Tx enabled 
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_PATH_CMD.format(4))).strip()
        ok &= "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_RX_LNA_ENABLE_CMD)).strip()
        ok &= "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_RX_PATH_CMD.format(7))).strip()
        self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_ENABLE_CMD)
        if not ok:
            self.test_report_insert_text("EMA command failure (select paths)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # Read LTC2991_0 channels
        ltc2991_0_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_0_CH_VOLTS_CMD)).strip().split()

        # 1.18 LNA 1 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[24]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.19 LNA 2 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_0_channels[28]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1
       
        # Read LTC2991_1 channels
        ltc2991_1_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_1_CH_VOLTS_CMD)).strip().split()

        # 1.20 GB 2 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[4]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.21 GB 3 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[8]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.22 GB 7 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[24]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # Opportunity to abort here
        if self.abort_requested:
            self.test_running = False
            return False
        
        # Select path XCVR4
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_PATH_CMD.format(4))).strip()
        if not ok:
            self.test_report_insert_text("EMA command failure (select XCVR path)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)
        
        # Read LTC2991_1 channels
        ltc2991_1_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_1_CH_VOLTS_CMD)).strip().split()

        # 1.23 GB 8 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[28]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # Opportunity to abort here
        if self.abort_requested:
            self.test_running = False
            return False
        
        # Select path DDS5
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_PATH_CMD.format(5))).strip()
        if not ok:
            self.test_report_insert_text("EMA command failure (select DDS path)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)
        
        # Read LTC2991_1 channels
        ltc2991_1_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_1_CH_VOLTS_CMD)).strip().split()

        # 1.24 GB 4 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[12]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 1.25 GB 5 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[16]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # Opportunity to abort here
        if self.abort_requested:
            self.test_running = False
            return False

        # Select path DDS7
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_PATH_CMD.format(7))).strip()
        if not ok:
            self.test_report_insert_text("EMA command failure (select DDS path)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)
        
        # Read LTC2991_1 channels
        ltc2991_1_channels = str(self.ema_ssh.send_command(self.EMA_TEST_GET_LTC2991_1_CH_VOLTS_CMD)).strip().split()

        # 1.26 GB 6 VDD (on)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        result = float("{:.2f}".format(float(ltc2991_1_channels[20]) * 3.7))
        # Correct a false "0.08 V" LTC2991 reading...
        if result == 0.30:
            result = 0.00
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"    
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # End the test
        if standalone:
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
            
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)
    
    def run_hardware_config_data(self, standalone=True):
        # Start test running
        self.test_running = True
        self.hardware_config_data_label["text"] = "Test in progress..."
        
        fail_count = 0
        section = 2
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.hardware_config_data_label["text"] = "Test in progress..."
        
            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.hardware_config_data_button["text"]))
        
            if ok:
                # Display the required set-up image
                self.show_hardware_setup(self.setup_type[5])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, False, False)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.hardware_config_data_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False
        
        # Section header        
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")                

        # 2.1: Set HW Config Data (using the UUT Details)
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        serial_no = self.uut_serial_number.get().upper()
        rev_no = self.uut_revision_entry.get().capitalize()
        batch_no = "{:02d}/{:02d}/{:04d}".format(self.now.day, self.now.month, self.now.year)
        if self.uut_part_number_combobox.get() == "KT-000-0202-00":
            assembly_type = "NTM_RF_MB_EHB_8GHZ"
        elif self.uut_part_number_combobox.get() == "KT-000-0202-01":
            assembly_type = "NTM_RF_MB_EHB_6GHZ"
        if "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_CONFIG_DATA_CMD.format(serial_no, rev_no, batch_no, assembly_type))).strip():
            result = "Pass"
        else:
            result = "Fail"
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # Get HW Config Data
        resp = str(self.ema_ssh.send_command(self.EMA_TEST_GET_CONFIG_DATA_CMD.format(assembly_type))).strip()
        
        # Remove some troublesome characters then tokenise the response
        resp = re.sub('[\':\{\},]', '', resp).split()

        # Search for the bits we want
        for i, tkn in enumerate(resp):
            if tkn == "Serial":
                serial_no = resp[i+2]
            if tkn == "Revision":
                rev_no = resp[i+2]
            if tkn == "Date/Batch":
                batch_no = resp[i+2]
            if tkn == "Part":
                part_no = resp[i+2]
            if tkn == "calculated":
                checksum = resp[i+2]

        # 2.2: Verify Serial Number
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        lower_limit = upper_limit = self.uut_serial_number.get().upper()
        result = serial_no           
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1
        
        # 2.3: Verify Revision Number
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        lower_limit = upper_limit = self.uut_revision_entry.get().capitalize()
        result = rev_no
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 2.4: Verify Batch Number
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        lower_limit = upper_limit = "{:02d}/{:02d}/{:04d}".format(self.now.day, self.now.month, self.now.year)
        result = batch_no
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # 2.5: Verify Part Number
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        lower_limit = upper_limit = self.uut_part_number_combobox.get()
        result = part_no
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1
        
        # 2.6: Verify CRC Valid
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        if checksum == "VALID":
            result = "Pass"
        else:
            result = "Fail"
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{}\t\t{}\t\t{}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # End the test
        if standalone:
            self.test_running = False

        # Update the test status
        self.hardware_config_data_label["text"] = "Test complete (failures: {})".format(fail_count)
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
           
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_dds_tx_paths(self, standalone=True):
        # Start test running
        self.test_running = True
        self.dds_tx_paths_label["text"] = "Test in progress..."
        
        fail_count = 0
        section = 3
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.dds_tx_paths_label["text"] = "Test in progress..."
        
            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.dds_tx_paths_button["text"]))
        
            if ok:
                # Display the required set-up image
                self.show_hardware_setup(self.setup_type[0])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, True, False)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.dds_tx_paths_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False       
        
        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")                    
        
        # Apply common Spectrum Analyser settings
        ok = self.sa.set_span_Hz(int(1e6))
        ok &= self.sa.set_reference_level_dBm(20.0)
        ok &= self.sa.set_continuous_sweep(False)
        if not ok:
            self.test_report_insert_text("TE command failure (Spectrum Analyser)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        
        s2p = S2PFileReader()
        dds_path_curr = -1
        
        # 3.x: Loop around measuring fundamental and spurious levels using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
                
                # The description field contains the DDS path #, the test frequency, the multiplication factor
                # and whether the test frequency is the fundamental or a spurious term
                descr_chunks = str(description).strip().split(", ")                
                dds_path = int(re.sub('DDS', '', descr_chunks[0].strip()))                
                
                # DDS7 path is not supported by the -01 board variant so end test here
                if dds_path == 7 and self.uut_part_number_combobox.get() == "KT-000-0202-01":
                    break
                
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
                multiplier = int(re.sub("\D", '', descr_chunks[2].strip()))

                # Set the DDS path (using detection of the fundamental term in TEST_LIMITS as indication of a new path)
                if is_fundamental and not dds_path_curr == dds_path:
                    dds_path_curr = dds_path
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_PATH_CMD.format(dds_path))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (select DDS path)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)

                # Apply the Tx attenuation (if this is the fundamental)
                if is_fundamental:
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_ATTENUATION_CMD.format(False, self.test_limits.tx_att_dB(section-1, sub_section-1)))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set attenuation)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)
            
                # Update Spectrum Analyser centre frequency
                ok = self.sa.set_centre_frequency_Hz(test_freq_Hz)
                if not ok:
                    self.test_report_insert_text("TE command failure (Spectrum Analyser)\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                
                # Apply the DDS test tone to UUT (using detection of the fundamental term in TEST_LIMITS as indication of a new tone)
                if is_fundamental:
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_DDS_TONE_CMD.format(int(test_freq_Hz / multiplier)))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set DDS test tone)\n\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    sleep(1)

                # Measure the peak tone power and apply correction
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + (s2p.get_s_parameter(test_freq_Hz, 3, self.uut_to_spectrum_analyser_s2p_file, True) * -1)))

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
                self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
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
        self.ema_ssh.send_command(self.EMA_TEST_RESET_DDS_CMD)        
        if standalone:
            self.test_running = False
        
        # Update the test status
        self.dds_tx_paths_label["text"] = "Test complete (failures: {})".format(fail_count)
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
           
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)
    
    def run_dds_tx_attenuation(self, standalone=True):
        # Start test running
        self.test_running = True
        self.dds_tx_attenuation_label["text"] = "Test in progress..."
        
        fail_count = 0
        section = 4
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.dds_tx_attenuation_label["text"] = "Test in progress..."
        
            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.dds_tx_attenuation_button["text"]))
        
            if ok:
                # Display the required set-up image
                self.show_hardware_setup(self.setup_type[0])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, True, False)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.dds_tx_attenuation_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False       
        
        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")                    

        # Set all Tx attenuation to zero
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_ATTENUATION_CMD.format(False, 0.0))).strip()
        if not ok:
            self.test_report_insert_text("EMA command failure (set attenuation)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        
        # Select path DDS0
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_PATH_CMD.format(0))).strip()
        if not ok:
            self.test_report_insert_text("EMA command failure (select DDS path)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        # The test frequency
        test_freq_Hz = int(1e9)

        # Apply Spectrum Analyser settings
        ok = self.sa.set_centre_frequency_Hz(test_freq_Hz)
        ok &= self.sa.set_span_Hz(int(1e6))
        ok &= self.sa.set_reference_level_dBm(20.0)        
        ok &= self.sa.set_continuous_sweep(False)
        if not ok:
            self.test_report_insert_text("TE command failure (Spectrum Analyser)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        
        # Apply the DDS test tone to UUT
        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_DDS_TONE_CMD.format(test_freq_Hz))).strip()        
        if not ok:
            self.test_report_insert_text("EMA command failure (set DDS test tone)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        sleep(1)

        s2p = S2PFileReader()

        # 4.1: Reference Level
        ref_level = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + (s2p.get_s_parameter(test_freq_Hz, 3, self.uut_to_spectrum_analyser_s2p_file, True) * -1)))
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)        
        result = ref_level
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1
        
        # 4.x: Loop around measuring the attenuation step changes using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
                
                # The description field contains the attenution value
                try:
                    atten_dB = float(re.sub('dB State', '', description).strip())
                except:
                    self.test_report_insert_text("Invalid test parameter\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                
                # Apply the Tx attenuation
                ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_TX_ATTENUATION_CMD.format(False, atten_dB))).strip()
                if not ok:
                    self.test_report_insert_text("EMA command failure (set attenuation)\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False
                sleep(1)

                # Measure the peak tone power and apply correction
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + (s2p.get_s_parameter(test_freq_Hz, 3, self.uut_to_spectrum_analyser_s2p_file, True) * -1)))
                result = ref_level - peak                
                if result >= lower_limit and result <= upper_limit:        
                    status = "Pass"
                else:
                    status = "Fail"
                    fail_count += 1
                    self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                    self.overall_status_label["background"] = "red"
                self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
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
        self.ema_ssh.send_command(self.EMA_TEST_RESET_DDS_CMD)
        if standalone:
            self.test_running = False

        # Update the test status
        self.dds_tx_attenuation_label["text"] = "Test complete (failures: {})".format(fail_count)
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
           
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_xcvr_tx_paths(self, standalone=True):
        # Start test running
        self.test_running = True
        self.transceiver_tx_paths_label["text"] = "Test in progress..."
        
        fail_count = 0
        section = 5
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.transceiver_tx_paths_label["text"] = "Test in progress..."
        
            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.transceiver_tx_paths_button["text"]))
        
            if ok:
                # Display the required set-up image
                self.show_hardware_setup(self.setup_type[0])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(False, True, True)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.transceiver_tx_paths_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False

        # Set XCVR Tx enabled
        self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_ENABLE_CMD)
        
        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")                    
        
        # Get next row in TEST_LIMITS
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        
        # Apply common Spectrum Analyser settings
        ok = self.sa.set_span_Hz(int(50e6))
        ok &= self.sa.set_reference_level_dBm(20.0)
        if not ok:
            self.test_report_insert_text("TE command failure (Spectrum Analyser)\n")
            self.test_running = False
            self.request_abort_test()
            return False
        
        s2p = S2PFileReader()

        # 5.x: Loop around measuring fundamental and harmonic levels using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
                
                # The description field contains the XCVR path #, the test frequency and the harmonic order
                descr_chunks = str(description).strip().split(", ")
                xcvr_path = int(re.sub('XCVR', '', descr_chunks[0].strip()))
                
                # XCVR4 path is not supported by the -01 board variant so end test here
                if xcvr_path == 4 and self.uut_part_number_combobox.get() == "KT-000-0202-01":
                    break
                
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
            
                # Update Spectrum Analyser centre frequency
                ok = self.sa.set_centre_frequency_Hz(test_freq_Hz)
                if not ok:
                    self.test_report_insert_text("TE command failure (Spectrum Analyser)\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                # Configure the transceiver/test tone generator
                if is_fundamental:
                    initial_run = True if sub_section == 1 else False
                    test_freq_MHz = test_freq_Hz / 1e6
                    xcvr_tx_att_milli_dB = int(self.test_limits.tx_att_dB(section-1, sub_section-1) * 1000)
                    
                    # Determine transceiver/synth frequencies
                    xcvr_freq_MHz = test_freq_MHz
                    synth_freq_MHz = 11000.0
                    synth_path = 0
                    if xcvr_path == 4:
                        xcvr_freq_MHz = 5000.0  # 5 GHz IF
                        synth_freq_MHz = test_freq_MHz + xcvr_freq_MHz
                        synth_path = 1
                    
                    if initial_run:
                        self.ema_ssh.send_command(self.EMA_TEST_SET_TEST_TONE_CMD)
                        self.ema_ssh.send_command(self.EMA_TEST_SET_TEST_TONE_AMP_CMD)
                        ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_MODE_CMD)).strip()
                        if not ok:
                            self.test_report_insert_text("EMA command failure (set XCVR Tx mode)\n")
                            self.test_running = False
                            self.request_abort_test()
                            return False
                    
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_PATH_CMD.format(xcvr_path))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set XCVR Tx path)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_TX_ATT_CMD.format(xcvr_tx_att_milli_dB))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set XCVR attenuation)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_FREQ_CMD.format(xcvr_freq_MHz))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set XCVR frequency)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_SYNTH_CMD.format(synth_freq_MHz))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set XCVR synth frequency)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False
                    
                    ok = "OK" in str(self.ema_ssh.send_command(self.EMA_TEST_SET_SYNTH_PATH_CMD.format(synth_path))).strip()
                    if not ok:
                        self.test_report_insert_text("EMA command failure (set synth path)\n")
                        self.test_running = False
                        self.request_abort_test()
                        return False

                # Measure the peak tone power and apply correction (need to MAX HOLD the trace)
                self.sa.set_max_hold_mode(True)
                sleep(1)
                peak = float("{:.2f}".format(self.sa.get_peak_amplitude_dBm() + (s2p.get_s_parameter(test_freq_Hz, 3, self.uut_to_spectrum_analyser_s2p_file, True) * -1)))
                self.sa.set_max_hold_mode(False)

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
                self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
                sub_section += 1

                # Opportunity to abort here
                if self.abort_requested:
                    self.test_running = False
                    return False
                
            except IndexError:
                # We've reached the end
                break

        # End the test
        self.ema_ssh.send_command(self.EMA_TEST_SET_XCVR_RESET_CMD)
        ok &= self.sa.set_max_hold_mode(False)
        if standalone:
            self.test_running = False

        # Update the test status
        self.transceiver_tx_paths_label["text"] = "Test complete (failures: {})".format(fail_count)
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
           
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def run_rx_paths(self, standalone=True):
        # Start test running
        self.test_running = True
        self.rx_paths_label["text"] = "Test in progress..."
        
        fail_count = 0
        section = 6
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
                self.show_hardware_setup(self.setup_type[1])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(True, False, False)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.rx_paths_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False
        
        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")

        # Apply common Signal Generator settings
        ok = self.sg.set_output_power_dBm(-80.00)
        ok &= self.sg.set_output_enable(True)
        if not ok:
            self.test_report_insert_text("TE command failure (Signal Generator)\n")
            self.test_running = False
            self.request_abort_test()
            return False  
       
        s2p = S2PFileReader()
        sub_section_max = self.test_limits.section_size(section-1)

        # Ensure the plots folder exists
        if not os.path.exists(self.PLOTS_REL_DIR):
            os.makedirs(self.PLOTS_REL_DIR)

        # Create a popup window that will show the FFT plots as they come
        self.popup = Toplevel(self)

        # Set the fixed window size
        window_width = 538
        window_height = 432
        self.popup.minsize(window_width, window_height)
        self.popup.maxsize(window_width, window_height)

        # Get the main window position
        main_win_x = self.winfo_rootx()
        main_win_y = self.winfo_rooty()

        # Add offset
        main_win_x += 281
        main_win_y += 40

        # Set the position of the popup window to the centre of the main window
        self.popup.geometry(f'+{main_win_x}+{main_win_y}')
        self.popup.wm_transient(self)
        #self.popup.grab_set()
        self.popup.title("Transceiver Control: Receive Spectrum")
        self.popup.iconbitmap("./images/kirintec_logo.ico")
        self.popup.option_add("*font", "Arial 9")
        self.popup.protocol("WM_DELETE_WINDOW", self.disable_event) # Disables the window's Close button
        
        # 6.x: Loop around measuring the received Rx test tone using the TEST_LIMITS tuple to control execution
        while True:
            try:
                # Get next row in TEST_LIMITS
                description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
                
                # The description field contains the Rx path #, the test frequency and amplitude, and LNA or Bypass
                descr_chunks = str(description).strip().split(", ")
                rx_path = int(re.sub('RX', '', descr_chunks[0].strip()))
                
                # RX7 path is not supported by the -01 board variant so end test here
                if rx_path == 7 and self.uut_part_number_combobox.get() == "KT-000-0202-01":
                    break
                
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
                test_ampl_dBm = float(re.sub('dBm', '', descr_chunks[2].strip()))
                lna_enabled = True if "L" in descr_chunks[3] else False

                # Update Signal Generator output frequency and amplitude, correcting the amplitude
                test_ampl_dBm += (s2p.get_s_parameter(test_freq_Hz, 3, self.uut_to_signal_generator_s2p_file, True) * -1)
                ok = self.sg.set_frequency_Hz(test_freq_Hz)
                ok &= self.sg.set_output_power_dBm(test_ampl_dBm)
                if not ok:
                    self.test_report_insert_text("TE command failure (Signal Generator)\n")
                    self.test_running = False
                    self.request_abort_test()
                    return False

                # Update the popup window message
                msg_text = "Capturing Rx spectrum: {}/{} ({}), please wait".format(sub_section, sub_section_max, description)
                msg = Label(self.popup, text=msg_text)
                msg.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

                # Execute the OCPI IQ Capture notebook with parameters
                initial_run = True if sub_section == 1 else False
                offset = self.test_limits.fft_offset(section-1, sub_section-1)
                test_freq_MHz = test_freq_Hz / 1e6
                show_nb_plots = False
                ema_hostname = self.EMA_HOSTNAME if self.PYTHON_ENV else "\"{}\"".format(self.EMA_HOSTNAME)
                parameters = dict(EMA_HOST=ema_hostname,
                               CENTRE_FREQ_MHZ=test_freq_MHz,
                               LNA_EN=lna_enabled,
                               OFFSET_DB=offset,
                               PREINITIALISE=initial_run,
                               SHOW_PLOTS=show_nb_plots)
                
                 # Run the notebook file in a new thread for non-blocking
                worker_thread = Thread(target=lambda: self.execute_notebook_file(self.OCPI_IQ_CAPTURE_NB_IN_PATH, self.OCPI_IQ_CAPTURE_NB_OUT_PATH, parameters))
                worker_thread.start()
                
                # Add dots to the message while we wait
                count = 0
                while worker_thread.is_alive():
                    if count == 25:
                            msg_text  = msg_text[:-count]
                            count = 0
                    sleep(1)
                    msg_text += "."
                    msg = Label(self.popup, text=msg_text)
                    msg.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
                    count +=1

                    # Opportunity to abort here (e.g. notebook failed to execute)
                    if self.abort_requested:
                        worker_thread.join()    # Need to wait for other thread to complete
                        self.test_running = False
                        return False
                
                # Move the plot to the plots folder (will overwrite an existing one, so only keeping a copy of last unit tested)
                fft_plot_filename = self.PLOTS_REL_DIR + "{}.png".format(description)
                os.replace(self.OCPI_IQ_CAPTURE_PLOT_OUT_PATH, fft_plot_filename)

                # Update the popup window plot
                img = ImageTk.PhotoImage(Image.open(fft_plot_filename).resize((528,396)))
                plot = Label(self.popup, image=img)
                plot.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)

                # Get the peak tone information, find the applicable line in the output file (treating it as a regular text file, in case it is!)
                with open(self.OCPI_IQ_CAPTURE_NB_OUT_PATH,'r') as f:
                    contents = f.readlines()
                    # Get the index of the first line containing "Marker:", which is where the information is
                    count = 0
                    for line in contents:
                        if "Marker:" in line:
                            line_chunks = line.strip().split(", ")
                            marker_freq_MHz = float(re.sub('[a-zA-Z:"\\\\]', '', line_chunks[0].strip()))
                            marker_ampl_dBm = float(re.sub('[a-zA-Z:"\\\\]', '', line_chunks[1].strip()))
                            break
                        count += 1
                
                # Determine the test result
                result = marker_ampl_dBm
                if result >= lower_limit and result <= upper_limit:        
                    # The result is only valid if the peak tone frequency is within +/-1 MHz of the test frequency
                    if marker_freq_MHz >= (test_freq_MHz - 1) and marker_freq_MHz <= (test_freq_MHz + 1):
                        status = "Pass"
                    else:
                        status = "Fail"
                else:
                    status = "Fail"
                    fail_count += 1
                    self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
                    self.overall_status_label["background"] = "red"
                self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
                sub_section += 1

                # Opportunity to abort here
                if self.abort_requested:
                    self.test_running = False
                    return False
                
            except IndexError:
                # We've reached the end
                break

        """
        # Uncomment this block if the Obs Rx Path tests require an EMA reboot
        if not standalone:
            # Reboot needed to reload standard FPGA image
            self.ema_ssh.send_command(self.EMA_TEST_REBOOT_CMD) 
            # Don't do anything yet other than append dots to show alive
            count = 0
            for s in range(self.EMA_BOOT_DELAY_S):
                msg = Label(self.popup, text="Waiting for EMA to reboot... {}".format(self.EMA_BOOT_DELAY_S - s))
                msg.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
                sleep(1)
            msg = Label(self.popup, text="Connecting to {}... ".format(self.EMA_HOSTNAME))
            msg.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
            ok = False
            for attempt in range(5): # Then attempt to connect every 3 seconds, for max. 15 seconds
                self.ema_ssh = SSH(self.EMA_HOSTNAME)
                if self.ema_ssh.is_connected():
                    ok = True
                    break
                sleep(3)
            if not ok:
                self.test_report_insert_text("{} failed to reboot\n".format(self.EMA_HOSTNAME))
        """

        # Clean up the working directory
        if os.path.exists(self.OCPI_IQ_CAPTURE_NB_IN_PATH[:-5]+"py"):
            os.remove(self.OCPI_IQ_CAPTURE_NB_IN_PATH[:-5]+"py")
        if os.path.exists(self.OCPI_IQ_CAPTURE_NB_OUT_PATH):
            os.remove(self.OCPI_IQ_CAPTURE_NB_OUT_PATH)
        if os.path.exists(self.OCPI_IQ_CAPTURE_DATA_OUT_PATH):    
            os.remove(self.OCPI_IQ_CAPTURE_DATA_OUT_PATH)
        if os.path.exists(self.OCPI_IQ_CAPTURE_PLOT_OUT_PATH):   
            os.remove(self.OCPI_IQ_CAPTURE_PLOT_OUT_PATH)

        # End the test
        self.sg.set_output_enable(False)
        self.popup.destroy()
        if standalone:
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
           
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)
    
    def run_obs_rx_paths(self, standalone=True):
        # Start test running
        self.test_running = True
        self.observation_rx_paths_label["text"] = "Test in progress..."
        
        fail_count = 0
        section = 7
        sub_section = 1

        # Skip initial steps if the module is not being run as standalone
        ok = True
        if standalone:
            # Lock the UI down
            self.lock_ui(True)
            self.observation_rx_paths_label["text"] = "Test in progress..."
        
            # Initialise the test report
            ok = self.initialise_test_report("Section {}: {}".format(section, self.observation_rx_paths_button["text"]))
        
            if ok:
                # Display the required set-up image
                self.show_hardware_setup(self.setup_type[2])
        
                # Initialise the test equipment
                ok = self.initialise_test_equipment(True, False, False)
        else:
            self.test_report_insert_text("Section {}: {}\n".format(section, self.observation_rx_paths_button["text"]))
        
        # Opportunity to abort here
        if not ok or self.abort_requested:
            self.test_running = False
            return False
        
        # Section header
        self.test_report_insert_text("Test #\tDescription\t\t\tUnits\tResult\t\tLL\t\tUL\t\tPass/Fail\n")                    
        
        # Get next row in TEST_LIMITS
        description, units, lower_limit, upper_limit = self.test_limits.get(section-1, sub_section-1)
        
        # Determine the test result
        result = 0        
        if result >= lower_limit and result <= upper_limit:        
            status = "Pass"
        else:
            status = "Fail"
            fail_count += 1
            self.overall_status_label["text"] = "TEST IN PROGRESS (FAIL)"
            self.overall_status_label["background"] = "red"
        self.test_report_insert_text("{}.{}\t{}\t\t\t{}\t{:.2f}\t\t{:.2f}\t\t{:.2f}\t\t{}\n".format(section, sub_section, description, units, result, lower_limit, upper_limit, status))
        sub_section += 1

        # End the test
        if standalone:
            self.test_running = False

        # Update the test status          
        self.observation_rx_paths_label["text"] = "Test complete (failures: {})".format(fail_count)
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
            self.test_report_insert_text("\nTest Duration (hh:mm:ss): {}\n".format(timedelta(seconds=(datetime.now() - self.now).seconds)))
            test_report_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}-{}-{}_{}(P).txt".\
                format(self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second,\
                        self.uut_part_number_combobox.get(), self.uut_revision_entry.get().capitalize(),\
                        self.uut_serial_number.get().upper(), overall_status)
            with open(self.TEST_REPORT_REL_DIR + test_report_file_name, "w") as f:
                    f.write(self.test_report_text.get('1.0', END))
           
            self.lock_ui(False)
            if not self.DEBUG_MODE:
                self.psu.set_enabled(False)

        return bool(fail_count == 0)

    def execute_notebook_file(self, input_ipynb_path, output_ipynb_path, parameters_dict):
        if self.PYTHON_ENV:
            try:
                # Executing a parameterised notebook with papermill only works when running in a Python environment
                # Many failed attempts to get this to work!
                pm.execute_notebook(input_ipynb_path, output_ipynb_path, parameters_dict)
            except Exception as e:
                    print(e)
                    self.test_report_insert_text("Notebook execution failure (as *.ipynb)\n")
                    self.request_abort_test()
        else:
            try:
                # Execute the notebook converted to a Python script instead when running as EXE
                input_script_path = input_ipynb_path[:-5]+"py"
                self.convert_notebook(input_ipynb_path, input_script_path)                
                
                # Modify the default parameters by inserting the required values below them, as per papermill
                with open(input_script_path,'r') as f:
                    contents = f.readlines()
                    # Get the index of the line containing "# Step 2" and insert above this
                    count = 0
                    for line in contents:
                        if "# Step 2" in line:
                            count -= 1
                            contents.insert(count, "# Injected Parameters\n")
                            for key, value in parameters_dict.items():
                                count += 1
                                contents.insert(count, "{} = {}\n".format(key, value))                        
                            break
                        count += 1
                with open(input_script_path, "w") as f:
                    contents = "".join(contents)
                    f.write(contents)

                # Now run the script
                with open(output_ipynb_path,'w') as f:
                    subprocess.run(["python", input_script_path], timeout=60, stdout=f, stderr=f)
            except Exception as e:
                print(e)
                self.test_report_insert_text("Notebook execution failure (as *.py)\n")
                self.request_abort_test()

    def convert_notebook(self, notebookPath, modulePath):
        with open(notebookPath) as f:
            nb = nbformat.reads(f.read(), nbformat.NO_CONVERT)
        exporter = PythonExporter()
        source, meta = exporter.from_notebook_node(nb)
        with open(modulePath, 'w') as f:
            f.writelines(source)

    def test_report_insert_text(self, text=""):
        # Function ensures the vertical scroll bar moves with the text
        self.test_report_text.insert(END, text)
        self.test_report_text.see(END)

    def show_hardware_setup(self, setup=""):
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
        #self.popup.attributes('-topmost', True)
        self.popup.grab_set()
    
        # Display the set-up image and wait for button press
        self.popup.title("Set-Up: {}".format(setup))
        self.popup.iconbitmap("./images/kirintec_logo.ico")
        self.popup.option_add("*font", "Arial 9")
        self.popup.protocol("WM_DELETE_WINDOW", self.disable_event) # Disables the window's Close button
        if setup == self.setup_type[0]:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_TX_PATH))
        elif setup == self.setup_type[1]:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_RX_PATH))
        elif setup == self.setup_type[2]:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_OBS_PATH))
        elif setup == self.setup_type[3]:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_TX_RX_PATH))
        elif setup == self.setup_type[4]:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_TX_OBS_PATH))
        elif setup == self.setup_type[5]:
            img = ImageTk.PhotoImage(Image.open(self.SETUP_NO_RF_PATH))
        label = Label(self.popup, image=img)
        label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
        var = IntVar()        
        close_button = Button(self.popup, text=">> FOLLOW THE INSTRUCTIONS THEN CLICK HERE TO CONTINUE <<", command=lambda: var.set(1))
        close_button.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)        
        close_button.wait_variable(var)
        self.popup.destroy()

if __name__ == "__main__":
    main_window = NTMMBeHBRFBoardTest()
    main_window.mainloop()