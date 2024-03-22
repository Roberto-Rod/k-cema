#!/usr/bin/env python3
"""
Tkinter GUI application for interfacing with the Active Backplane Firmware,
KT-656-0194-00 serial interface, ICD KT-957-0143-00
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
import logging
import tkinter as tk
from tkinter import filedialog

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
import ab_program_devices as apd
from ab_serial_msg_intf import AbSerialMsgInterface, AbMsgId, AbMsgPayloadLen
import mac_address

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_VERSION = "V1.1.0"
DEFAULT_COM_PORT = "COM4"
DEFAULT_BAUD_RATE = 115200

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class AbTestGui:
    """
    Tkinter GUI application class, all the functionality and methods needed
    to create, update and interact with the GUI window are in this class
    """
    _HW_INFO_NUM_ITEMS = 6
    _HW_INFO_LABELS = ["Assembly Part No", "Assembly Revision No", "Assembly Serial No",
                       "Assembly Build Date/Batch No", "Bare PCB Revision", "Modification Level"]
    _UNIT_INFO_NUM_ITEMS = 5
    _UNIT_INFO_LABELS = ["Status", "Assembly Part No (15-chars max)", "Assembly Revision No (15-chars max)",
                         "Assembly Serial No (15-chars max)", "Assembly Build Date/Batch No (15-chars max)"]

    _BIT_INFO_NUM_ITEMS = 7
    _BIT_INFO_LABELS = ["Flags", "+1V0 (mV)", "+2V5 (mV)", "Ambient Temp (deg C)",
                        "Eth Switch Junc Temp (deg C)", "Eth PHY Junc Temp (deg C)", "Micro Junc Temp (deg C)"]

    def __init__(self):
        """
        Class constructor, initialises the Tkinter GUI window and adds all the widgets to it.

        All of the text boxes on the GUI window have associated tk.StringVar variables which
        are used to get/set the displayed text.  Text boxes used solely for reporting purposes
        are set as read-only
        """
        self._window = tk.Tk()
        self.initialise_window()
        row = 0

        # COM Port Widgets
        row += 1
        self._com_port_lbl = tk.Label(self._window, text="Com Port:").grid(column=1, row=row, sticky="w",
                                                                           padx=2, pady=2)
        self._com_port_var = tk.StringVar()
        self._com_port_var.set(DEFAULT_COM_PORT)
        self._com_port_txt = tk.Entry(self._window, textvariable=self._com_port_var, width=30)
        self._com_port_txt.grid(column=2, row=row, sticky="w", padx=2, pady=2)

        # Ping Command Widgets
        row += 1
        self._ping_btn = tk.Button(self._window, text="Ping", command=self.ping_cmd)
        self._ping_btn.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._ping_success_var = tk.StringVar()
        self._ping_success_var.set("N/A")
        self._ping_success_txt = tk.Entry(self._window, textvariable=self._ping_success_var, width=30)
        self._ping_success_txt.grid(column=2, row=row, sticky="w", padx=2, pady=2)
        self._ping_success_txt.configure(state="readonly")

        # Software Version Widgets
        row += 1
        self._get_sw_ver_btn = tk.Button(self._window, text="Read Sw Version", command=self.get_sw_ver_cmd)
        self._get_sw_ver_btn.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._sw_ver_var = tk.StringVar()
        self._sw_ver_var.set("N/A")
        self._sw_ver_txt = tk.Entry(self._window, textvariable=self._sw_ver_var, width=30)
        self._sw_ver_txt.grid(column=2, row=row, sticky="w", padx=2, pady=2)
        self._sw_ver_txt.configure(state="readonly")

        # Hw Information Widgets
        row += 1
        self._get_hw_info_btn = tk.Button(self._window, text="Read Hw Info", command=self.get_hw_info_cmd)
        self._get_hw_info_btn.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._hw_info_str_var = []
        self._hw_info_txt_entry = []
        self._hw_info_label = []

        for i in range(0, self._HW_INFO_NUM_ITEMS):
            str_var = tk.StringVar()
            str_var.set("N/A")
            self._hw_info_str_var.append(str_var)

            txt_var = tk.Entry(self._window, textvariable=self._hw_info_str_var[i], width=30)
            txt_var.grid(column=2, row=row, sticky="w", padx=2, pady=2)
            txt_var.configure(state="readonly")
            self._hw_info_txt_entry.append(txt_var)

            lbl_var = tk.Label(self._window, text=self._HW_INFO_LABELS[i]).grid(column=3, row=row, sticky="w",
                                                                                padx=2, pady=2)
            self._hw_info_label.append(lbl_var)

            row += 1
        row -= 1

        # Unit Information Widgets
        row += 1
        self._get_unit_info_btn = tk.Button(self._window, text="Read Unit Info", command=self.get_unit_info_cmd)
        self._get_unit_info_btn.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._set_unit_info_btn = tk.Button(self._window, text="Set Unit Info", command=self.set_unit_info_cmd)
        self._set_unit_info_btn.grid(column=1, row=row+1, sticky="w", padx=2, pady=2)

        self._unit_info_str_var = []
        self._unit_info_txt_entry = []
        self._unit_info_label = []

        for i in range(0, self._UNIT_INFO_NUM_ITEMS):
            str_var = tk.StringVar()
            str_var.set("N/A")
            self._unit_info_str_var.append(str_var)

            txt_var = tk.Entry(self._window, textvariable=self._unit_info_str_var[i], width=30)
            txt_var.grid(column=2, row=row, sticky="w", padx=2, pady=2)
            self._unit_info_txt_entry.append(txt_var)

            lbl_var = tk.Label(self._window, text=self._UNIT_INFO_LABELS[i]).grid(column=3, row=row, sticky="w",
                                                                                  padx=2, pady=2)
            self._unit_info_label.append(lbl_var)

            row += 1
        row -= 1
        # Set the Status text box read only
        self._unit_info_txt_entry[0].configure(state="readonly")

        # BIT Information Widgets
        row += 1
        self._get_bit_info_btn = tk.Button(self._window, text="Read BIT Info", command=self.get_bit_info_cmd)
        self._get_bit_info_btn.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._bit_info_str_var = []
        self._bit_info_txt_entry = []
        self._bit_info_label = []

        for i in range(0, self._BIT_INFO_NUM_ITEMS):
            str_var = tk.StringVar()
            str_var.set("N/A")
            self._bit_info_str_var.append(str_var)

            txt_var = tk.Entry(self._window, textvariable=self._bit_info_str_var[i], width=30)
            txt_var.grid(column=2, row=row, sticky="w")
            txt_var.configure(state="readonly")
            self._bit_info_txt_entry.append(txt_var)

            lbl_var = tk.Label(self._window, text=self._BIT_INFO_LABELS[i]).grid(column=3, row=row, sticky="w")
            self._bit_info_label.append(lbl_var)

            row += 1
        row -= 1

        # Get Slot Number Widgets
        row += 1

        self._get_slot_no_btn = tk.Button(self._window, text="Get Slot Number", command=self.get_slot_no_cmd)
        self._get_slot_no_btn.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._mac_addr_var = tk.StringVar()
        self._mac_addr_var.set("00-00-00-00-00-00")
        self._mac_addr_txt = tk.Entry(self._window, textvariable=self._mac_addr_var, width=30)
        self._mac_addr_txt.grid(column=2, row=row, sticky="w", padx=2, pady=2)

        self._slot_no_var = tk.StringVar()
        self._slot_no_var.set("N/A")
        self._slot_no_txt = tk.Entry(self._window, textvariable=self._slot_no_var, width=40)
        self._slot_no_txt.grid(column=3, row=row, sticky="w", padx=2, pady=2)
        self._slot_no_txt.configure(state="readonly")

        # Erase/Program Micro Widgets
        row += 1

        self._erase_micro = tk.Button(self._window, text="Erase Micro", command=self.erase_micro)
        self._erase_micro.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._program_micro = tk.Button(self._window, text="Program Micro", command=self.program_micro)
        self._program_micro.grid(column=2, row=row, sticky="w", padx=2, pady=2)

        self._erase_prog_micro_var = tk.StringVar()
        self._erase_prog_micro_var.set("N/A")
        self._erase_prog_micro_txt = tk.Entry(self._window, textvariable=self._erase_prog_micro_var, width=40)
        self._erase_prog_micro_txt.grid(column=3, row=row, sticky="w", padx=2, pady=2)

        # Erase/Program GbE Switch Widgets
        row += 1

        self._erase_gbe_sw = tk.Button(self._window, text="Erase GbE Switch", command=self.erase_gbe_sw)
        self._erase_gbe_sw.grid(column=1, row=row, sticky="w", padx=2, pady=2)

        self._program_gbe_sw = tk.Button(self._window, text="Program GbE Switch", command=self.program_gbe_sw)
        self._program_gbe_sw.grid(column=2, row=row, sticky="w", padx=2, pady=2)

        self._erase_prog_gbe_sw_var = tk.StringVar()
        self._erase_prog_gbe_sw_var.set("N/A")
        self._erase_prog_gbe_sw_txt = tk.Entry(self._window, textvariable=self._erase_prog_gbe_sw_var, width=40)
        self._erase_prog_gbe_sw_txt.grid(column=3, row=row, sticky="w", padx=2, pady=2)

    def run(self):
        """
        Tkinter GUI application main loop
        :return:
        """
        self._window.mainloop()

    def initialise_window(self):
        """
        Set up the Tkinter window title and overall geometry
        :return: None
        """
        self._window.title("K-CEMA Active Backplane Test GUI - {}".format(SW_VERSION))
        self._window.geometry("550x625")

    def ping_cmd(self):
        """
        Command handler for the "Ping" button, sends a Ping message to the
        Active Backplane and processes the response reporting success or failure
        :return: None
        """
        self._ping_success_var.set("Pinging...")
        self._ping_success_txt.update()

        try:
            with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                if absi.send_ping():
                    self._ping_success_var.set("Ping Success")
                else:
                    self._ping_success_var.set("Ping Fail")
        except Exception as ex:
            self._ping_success_var.set("{}".format(ex))

    def get_sw_ver_cmd(self):
        """
        Command handler for the "Read Sw Version" button, sends a Read Software Version
        request to the Active Backplane and processes the response reporting the
        received software version if the request is successful or an appropriate fault message
        :return: None
        """
        self._sw_ver_var.set("Reading Sw Version...")
        self._sw_ver_txt.update()

        try:
            with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                result, msg = absi.get_command(AbMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                               AbMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)
                if result:
                    payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                        absi.unpack_get_software_version_number_response(msg)
                    self._sw_ver_var.set("{}.{}.{}:{}".format(sw_major, sw_minor, sw_patch, sw_build))
                else:
                    self._sw_ver_var.set("Sw Version Read Fail")
        except Exception as ex:
            self._sw_ver_var.set("{}".format(ex))

    def get_hw_info_cmd(self):
        """
        Command handler for the "Read Hw Info" button, sends a Read Hardware Information
        request to the Active Backplane and processes the response reporting the
        received hardware information if the request is successful or an appropriate fault message
        :return: None
        """
        self._hw_info_str_var[0].set("Reading Hw Info...")
        for i in range(1, self._HW_INFO_NUM_ITEMS):
            self._hw_info_str_var[i].set("N/A")
        self._hw_info_txt_entry[0].update()

        try:
            with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                result, msg = absi.get_command(AbMsgId.GET_HARDWARE_INFO, AbMsgPayloadLen.GET_HARDWARE_INFO)
                if result:
                    payload_version, assy_part_no, assy_rev_no, assy_serial_no, \
                        assy_build_date_batch_no, bare_pcb_rev, mod_level = \
                        absi.unpack_get_hardware_info_response(msg)
                    self._hw_info_str_var[0].set("{}".format(assy_part_no))
                    self._hw_info_str_var[1].set("{}".format(assy_rev_no))
                    self._hw_info_str_var[2].set("{}".format(assy_serial_no))
                    self._hw_info_str_var[3].set("{}".format(assy_build_date_batch_no))
                    self._hw_info_str_var[4].set("{}".format(bare_pcb_rev))
                    self._hw_info_str_var[5].set("{}".format(mod_level))
                else:
                    self._hw_info_str_var[0].set("Hw Info Read Fail")
        except Exception as ex:
            self._hw_info_str_var[0].set("{}".format(ex))

    def get_unit_info_cmd(self):
        """
        Command handler for the "Read Unit Info" button, sends a Read Unit Information
        request to the Active Backplane and processes the response reporting the
        received unit information if the request is successful or an appropriate fault message
        :return: None
        """
        self._unit_info_str_var[0].set("Reading Unit Info...")
        for i in range(1, self._UNIT_INFO_NUM_ITEMS):
            self._unit_info_str_var[i].set("N/A")
        self._unit_info_txt_entry[0].update()

        try:
            with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                result, msg = absi.get_command(AbMsgId.GET_UNIT_INFO, AbMsgPayloadLen.GET_UNIT_INFO)
                if result:
                    payload_version, status, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no = \
                        absi.unpack_get_unit_info_response(msg)
                    self._unit_info_str_var[0].set("{}".format(status))
                    self._unit_info_str_var[1].set("{}".format(assy_part_no))
                    self._unit_info_str_var[2].set("{}".format(assy_rev_no))
                    self._unit_info_str_var[3].set("{}".format(assy_serial_no))
                    self._unit_info_str_var[4].set("{}".format(assy_build_date_batch_no))
                else:
                    self._unit_info_str_var[0].set("Unit Info Read Fail")
        except Exception as ex:
            self._unit_info_str_var[0].set("{}".format(ex))

    def set_unit_info_cmd(self):
        """
        Command handler for the "Set Unit Info" button, sends a Set Unit Information
        command to the Active Backplane and processes the response reporting success
        or an appropriate fault message
        :return: None
        """
        self._unit_info_str_var[0].set("Setting Unit Info...")
        self._unit_info_txt_entry[0].update()

        try:
            with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                if absi.send_set_unit_info(self._unit_info_str_var[1].get(),
                                           self._unit_info_str_var[2].get(),
                                           self._unit_info_str_var[3].get(),
                                           self._unit_info_str_var[4].get()):
                    self._unit_info_str_var[0].set("Set Unit Info Success")
                else:
                    self._unit_info_str_var[0].set("Set Unit Info Fail")
        except Exception as ex:
            self._unit_info_str_var[0].set("{}".format(ex))

    def get_bit_info_cmd(self):
        """
        Command handler for the "Read BIT Info" button, sends a Read Built-In Test Information
        request to the Active Backplane and processes the response reporting the
        received BIT information if the request is successful or an appropriate fault message
        :return: None
        """
        self._bit_info_str_var[0].set("Reading BIT Info...")
        for i in range(1, self._BIT_INFO_NUM_ITEMS):
            self._bit_info_str_var[i].set("N/A")
        self._bit_info_txt_entry[0].update()

        try:
            with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                result, msg = absi.get_command(AbMsgId.GET_BIT_INFO, AbMsgPayloadLen.GET_BIT_INFO)
                if result:
                    payload_version, flags, voltage_1v0_mv, voltage_2v5_mv, \
                        ambient_temp_deg, eth_sw_temp_deg, eth_phy_temp_deg, micro_temp_deg = \
                        absi.unpack_get_bit_info_response(msg)
                    self._bit_info_str_var[0].set("0x{}".format(format(flags, '02x')))
                    self._bit_info_str_var[1].set("{}".format(voltage_1v0_mv))
                    self._bit_info_str_var[2].set("{}".format(voltage_2v5_mv))
                    self._bit_info_str_var[3].set("{}".format(ambient_temp_deg))
                    self._bit_info_str_var[4].set("{}".format(eth_sw_temp_deg))
                    self._bit_info_str_var[5].set("{}".format(eth_phy_temp_deg))
                    self._bit_info_str_var[6].set("{}".format(micro_temp_deg))
                else:
                    self._bit_info_str_var[0].set("BIT Info Read Fail")
        except Exception as ex:
            self._bit_info_str_var[0].set("{}".format(ex))

    def get_slot_no_cmd(self):
        """
        Command handler for the "Get Slot Number" button, sends a Get Slot Number
        request to the Active Backplane and processes the response reporting the
        received slot number if the request is successful or an appropriate fault message
        :return: None
        """
        if mac_address.check_str_format(self._mac_addr_var.get()):
            self._slot_no_var.set("Getting Slot Number...")
            self._slot_no_txt.update()

            try:
                with AbSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE) as absi:
                    result, slot_no = absi.get_slot_no(self._mac_addr_var.get())

                    if result:
                        self._slot_no_var.set("{}".format(slot_no))
                    else:
                        self._slot_no_var.set("Get Slot Number Failed")
            except Exception as ex:
                self._slot_no_var.set("{}".format(ex))
        else:
            self._slot_no_var.set("Invalid MAC address format!")

    def erase_micro(self):
        """
        Command handler for the "Erase Micro" button, uses Segger J-Link to
        erase the KT-000-0139-00 microcontroller.
        :return: None
        """
        if apd.erase_micro_device():
            self._erase_prog_micro_var.set("Successfully Erased Microcontroller")
        else:
            self._erase_prog_micro_var.set("Failed to Erase Microcontroller!")

    def program_micro(self):
        """
        Command handler for the "Program Micro" button, uses Segger J-Link to
        program the KT-000-0139-00 microcontroller.
        :return: None
        """
        fn = filedialog.askopenfilename(filetypes=[("Bin Files", "*.bin")])

        if apd.program_micro_device(fn):
            self._erase_prog_micro_var.set("Successfully Programmed Microcontroller")
        else:
            self._erase_prog_micro_var.set("Failed to Program Microcontroller!")

    def erase_gbe_sw(self):
        """
        Command handler for the "Erase GbE Switch" button, uses ASIX PRESTO and
        UP software to erase the KT-000-0139-00 GbE Switch SPI FLash.
        :return: None
        """
        if apd.erase_gbe_sw_spi_flash():
            self._erase_prog_gbe_sw_var.set("Successfully Erased GbE Switch")
        else:
            self._erase_prog_gbe_sw_var.set("Failed to Erase GbE Switch!")

    def program_gbe_sw(self):
        """
        Command handler for the "Erase GbE Switch" button, uses ASIX PRESTO and
        UP software to program the KT-000-0139-00 GbE Switch SPI FLash.
        :return: None
        """
        fn = filedialog.askopenfilename(filetypes=[("Bin Files", "*.bin")])

        if apd.program_gbe_sw_spi_flash(fn):
            self._erase_p_erase_prog_gbe_sw_varrog_var.set("Successfully Programmed GbE Switch")
        else:
            self._erase_prog_gbe_sw_var.set("Failed to Program GbE Switch!")


# -----------------------------------------------------------------------------
# FUNCTIONS#
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = AbTestGui()
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
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    main()
