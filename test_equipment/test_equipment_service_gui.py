#!/usr/bin/env python3
"""
Test Equipment Service GUI for:

- KT-0956-0267-00

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

# -----------------------------------------------------------------------------
# Tkinter imports
# -----------------------------------------------------------------------------
from tkinter import *
from tkinter.ttk import *
import tkinter as tk
from tkinter import messagebox

# -----------------------------------------------------------------------------
# Standard library imports
# -----------------------------------------------------------------------------
from threading import *
from time import sleep
from  datetime import datetime, timedelta
from enum import Enum
import re, os, sys
import io
import logging

# -----------------------------------------------------------------------------
# Third-party imports
# -----------------------------------------------------------------------------
from PIL import ImageTk, Image

# -----------------------------------------------------------------------------
# Local application imports
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Local Services imports
# -----------------------------------------------------------------------------
from signal_generator_service import *
from power_meter_service import *
from spectrum_analyser_service import *
from power_supply_service import *
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
    def __init__(self, text_ctrl=""):
        """ Class constructor """
        self.output = text_ctrl
        super().__init__()

    def write(self, string):
        self.output.insert(tk.END, string)
        self.output.see(tk.END)

    def flush(self):
        pass

class TestEquipServiceGui(Tk):
    # Determine if application is running in the normal Python environment or as a frozen exe
    if getattr(sys, 'frozen', False):        
        APP_PATH = os.path.dirname(sys.executable)
        PYTHON_ENV = False
        log.info("Running as EXE")
    else:
        APP_PATH = os.path.dirname(__file__)
        PYTHON_ENV = True
        log.info("Running in Python environment")

    # Constants
    SW_NO = "KT-0956-0267-00"
    UI_VERSION = "1.0.0"
    TEST_VERSION = "1.0.0"
    APP_NAME = "Test Equipment Service UI [v{}]".format(UI_VERSION)
    APP_LOGO_PATH = os.path.join(APP_PATH + os.sep + "kirintec_logo.ico")

    # Test objects
    psu = None
    psus = None
    sg = None
    sgs = None
    sa = None
    sas = None
    pm = None
    pms = None

    # Flags used for abort test feature
    abort_requested = False
    abort_pending = False
    test_running = False

    def __init__(self):
        """
        Class constructor, initialises the Tkinter GUI window and adds all the widgets to it.

        All of the text boxes on the GUI window have associated tk.StringVar variables which
        are used to get/set the displayed text.  Text boxes used solely for reporting purposes
        are set as read-only
        """
        super().__init__()      
        
        # Needed for windows to show correct icon on Taskbar
        try:
            from ctypes import windll            
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_NAME)
        except ImportError:
            pass

            # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

        # Set up the Tkinter window
        self.initialise_window()

        # # Set up sys.stdout/logging to re-direct to the Test Status ScrolledText widget
        redir = StdRedirect(self.test_report_text)
        sys.stdout = redir

        self._logging_level = \
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level, force=True)

        self._pm_service_created = False
        self._sg_service_created = False
        self._sa_service_created = False
        self._psu_service_created = False


    def run(self):
        """
        Tkinter GUI application main loop
        :return:
        """
        self.mainloop()

    def initialise_window(self):
        """
        Set up the Tkinter window title and overall geometry
        :return: N/A
        """
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Set title and icon
        self.title("{} - {}".format(self.SW_NO, self.APP_NAME))
        self.iconbitmap(self.APP_LOGO_PATH)
        self.option_add("*font", "Arial 9")

        # Set the fixed window size
        window_width = 1024
        window_height = 768

        # Get the screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.minsize(window_width, window_height)
        self.maxsize(screen_width, screen_height)

        # Find the screen centre point
        screen_center_x = int((screen_width / 2) - (window_width / 2))
        screen_center_y = int((screen_height / 2) - (window_height / 2))

        # Set the position of the window to the centre of the screen
        self.geometry(f'{window_width}x{window_height}+{screen_center_x}+{screen_center_y}')

        # Set the position of the window to the centre of the screen
        self.geometry(f'{window_width}x{window_height}')
        if os.path.isfile(self.APP_LOGO_PATH):
            self.iconbitmap(self.APP_LOGO_PATH)
        
        # Populate main window with the required widgets
        # Test Equipment frame and label
        self.test_equipment_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.test_equipment_frame.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)
        self.test_equipment_frame_label = Label(self.test_equipment_frame, text="Test Equipment", font="Arial 11 bold")
        self.test_equipment_frame_label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # Start all services button and label
        self.start_all_services_button = Button(self.test_equipment_frame, text="Start All Services", state=DISABLED, command=self.start_all_services)
        self.start_all_services_button.grid(column=3, row=0, padx=3, pady=3, sticky=NSEW)

        # Find Ip Adapters button and label
        self.find_ip_adapter_button = Button(self.test_equipment_frame, text="Find IP Adapters", command=self.find_ip_adapters)
        self.find_ip_adapter_button.grid(column=4, row=0, padx=3, pady=3, sticky=NSEW)

        # DC Power Supply label, combobox, button and label
        self.dc_power_supply_ip_adapter = StringVar()
        self.dc_power_supply_label0 = Label(self.test_equipment_frame, text="DC Power Supply:")
        self.dc_power_supply_label0.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_connected_label = Label(self.test_equipment_frame, text="None")
        self.dc_power_supply_connected_label.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_label1 = Label(self.test_equipment_frame, text= "------------")
        self.dc_power_supply_label1.grid(column=2, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_serv_button = Button(self.test_equipment_frame, text="Start PSU Service", state=DISABLED, command=self.start_dc_power_supply_service)
        self.dc_power_supply_serv_button.grid(column=3, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_ip_combobox = Combobox(self.test_equipment_frame, textvariable=self.dc_power_supply_ip_adapter)
        self.dc_power_supply_ip_combobox["values"] = ("---")
        self.dc_power_supply_ip_combobox.current(0)
        self.dc_power_supply_ip_combobox.grid(column=4, row=1, padx=3, pady=3, sticky=NSEW)
        self.dc_power_supply_serv_label = Label(self.test_equipment_frame, text="PSU Service Not Started", font="Arial 11 bold", foreground="white", background="gray32", anchor=CENTER, width=25)
        self.dc_power_supply_serv_label.grid(column=5, row=1, padx=3, pady=3, sticky=NSEW)       

        # RF Signal Generator combobox, button and label
        self.rf_signal_generator_ip_adapter = StringVar()
        self.rf_signal_generator_label0 = Label(self.test_equipment_frame, text="RF Signal Generator:")
        self.rf_signal_generator_label0.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_connected_label = Label(self.test_equipment_frame, text="None")
        self.rf_signal_generator_connected_label.grid(column=1, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_label1 = Label(self.test_equipment_frame, text="------------")
        self.rf_signal_generator_label1.grid(column=2, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_serv_button = Button(self.test_equipment_frame, text="Start SG Service", state=DISABLED, command=self.start_rf_signal_generator_service)
        self.rf_signal_generator_serv_button.grid(column=3, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_ip_combobox = Combobox(self.test_equipment_frame, textvariable=self.rf_signal_generator_ip_adapter)
        self.rf_signal_generator_ip_combobox["values"] = ("---")
        self.rf_signal_generator_ip_combobox.current(0)
        self.rf_signal_generator_ip_combobox.grid(column=4, row=2, padx=3, pady=3, sticky=NSEW)
        self.rf_signal_generator_serv_label = Label(self.test_equipment_frame, text="SG Service Not Started", font="Arial 11 bold", foreground="white", background="gray32", anchor=CENTER, width=25)
        self.rf_signal_generator_serv_label.grid(column=5, row=2, padx=3, pady=3, sticky=NSEW)

        # RF Spectrum Analyser combobox, button and label
        self.rf_spectrum_analyser_ip_adapter = StringVar()
        self.rf_spectrum_analyser_label0 = Label(self.test_equipment_frame, text="RF Spectrum Analyser:")
        self.rf_spectrum_analyser_label0.grid(column=0, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_connected_label = Label(self.test_equipment_frame, text="None")
        self.rf_spectrum_analyser_connected_label.grid(column=1, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_label1 = Label(self.test_equipment_frame, text="------------")
        self.rf_spectrum_analyser_label1.grid(column=2, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_serv_button = Button(self.test_equipment_frame, text="Start SA Service", state=DISABLED, command=self.start_rf_spectrum_analyser_service)
        self.rf_spectrum_analyser_serv_button.grid(column=3, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_ip_combobox = Combobox(self.test_equipment_frame, textvariable=self.rf_spectrum_analyser_ip_adapter)
        self.rf_spectrum_analyser_ip_combobox["values"] = ("---")
        self.rf_spectrum_analyser_ip_combobox.current(0)
        self.rf_spectrum_analyser_ip_combobox.grid(column=4, row=3, padx=3, pady=3, sticky=NSEW)
        self.rf_spectrum_analyser_serv_label = Label(self.test_equipment_frame, text="SA Service Not Started", font="Arial 11 bold", foreground="white", background="gray32", anchor=CENTER, width=25)
        self.rf_spectrum_analyser_serv_label.grid(column=5, row=3, padx=3, pady=3, sticky=NSEW)

        # NRP Power Meter combobox, button and label
        self.power_meter_ip_adapter = StringVar()
        self.power_meter_label0 = Label(self.test_equipment_frame, text="NRP Power Meter:")
        self.power_meter_label0.grid(column=0, row=4, padx=3, pady=3, sticky=NSEW)
        self.power_meter_connected_label = Label(self.test_equipment_frame, text="None")
        self.power_meter_connected_label.grid(column=1, row=4, padx=3, pady=3, sticky=NSEW)
        self.power_meter_check_label1 = Label(self.test_equipment_frame, text="------------")
        self.power_meter_check_label1.grid(column=2, row=4, padx=3, pady=3, sticky=NSEW)
        self.power_meter_serv_button = Button(self.test_equipment_frame, text="Start PM Service", state=DISABLED, command=self.start_power_meter_service)
        self.power_meter_serv_button.grid(column=3, row=4, padx=3, pady=3, sticky=NSEW)
        self.power_meter_ip_combobox = Combobox(self.test_equipment_frame, textvariable=self.power_meter_ip_adapter)
        self.power_meter_ip_combobox["values"] = ("---")
        self.power_meter_ip_combobox.current(0)
        self.power_meter_ip_combobox.grid(column=4, row=4, padx=3, pady=3, sticky=NSEW)
        self.power_meter_serv_label = Label(self.test_equipment_frame, text="PM Service Not Started", font="Arial 11 bold", foreground="white", background="gray32", anchor=CENTER, width=25)
        self.power_meter_serv_label.grid(column=5, row=4, padx=3, pady=3, sticky=NSEW)

        # Test Report frame and label
        self.test_report_frame = Frame(self, borderwidth=3, relief=RIDGE, padding=3)
        self.test_report_frame.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.test_report_frame_label = Label(self.test_report_frame, text="Test Report", font="Arial 11 bold")
        self.test_report_frame_label.grid(column=0, row=0, padx=3, pady=3, sticky=NSEW)

        # Test Report text box
        self.test_report_text = Text(self.test_report_frame, wrap=NONE, height=32, width=125)
        self.test_report_text.bind("<Key>", lambda e: self.ctrl_event(e)) # Makes the Text widget read-only while allowing CTRL+C event
        self.test_report_text_xs = Scrollbar(self.test_report_frame, orient=HORIZONTAL, command=self.test_report_text.xview)
        self.test_report_text_ys = Scrollbar(self.test_report_frame, orient=VERTICAL, command=self.test_report_text.yview)
        self.test_report_text['xscrollcommand'] = self.test_report_text_xs.set
        self.test_report_text['yscrollcommand'] = self.test_report_text_ys.set
        self.test_report_text.grid(column=0, row=1, padx=3, pady=3, sticky=NSEW)
        self.test_report_text_xs.grid(column=0, row=2, padx=3, pady=3, sticky=NSEW)
        self.test_report_text_ys.grid(column=1, row=1, padx=3, pady=3, sticky=NSEW)
    
    def ctrl_event(self, event):
        if (12 == event.state and event.keysym == 'c'):
            return None
        else:
            return "break" 
    
    # -----------------------------------------------------------------------------
    # IP Adapters functions
    # -----------------------------------------------------------------------------

    def find_ip_adapters(self):
        log.info("INFO - Searching for IP adapters...")
        self.find_psu_ip_adapters()
        self.find_sg_ip_adapters()
        self.find_sa_ip_adapters()
        self.find_pm_ip_adapters()

        self.start_all_services_button["state"] = NORMAL

    def find_psu_ip_adapters(self):
        """
        This method searches for IP adapters and populates the relevant GUI dropdown menu with the existing available options
        :param None
        :return None
        """
        # Populate PSU IP adapters list
        self.psus = PowerSupplyService()
        self.find_dc_power_supply()
        if self.psus.ips:

            # Present the IP adapters list in the dropdown menu so that the user can select the adapter to use.
            log.info("INFO - PSU Service IP Adapter's List: {}".format(self.psus.ips))
            self.dc_power_supply_ip_adapter = self.psus.ips
            self.sel_string =("Select PSUS IP Adapter",)

            for i in self.psus.ips:
                self.sel_string = self.sel_string + (i,)
            
            self.dc_power_supply_ip_combobox["values"] = self.sel_string
            self.dc_power_supply_ip_combobox.current(0)
        
        del self.psus
    
    def find_sg_ip_adapters(self):
        """
        This method searches for IP adapters and populates the relevant GUI dropdown menu with the existing available options
        :param None
        :return None
        """
        # Populate sg IP adapters list
        self.sgs = SignalGeneratorService()
        self.find_rf_signal_generator()
        if self.sgs.ips:

            # Present the IP adapters list in the dropdown menu so that the user can select the adapter to use.
            log.info("INFO - SG Service IP Adapter's List: {}".format(self.sgs.ips))
            self.rf_signal_generator_ip_adapter = self.sgs.ips
            self.sel_string =("Select SGS IP Adapter",)

            for i in self.sgs.ips:
                self.sel_string = self.sel_string + (i,)
            
            self.rf_signal_generator_ip_combobox["values"] = self.sel_string
            self.rf_signal_generator_ip_combobox.current(0)

        del self.sgs
    
    def find_sa_ip_adapters(self):
        """
        This method searches for IP adapters and populates the relevant GUI dropdown menu with the existing available options
        :param None
        :return None
        """
        # Populate sa IP adapters list
        self.sas = SpectrumAnalyserService()
        self.find_rf_spectrum_analyser()
        if self.sas.ips:

            # Present the IP adapters list in the dropdown menu so that the user can select the adapter to use.
            log.info("INFO - SA Service IP Adapter's List: {}".format(self.sas.ips))
            self.rf_spectrum_analyser_ip_adapter = self.sas.ips
            self.sel_string =("Select SAS IP Adapter",)

            for i in self.sas.ips:
                self.sel_string = self.sel_string + (i,)
            
            self.rf_spectrum_analyser_ip_combobox["values"] = self.sel_string
            self.rf_spectrum_analyser_ip_combobox.current(0)
        
        del self.sas

    def find_pm_ip_adapters(self):
        """
        This method searches for IP adapters and populates the relevant GUI dropdown menu with the existing available options
        :param None
        :return None
        """
        # Populate pm IP adapters list
        self.pms = PowerMeterService()
        self.find_power_meter()
        if self.pms.ips:

            # Present the IP adapters list in the dropdown menu so that the user can select the adapter to use.
            log.info("INFO - PM Service IP Adapter's List: {}".format(self.pms.ips))
            self.power_meter_ip_adapter = self.pms.ips
            self.psu_sel_string =("Select PMS IP Adapter",)

            for i in self.pms.ips:
                self.psu_sel_string = self.psu_sel_string + (i,)
            
            self.power_meter_ip_combobox["values"] = self.psu_sel_string
            self.power_meter_ip_combobox.current(0)
        
        del self.pms
        
    # -----------------------------------------------------------------------------
    # Power supply functions
    # -----------------------------------------------------------------------------
    
    def find_dc_power_supply(self, button_normal_on_complete=True):
        """
        This method searches for connected power supplies and populates the relevant GUI box with the first PSU which is connected and supported
        :param button_normal_on_complete: Type: Boolean
        :return None
        """
        log.info("INFO - Checking for connected power supplies...")
        self.dc_power_supply_label1["text"] = "........"
        self.dc_power_supply_label1["foreground"] = "orange"
        self.dc_power_supply_label1["background"] = "white"
        self.dc_power_supply_serv_button["state"] = DISABLED
        self.dc_power_supply_connected_label["text"] = "------------"

        # Attempt to find and initialise the DC Power Supply
        [is_device_initalized, model] = self.psus.psu.device_specific_initialisation()
        if is_device_initalized:
            self.dc_power_supply_connected_label["text"] = model
            self.dc_power_supply_label1["text"] = "PSU Found"
            self.dc_power_supply_label1["font"] = "Arial 9 bold"
            self.dc_power_supply_label1["foreground"] = "green"
            self.dc_power_supply_label1["background"] = "white"
            log.info("INFO - Found Power Supply: {}".format(model))
        else:
            self.dc_power_supply_label1["text"] = "Not found"
            self.dc_power_supply_label1["font"] = "Arial 9 bold"
            self.dc_power_supply_label1["foreground"] = "red"
            self.dc_power_supply_label1["background"] = "white"
            log.info("INFO - Did not find any connected power supplies!")
            self.psu = None
        
        if button_normal_on_complete:
            self.dc_power_supply_serv_button["state"] = NORMAL

        return bool(self.psu is not None)
    
    def start_dc_power_supply_service(self):
        """
        This method starts the PSU service
        :param None
        :return None
        """
        log.info("INFO - Starting Power Supply Service Thread...")
        self.dc_power_supply_serv_button["state"] = DISABLED
        self.dc_power_supply_serv_label["text"] = "Starting PSU Service..." 
        self.dc_power_supply_serv_label["font"] = "Arial 11 bold" 
        self.dc_power_supply_serv_label["background"] = "white"      
        self.dc_power_supply_serv_label["foreground"] = "orange"
        
        # Start a power supply service thread
        Thread(target=self.start_dc_power_supply_service_thread).start()
    
    def stop_dc_power_supply_service(self):
        """
        This method stops the PSU service
        :param None
        :return None
        """
        log.info("INFO - Stopping Power Supply Service Thread...")
        self.dc_power_supply_serv_label["text"] = "PSU Service Stopped..."   
        self.dc_power_supply_serv_label["font"] = "Arial 11 bold" 
        self.dc_power_supply_serv_label["background"] = "white"      
        self.dc_power_supply_serv_label["foreground"] = "red"
        self.dc_power_supply_serv_button["text"] = "Start PSU Service"
        self.dc_power_supply_serv_button["state"] = NORMAL
        self.dc_power_supply_ip_combobox["state"] = NORMAL
        self.dc_power_supply_serv_button.configure(command=self.start_dc_power_supply_service)
        
        # Stop the power supply service thread
        self.psus_thread.quit()
        self._psu_service_created = False
        self.psus.is_thread_running = False
        # Close the resource manager connection
        self.psus.psu.visa_te.psu.rm.close()

        # Check if any of the other services are running
        if not (self._sg_service_created or self._sa_service_created or self._pm_service_created):
            # Reconfigure button to be able to start all services
            self.start_all_services_button["state"] = NORMAL
            self.start_all_services_button["text"] = "Start All Services"
            self.start_all_services_button.configure(command=self.start_all_services)
            self.find_ip_adapter_button["state"] = NORMAL

    def start_dc_power_supply_service_thread(self):
        """
        This method starts the PSU service thread
        :param None
        :return None
        """
        self.psus = PowerSupplyService()
        [is_device_initalized, model] = self.psus.psu.device_specific_initialisation()
        # self._psu_service_created = True
        # Attempt to find and initialise the DC Power Supply
        # self.find_dc_power_supply()
        if is_device_initalized:
            self._psu_service_created = True
            if self.psus.ips:
                self.psus.ip = self.dc_power_supply_ip_combobox.get()

                # Check for a valid IP adapter selection
                if self.psus.ip == "Select PSUS IP Adapter":

                    self.instruction_dialog("INFO - PSU Service: Please select a valid IP adapter before proceeding!")
                    self.dc_power_supply_serv_button["state"] = NORMAL
                    self.dc_power_supply_serv_label["text"] = "PSU Service Not Started"        
                    self.dc_power_supply_serv_label["background"] = "gray32"
                    self.dc_power_supply_serv_label["font"] ="Arial 11 bold"
                    self.dc_power_supply_serv_label["foreground"] ="white"
                    self._psu_service_created = False
                else:
                    log.info("INFO - Selecting network interface with IP address {}".format(self.psus.ip))
                    log.info("INFO - Starting TCP/IP listener on port {}".format(self.psus.port))
                    self.psus_thread = PSUSAccept(self.psus.ip, self.psus.port, self.psus, self.psus.psu)
                    self.psus_thread.start()
                    log.info("INFO - Registering service for power supply {}".format(model))
                    self.psus.register_service()
                    if self.psus.psu.binding_success:
                        self._psu_service_created = True
                        self.psus.is_thread_running = True
                        log.info("INFO - Registering power supply service successfull")
                        log.info("INFO - Power supply service is running...")
                        self.dc_power_supply_serv_label["text"] = "PSU Service Running..."  
                        self.dc_power_supply_serv_label["font"] = "Arial 11 bold"       
                        self.dc_power_supply_serv_label["background"] = "white"  
                        self.dc_power_supply_serv_label["foreground"] = "green" 
                        self.dc_power_supply_serv_button["text"] = "Stop PSU Service"
                        self.dc_power_supply_serv_button["state"] = NORMAL
                        self.dc_power_supply_serv_button.configure(command=self.stop_dc_power_supply_service)
                        self.dc_power_supply_ip_combobox["state"] = DISABLED
                        self.find_ip_adapter_button["state"] = DISABLED
                        # Reconfigure start all services button to be able to stop all services
                        self.start_all_services_button["state"] = NORMAL
                        self.start_all_services_button["text"] = "Stop All Services"
                        self.start_all_services_button.configure(command=self.stop_all_services)
                    else:
                        log.info("ERROR - Failed to register power supply service!")
                        self.dc_power_supply_serv_button["state"] = NORMAL
                        self.dc_power_supply_serv_label["text"] = "PSU Service Not Started"        
                        self.dc_power_supply_serv_label["background"] = "gray32"
                        self.dc_power_supply_serv_label["font"] ="Arial 11 bold"
                        self.dc_power_supply_serv_label["foreground"] ="white"
                        self._psu_service_created = False
                        self.psus.is_thread_running = False
                        self.psus_thread.quit()
            else:
                self._psu_service_created = False
                log.info("ERROR - No candidate network interface found!")
                self.dc_power_supply_serv_button["state"] = NORMAL
                self.dc_power_supply_serv_label["text"] = "PSU Service Not Started"        
                self.dc_power_supply_serv_label["background"] = "gray32"
                self.dc_power_supply_serv_label["font"] ="Arial 11 bold"
                self.dc_power_supply_serv_label["foreground"] ="white"
        else:
            self._psu_service_created = False
            log.info("ERROR - Could not find power supply!")
            log.info("ERROR - Stopping Power Supply Service...")
            self.dc_power_supply_serv_button["state"] = NORMAL
            self.dc_power_supply_serv_label["text"] = "PSU Service Not Started"        
            self.dc_power_supply_serv_label["background"] = "gray32"
            self.dc_power_supply_serv_label["font"] ="Arial 11 bold"
            self.dc_power_supply_serv_label["foreground"] ="white"

    # -----------------------------------------------------------------------------
    # Signal generator functions
    # -----------------------------------------------------------------------------  
    def find_rf_signal_generator(self, button_normal_on_complete=True):
        """
        This method searches for connected signal generators and populates the relevant GUI box with the first SG which is connected and supported
        :param button_normal_on_complete: Type: Boolean
        :return None
        """
        log.info("INFO - Checking for connected signal generators...")
        self.rf_signal_generator_label1["text"] = "........"
        self.rf_signal_generator_label1["foreground"] = "orange"
        self.rf_signal_generator_label1["background"] = "white"
        self.rf_signal_generator_serv_button["state"] = DISABLED
        self.rf_signal_generator_connected_label["text"] = "------------"
        
        # Attempt to find and initialise the RF Signal Generator
        [is_device_initalized, model] = self.sgs.sg.device_specific_initialisation()
        if is_device_initalized:
            self.rf_signal_generator_connected_label["text"] = model
            self.rf_signal_generator_label1["text"] = "SG Found"
            self.rf_signal_generator_label1["font"] = "Arial 9 bold"
            self.rf_signal_generator_label1["foreground"] = "green"
            self.rf_signal_generator_label1["background"] = "white"
            log.info("INFO - Found Signal Generator: {}".format(model))
        else:
            self.rf_signal_generator_label1["text"] = "Not found"
            self.rf_signal_generator_label1["font"] = "Arial 9 bold"
            self.rf_signal_generator_label1["foreground"] = "red"
            self.rf_signal_generator_label1["background"] = "white"
            log.info("INFO - Did not find any connected signal generators!")
            self.sg = None
        
        if button_normal_on_complete:
            self.rf_signal_generator_serv_button["state"] = NORMAL
        
        return bool(self.sg is not None)

    def start_rf_signal_generator_service(self):
        """
        This method starts the SG service
        :param None
        :return None
        """
        log.info("INFO - Starting Signal Generator Service Thread...")
        self.rf_signal_generator_serv_button["state"] = DISABLED
        self.rf_signal_generator_serv_label["text"] = "Starting SG Service..."   
        self.rf_signal_generator_serv_label["font"] = "Arial 11 bold" 
        self.rf_signal_generator_serv_label["background"] = "white"      
        self.rf_signal_generator_serv_label["foreground"] = "orange"     
        
        # Start a signal generator service thread
        Thread(target=self.start_rf_signal_generator_service_thread).start()
    
    def stop_rf_signal_generator_service(self):
        """
        This method stops the SG service
        :param None
        :return None
        """
        log.info("INFO - Stopping Signal Generator Service Thread...")
        self.rf_signal_generator_serv_label["text"] = "SG Service Stopped..."        
        self.rf_signal_generator_serv_label["font"] = "Arial 11 bold" 
        self.rf_signal_generator_serv_label["background"] = "white"      
        self.rf_signal_generator_serv_label["foreground"] = "red"
        self.rf_signal_generator_serv_button["text"] = "Start SG Service"
        self.rf_signal_generator_serv_button["state"] = NORMAL
        self.rf_signal_generator_ip_combobox["state"] = NORMAL
        self.rf_signal_generator_serv_button.configure(command=self.start_rf_signal_generator_service)
        
        # Stop the signal generator service thread
        self.sgs_thread.quit()
        self.sgs.is_thread_running = False
        self._sg_service_created = False
        # Close the resource manager connection
        self.sgs.sg.visa_te.sg.rm.close()

        # Check if any of the other services are running
        if not (self._psu_service_created or self._sa_service_created or self._pm_service_created):
            # Reconfigure button to be able to start all services
            self.start_all_services_button["state"] = NORMAL
            self.start_all_services_button["text"] = "Start All Services"
            self.start_all_services_button.configure(command=self.start_all_services)
            self.find_ip_adapter_button["state"] = NORMAL

    
    def start_rf_signal_generator_service_thread(self):
        """
        This method starts the SG service thread
        :param None
        :return None
        """
        self.sgs = SignalGeneratorService()
        [is_device_initalized, model] = self.sgs.sg.device_specific_initialisation()
        self._sg_service_created = True
        # Attempt to find and initialise the RF Signal Generator
        # self.find_rf_signal_generator()
        if is_device_initalized:
            self._sg_service_created = True
            if self.sgs.ips:
                self.sgs.ip = self.rf_signal_generator_ip_combobox.get()

                # Check for a valid IP adapter selection
                if self.sgs.ip == "Select SGS IP Adapter":

                    self.instruction_dialog("INFO - SG Service: Please select a valid IP adapter before proceeding!")
                    self.rf_signal_generator_serv_label["text"] = "SG Service Not Started..."        
                    self.rf_signal_generator_serv_label["font"] = "Arial 11 bold" 
                    self.rf_signal_generator_serv_label["background"] = "gray32"      
                    self.rf_signal_generator_serv_label["foreground"] = "white"
                    self.rf_signal_generator_serv_button["state"] = NORMAL
                    self._sg_service_created = False
                else:
                    log.info("INFO - Selecting network interface with IP address {}".format(self.sgs.ip))
                    log.info("INFO - Starting TCP/IP listener on port {}".format(self.sgs.port))
                    self.sgs_thread = SGSAccept(self.sgs.ip, self.sgs.port, self.sgs, self.sgs.sg)
                    self.sgs_thread.start()
                    log.info("INFO - Registering service for signal generator {}".format(model))
                    self.sgs.register_service()
                    if self.sgs.sg.binding_success:
                        self._sg_service_created = True
                        self.sgs.is_thread_running = True
                        log.info("INFO - Registering signal generator service successfull")
                        log.info("INFO - Signal generator service is running...")
                        self.rf_signal_generator_serv_label["text"] = "SG Service Running..."   
                        self.rf_signal_generator_serv_label["font"] = "Arial 11 bold"       
                        self.rf_signal_generator_serv_label["background"] = "white"
                        self.rf_signal_generator_serv_label["foreground"] = "green"
                        self.rf_signal_generator_serv_button["text"] = "Stop SG Service"
                        self.rf_signal_generator_serv_button["state"] = NORMAL
                        self.rf_signal_generator_serv_button.configure(command=self.stop_rf_signal_generator_service)
                        self.rf_signal_generator_ip_combobox["state"] = DISABLED
                        self.find_ip_adapter_button["state"] = DISABLED
                        # Reconfigure start all services button to be able to stop all services
                        self.start_all_services_button["state"] = NORMAL
                        self.start_all_services_button["text"] = "Stop All Services"
                        self.start_all_services_button.configure(command=self.stop_all_services)
                    else:
                        log.info("ERROR - Failed to register signal generator service!")
                        self.rf_signal_generator_serv_label["text"] = "SG Service Not Started..."        
                        self.rf_signal_generator_serv_label["font"] = "Arial 11 bold" 
                        self.rf_signal_generator_serv_label["background"] = "gray32"      
                        self.rf_signal_generator_serv_label["foreground"] = "white"
                        self.rf_signal_generator_serv_button["state"] = NORMAL
                        self.sgs.is_thread_running = False
                        self._sg_service_created = False
                        self.sgs_thread.quit()
            else:
                self._sg_service_created = False
                log.info("ERROR - no candidate network interface found!")
                self.rf_signal_generator_serv_label["text"] = "SG Service Not Started..."        
                self.rf_signal_generator_serv_label["font"] = "Arial 11 bold" 
                self.rf_signal_generator_serv_label["background"] = "gray32"      
                self.rf_signal_generator_serv_label["foreground"] = "white"
                self.rf_signal_generator_serv_button["state"] = NORMAL
        else:
            self._sg_service_created = False
            log.info("ERROR - Could not find signal generator!")
            log.info("ERROR - Stopping Signal generator Service...")
            self.rf_signal_generator_serv_label["text"] = "SG Service Not Started..."        
            self.rf_signal_generator_serv_label["font"] = "Arial 11 bold" 
            self.rf_signal_generator_serv_label["background"] = "gray32"      
            self.rf_signal_generator_serv_label["foreground"] = "white"
            self.rf_signal_generator_serv_button["state"] = NORMAL

    # -----------------------------------------------------------------------------
    # Spectrum analyser functions
    # -----------------------------------------------------------------------------
    
    def find_rf_spectrum_analyser(self, button_normal_on_complete=True):
        """
        This method searches for connected spectrum analysers and populates the relevant GUI box with the first SA which is connected and supported
        :param button_normal_on_complete: Type: Boolean
        :return None
        """
        log.info("INFO - Checking for connected spectrum analysers...")
        self.rf_spectrum_analyser_label1["text"] = "........"
        self.rf_spectrum_analyser_label1["foreground"] = "orange"
        self.rf_spectrum_analyser_label1["background"] = "white"
        self.rf_spectrum_analyser_serv_button["state"] = DISABLED
        self.rf_spectrum_analyser_connected_label["text"] = "------------"

        # Attempt to find and initialise the RF Spectrum Analyser
        [is_device_initalized, model] = self.sas.sa.device_specific_initialisation()
        if is_device_initalized:
            self.rf_spectrum_analyser_connected_label["text"] = model
            self.rf_spectrum_analyser_label1["text"] = "SA Found"
            self.rf_spectrum_analyser_label1["font"] = "Arial 9 bold"
            self.rf_spectrum_analyser_label1["foreground"] = "green"
            self.rf_spectrum_analyser_label1["background"] = "white"
            log.info("INFO - Found Spectrum Analyser: {}".format(model))
        else:
            self.rf_spectrum_analyser_label1["text"] = "Not found"
            self.rf_spectrum_analyser_label1["font"] = "Arial 9 bold"
            self.rf_spectrum_analyser_label1["foreground"] = "red"
            self.rf_spectrum_analyser_label1["background"] = "white"
            self.rf_spectrum_analyser_serv_button["state"] = NORMAL
            log.info("INFO - Did not find any connected spectrum analysers!")
            self.sa = None
        
        if button_normal_on_complete:
            self.rf_spectrum_analyser_serv_button["state"] = NORMAL

        return bool(self.sa is not None)

    def start_rf_spectrum_analyser_service(self):
        """
        This method starts the SA service
        :param None
        :return None
        """
        log.info("INFO - Starting Spectrum Analyser Service Thread...")
        self.rf_spectrum_analyser_serv_button["state"] = DISABLED
        self.rf_spectrum_analyser_serv_label["text"] = "Starting SA Service..." 
        self.rf_spectrum_analyser_serv_label["font"] = "Arial 11 bold" 
        self.rf_spectrum_analyser_serv_label["background"] = "white"      
        self.rf_spectrum_analyser_serv_label["foreground"] = "orange"
        
        # Start a Spectrum Analyser service thread
        Thread(target=self.start_rf_spectrum_analyser_service_thread).start()
    
    def stop_rf_spectrum_analyser_service(self):
        """
        This method stops the SA service
        :param None
        :return None
        """
        log.info("INFO - Stopping Spectrum Analyser Service Thread...")
        self.rf_spectrum_analyser_serv_label["text"] = "SA Service Stopped..."   
        self.rf_spectrum_analyser_serv_label["font"] = "Arial 11 bold" 
        self.rf_spectrum_analyser_serv_label["background"] = "white"      
        self.rf_spectrum_analyser_serv_label["foreground"] = "red"
        self.rf_spectrum_analyser_serv_button["text"] = "Start SA Service"
        self.rf_spectrum_analyser_serv_button["state"] = NORMAL
        self.rf_spectrum_analyser_ip_combobox["state"] = NORMAL
        self.rf_spectrum_analyser_serv_button.configure(command=self.start_rf_spectrum_analyser_service)
        
        # Stop the Spectrum Analyser service thread
        self.sas_thread.quit()
        self._sa_service_created = False
        self.sas.is_thread_running = False
        # Close the resource manager connection
        self.sas.sa.visa_te.sa.rm.close()

        # Check if any of the other services are running
        if not (self._psu_service_created or self._sg_service_created or self._pm_service_created):
            # Reconfigure button to be able to start all services
            self.start_all_services_button["state"] = NORMAL
            self.start_all_services_button["text"] = "Start All Services"
            self.start_all_services_button.configure(command=self.start_all_services)
            self.find_ip_adapter_button["state"] = NORMAL
    
    def start_rf_spectrum_analyser_service_thread(self):
        """
        This method starts the SA service thread
        :param None
        :return None
        """
        self.sas = SpectrumAnalyserService()
        [is_device_initalized, model] = self.sas.sa.device_specific_initialisation()
        # self._sa_service_created = True
        # Attempt to find and initialise the RF Spectrum Analyser
        # self.find_rf_spectrum_analyser()
        if is_device_initalized:
            self._sa_service_created = True
            if self.sas.ips:              
                self.sas.ip = self.rf_spectrum_analyser_ip_combobox.get()

                # Check for a valid IP adapter selection
                if self.sas.ip == "Select SAS IP Adapter":

                    self.instruction_dialog("INFO - SA Service: Please select a valid IP adapter before proceeding!")
                    self.rf_spectrum_analyser_serv_button["state"] = NORMAL
                    self.rf_spectrum_analyser_serv_label["text"] = "SA Service Not Started"        
                    self.rf_spectrum_analyser_serv_label["background"] = "gray32"
                    self.rf_spectrum_analyser_serv_label["font"] ="Arial 11 bold"
                    self.rf_spectrum_analyser_serv_label["foreground"] ="white"
                    self._sa_service_created = False
                else:
                    log.info("INFO - Selecting network interface with IP address {}".format(self.sas.ip))
                    log.info("INFO - Starting TCP/IP listener on port {}".format(self.sas.port))
                    self.sas_thread = SASAccept(self.sas.ip, self.sas.port, self.sas, self.sas.sa)
                    self.sas_thread.start()
                    log.info("INFO - Registering service for spectrum analyser {}".format(model))
                    self.sas.register_service()
                    if self.sas.sa.binding_success:
                        self._sa_service_created = True
                        self.sas.is_thread_running = True
                        log.info("INFO - Registering spectrum analyser service successfull")
                        log.info("INFO - Spectrum analyser service is running...")
                        self.rf_spectrum_analyser_serv_label["text"] = "SA Service Running..."  
                        self.rf_spectrum_analyser_serv_label["font"] = "Arial 11 bold"       
                        self.rf_spectrum_analyser_serv_label["background"] = "white"  
                        self.rf_spectrum_analyser_serv_label["foreground"] = "green" 
                        self.rf_spectrum_analyser_serv_button["text"] = "Stop SA Service"
                        self.rf_spectrum_analyser_serv_button["state"] = NORMAL
                        self.rf_spectrum_analyser_serv_button.configure(command=self.stop_rf_spectrum_analyser_service)
                        self.rf_spectrum_analyser_ip_combobox["state"] = DISABLED
                        self.find_ip_adapter_button["state"] = DISABLED
                        # Reconfigure start all services button to be able to stop all services
                        self.start_all_services_button["state"] = NORMAL
                        self.start_all_services_button["text"] = "Stop All Services"
                        self.start_all_services_button.configure(command=self.stop_all_services)
                    else:
                        log.info("ERROR - Failed to register spectrum analyser service!")
                        self.rf_spectrum_analyser_serv_button["state"] = NORMAL
                        self.rf_spectrum_analyser_serv_label["text"] = "SA Service Not Started"        
                        self.rf_spectrum_analyser_serv_label["background"] = "gray32"
                        self.rf_spectrum_analyser_serv_label["font"] ="Arial 11 bold"
                        self.rf_spectrum_analyser_serv_label["foreground"] ="white"
                        self._sa_service_created = False
                        self.sas.is_thread_running = False
                        self.sas_thread.quit()
            else:
                self._sa_service_created = False
                log.info("ERROR - No candidate network interface found!")
                self.rf_spectrum_analyser_serv_button["state"] = NORMAL
                self.rf_spectrum_analyser_serv_label["text"] = "SA Service Not Started"        
                self.rf_spectrum_analyser_serv_label["background"] = "gray32"
                self.rf_spectrum_analyser_serv_label["font"] ="Arial 11 bold"
                self.rf_spectrum_analyser_serv_label["foreground"] ="white"
        else:
            self._sa_service_created = False
            log.info("ERROR - Could not find spectrum analyser!")
            log.info("ERROR - Stopping Spectrum Analyser Service...")
            self.rf_spectrum_analyser_serv_button["state"] = NORMAL
            self.rf_spectrum_analyser_serv_label["text"] = "SA Service Not Started"        
            self.rf_spectrum_analyser_serv_label["background"] = "gray32"
            self.rf_spectrum_analyser_serv_label["font"] ="Arial 11 bold"
            self.rf_spectrum_analyser_serv_label["foreground"] ="white"

    # -----------------------------------------------------------------------------
    # Power meter functions
    # -----------------------------------------------------------------------------
    
    def find_power_meter(self, button_normal_on_complete=True):
        """
        This method searches for connected power meters and populates the relevant GUI box with the first PM which is connected and supported
        :param button_normal_on_complete: Type: Boolean
        :return None
        """
        log.info("INFO - Checking for connected power meters...")
        self.power_meter_check_label1["text"] = "........"
        self.power_meter_check_label1["foreground"] = "orange"
        self.power_meter_check_label1["background"] = "white"
        self.power_meter_serv_button["state"] = DISABLED
        self.power_meter_connected_label["text"] = "------------"

        
        # Attempt to find and initialise the Power Meter
        [is_device_initalized, model] = self.pms.pm.device_specific_initialisation()
        if is_device_initalized:
            self.power_meter_connected_label["text"] = model
            self.power_meter_check_label1["text"] = "PM Found"
            self.power_meter_check_label1["font"] = "Arial 9 bold"
            self.power_meter_check_label1["foreground"] = "green"
            self.power_meter_check_label1["background"] = "white"
            log.info("INFO - Found Power Meter: {}".format(model))
        else:
            self.power_meter_check_label1["text"] = "Not found"
            self.power_meter_check_label1["font"] = "Arial 9 bold"
            self.power_meter_check_label1["foreground"] = "red"
            self.power_meter_check_label1["background"] = "white"
            self.power_meter_connected_label["text"] = "------------"
            log.info("INFO - Did not find any connected power meters!")
            self.pm = None
        
        if button_normal_on_complete:
            self.power_meter_serv_button["state"] = NORMAL
        
        # Close the resource manager connection
        self.pms.pm.visa_te.pm.rm.close()

        return bool(self.pm is not None)

    def start_power_meter_service(self):
        """
        This method starts the PM service
        :param None
        :return None
        """
        log.info("INFO - Starting Power Meter Service Thread...")
        self.power_meter_serv_button["state"] = DISABLED
        self.power_meter_serv_label["text"] = "Starting PM Service..." 
        self.power_meter_serv_label["font"] = "Arial 11 bold" 
        self.power_meter_serv_label["background"] = "white"      
        self.power_meter_serv_label["foreground"] = "orange"
        
        # Start a power meter service thread
        Thread(target=self.start_power_meter_service_thread).start()

    def stop_power_meter_service(self):
        """
        This method stops the PM service
        :param None
        :return None
        """
        log.info("INFO - Stopping Power Meter Service Thread...")
        self.power_meter_serv_label["text"] = "PM Service Stopped..."   
        self.power_meter_serv_label["font"] = "Arial 11 bold" 
        self.power_meter_serv_label["background"] = "white"      
        self.power_meter_serv_label["foreground"] = "red"
        self.power_meter_serv_button["text"] = "Start PM Service"
        self.power_meter_serv_button["state"] = NORMAL
        self.power_meter_ip_combobox["state"] = NORMAL
        self.power_meter_serv_button.configure(command=self.start_power_meter_service)
        
        # Stop the power meter service thread
        self.pms_thread.quit()
        self._pm_service_created = False
        self.pms.is_thread_running = False
        # Close the resource manager connection
        self.pms.pm.visa_te.pm.rm.close()

        # Check if any other services are running
        if not (self._psu_service_created or self._sg_service_created or self._sa_service_created):
            # Reconfigure button to be able to start all services
            self.start_all_services_button["state"] = NORMAL
            self.start_all_services_button["text"] = "Start All Services"
            self.start_all_services_button.configure(command=self.start_all_services)
            self.find_ip_adapter_button["state"] = NORMAL

    def start_power_meter_service_thread(self):
        """
        This method starts the PM service thread
        :param None
        :return None
        """
        self.pms = PowerMeterService()
        [is_device_initalized, model] = self.pms.pm.device_specific_initialisation()
        # self._pm_service_created = True
        # Attempt to find and initialise the power meter
        # self.find_power_meter()
        if is_device_initalized:
            self._pm_service_created = True
            if self.pms.ips:
                self.pms.ip = self.power_meter_ip_combobox.get()

                # Check for a valid IP adapter selection
                if self.pms.ip == "Select PMS IP Adapter":

                    self.instruction_dialog("INFO - PM Service: Please select a valid IP adapter before proceeding!")
                    self.power_meter_serv_label["text"] = "PM Service Not Started"        
                    self.power_meter_serv_label["background"] = "gray32"
                    self.power_meter_serv_label["font"] ="Arial 11 bold"
                    self.power_meter_serv_label["foreground"] ="white"
                    self._pm_service_created = False

                else:
                    log.info("INFO - Selecting network interface with IP address {}".format(self.pms.ip))
                    log.info("INFO - Starting TCP/IP listener on port {}".format(self.pms.port))
                    self.pms_thread = PMSAccept(self.pms.ip, self.pms.port, self.pms, self.pms.pm)
                    self.pms_thread.start()
                    log.info("INFO - Registering power meter service for power meter {}".format(model))
                    self.pms.register_service()
                    if self.pms.pm.binding_success:
                        log.info("INFO - Registering power meter service successfull")
                        log.info("INFO - Power meter service is running...")
                        self._pm_service_created = True
                        self.pms.is_thread_running = True
                        self.power_meter_serv_label["text"] = "PM Service Running..."  
                        self.power_meter_serv_label["font"] = "Arial 11 bold"       
                        self.power_meter_serv_label["background"] = "white"  
                        self.power_meter_serv_label["foreground"] = "green" 
                        self.power_meter_serv_button["text"] = "Stop PM Service"
                        self.power_meter_serv_button["state"] = NORMAL
                        self.power_meter_serv_button.configure(command=self.stop_power_meter_service)
                        self.power_meter_ip_combobox["state"] = DISABLED
                        self.find_ip_adapter_button["state"] = DISABLED
                        # Reconfigure start all services button to be able to stop all services
                        self.start_all_services_button["state"] = NORMAL
                        self.start_all_services_button["text"] = "Stop All Services"
                        self.start_all_services_button.configure(command=self.stop_all_services)
                    else:
                        log.info("ERROR - Failed to register power meter service!")
                        self.power_meter_serv_button["state"] = NORMAL
                        self.power_meter_serv_label["text"] = "PM Service Not Started"        
                        self.power_meter_serv_label["background"] = "gray32"
                        self.power_meter_serv_label["font"] ="Arial 11 bold"
                        self.power_meter_serv_label["foreground"] ="white"
                        self._pm_service_created = False
                        self.pms.is_thread_running = False
                        self.pms_thread.quit()
            else:
                self._pm_service_created = False
                log.info("ERROR - No candidate network interface found!")
                self.power_meter_serv_button["state"] = NORMAL
                self.power_meter_serv_label["text"] = "PM Service Not Started"        
                self.power_meter_serv_label["background"] = "gray32"
                self.power_meter_serv_label["font"] ="Arial 11 bold"
                self.power_meter_serv_label["foreground"] ="white"

        else:
            self._pm_service_created = False
            log.info("ERROR - Could not find power meter!")
            log.info("ERROR - Stopping Power Meter Service...")
            self.power_meter_serv_button["state"] = NORMAL
            self.power_meter_serv_label["text"] = "PM Service Not Started"        
            self.power_meter_serv_label["background"] = "gray32"
            self.power_meter_serv_label["font"] ="Arial 11 bold"
            self.power_meter_serv_label["foreground"] ="white"

    def start_all_services(self):
        """
        This method starts all running services
        :param None
        :return None
        """
        self.start_dc_power_supply_service()
        self.start_rf_signal_generator_service()
        self.start_rf_spectrum_analyser_service()
        self.start_power_meter_service()

    def stop_all_services(self):
        """
        This method stops all running services
        :param None
        :return None
        """
        # Stop the power supply service thread if it is running
        if self._psu_service_created and self.psus.is_thread_running:
            self.stop_dc_power_supply_service()
        # Stop the signal generator service thread if it is running
        if self._sg_service_created and self.sgs.is_thread_running:
            self.stop_rf_signal_generator_service()
        # Stop the spectrum analyser service thread if it is running
        if self._sa_service_created and self.sas.is_thread_running:
            self.stop_rf_spectrum_analyser_service()
        # Stop the power meter service thread if it is running
        if self._pm_service_created and self.pms.is_thread_running:
            self.stop_power_meter_service()
        
        # Reconfigure button to be able to start all services
        self.start_all_services_button["state"] = NORMAL
        self.start_all_services_button["text"] = "Start All Services"
        self.start_all_services_button.configure(command=self.start_all_services)
        self.find_ip_adapter_button["state"] = NORMAL

    def on_closing(self):
        if tk.messagebox.askyesno("Exit", "Do you want to quit the application?"):
            # Stop the power meter service thread if it is running
            if self._pm_service_created and self.pms.is_thread_running:
                self.pms_thread.quit()
            # Stop the signal generator service thread if it is running
            if self._sg_service_created and self.sgs.is_thread_running:
                self.sgs_thread.quit()
            # Stop the spectrum analyser service thread if it is running
            if self._sa_service_created and self.sas.is_thread_running:
                self.sas_thread.quit()
            # Stop the power supply service thread if it is running
            if self._psu_service_created and self.psus.is_thread_running:
                self.psus_thread.quit()

            # Close the window
            self.destroy()

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


       
# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = TestEquipServiceGui()
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
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S", stream=sys.stdout)

    main()
