#!/usr/bin/env python3
"""
Tkinter GUI application for interfacing with the Integrated CTS Firmware,
KT-956-0265-00 serial interface, ICD KT-957-0413-00
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
import logging
import os
from threading import Event, Thread
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

# Third-party imports -----------------------------------------------
from PyCRC.CRCCCITT import CRCCCITT

# Our own imports ---------------------------------------------------
from cts_serial_msg_intf import CtsSerialMsgInterface, CtsSerialTcpMsgInterface, CtsMsgId, CtsMsgPayloadLen, \
    DEFAULT_RESPONSE_TIMEOUT as SERIAL_DEFAULT_RESPONSE_TIMEOUT

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_NO = "KT-956-0264-02"
SW_NAME = "K-CEMA Integrated CTS Test GUI"
SW_VERSION = "v1.0.1"
DEFAULT_COM_PORT = "COMx"
DEFAULT_BAUD_RATE = 115200

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class CtsTestGui:
    """
    Tkinter GUI application class, all the functionality and methods needed
    to create, update and interact with the GUI window are in this class
    """
    _ICON_FILE = "kirintec_logo.ico"
    _UNIT_INFO_LABELS = ["Status", "Assembly Part No (15-chars max)", "Assembly Revision No (15-chars max)",
                         "Assembly Serial No (15-chars max)", "Assembly Build Date/Batch No (15-chars max)"]
    _BIT_INFO_LABELS = ["Flags", "+12V (mV)", "+3V3 (mV)", "-3V3 (mV)", "+5V0 (mV)", "+3V3 IF (mV)", "+3V3 TX (mV)",
                        "+5V0 (mV)", "Micro Junc Temp (deg C)", "Ambient Temp (deg C)"]
    _TCP_PORT = 32

    def __init__(self):
        """
        Class constructor, initialises the Tkinter GUI window and adds all the widgets to it.

        All of the text boxes on the GUI window have associated tk.StringVar variables which
        are used to get/set the displayed text.  Text boxes used solely for reporting purposes
        are set as read-only
        """
        self._window = tk.Tk()
        self.initialise_window()
        self._cmd_buttons = {}
        row = 0

        # COM Port/Network Widgets
        row += 1
        self._com_port_lbl = tk.Label(self._window, text="Interface Address:").grid(column=1, row=row, sticky="w",
                                                                           padx=5, pady=5)
        self._com_port_var = tk.StringVar()
        self._com_port_var.set(DEFAULT_COM_PORT)
        self._com_port_txt = tk.Entry(self._window, textvariable=self._com_port_var, width=30)
        self._com_port_txt.grid(column=2, row=row, sticky="w", padx=5, pady=5)
        self._interface_type = tk.StringVar()
        self._interface_type.set("Serial")
        self._interface_option = tk.OptionMenu(self._window, self._interface_type, *["Serial", "Network"])
        self._interface_option.grid(column=3, row=row, sticky="w", padx=5, pady=5)

        # Ping Command Widgets
        row += 1
        self._cmd_buttons["ping_btn"] = tk.Button(self._window, text="Ping", command=self.ping_cmd)
        self._cmd_buttons["ping_btn"].grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._ping_success_var = tk.StringVar()
        self._ping_success_var.set("N/A")
        self._ping_success_txt = tk.Entry(self._window, textvariable=self._ping_success_var, width=30)
        self._ping_success_txt.grid(column=2, row=row, sticky="w", padx=5, pady=5)
        self._ping_success_txt.configure(state="readonly")

        # Software Version Widgets
        row += 1
        self._cmd_buttons["get_sw_ver_btn"] = tk.Button(self._window, text="Read Sw Version",
                                                        command=self.get_sw_ver_cmd)
        self._cmd_buttons["get_sw_ver_btn"].grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._sw_ver_var = tk.StringVar()
        self._sw_ver_var.set("N/A")
        self._sw_ver_txt = tk.Entry(self._window, textvariable=self._sw_ver_var, width=30)
        self._sw_ver_txt.grid(column=2, row=row, sticky="w", padx=5, pady=5)
        self._sw_ver_txt.configure(state="readonly")

        # Unit Information Widgets
        row += 1
        self._cmd_buttons["get_unit_info_btn"] = tk.Button(self._window, text="Read Unit Info",
                                                           command=self.get_unit_info_cmd)
        self._cmd_buttons["get_unit_info_btn"].grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._cmd_buttons["set_unit_info_btn"] = tk.Button(self._window, text="Set Unit Info",
                                                           command=self.set_unit_info_cmd)
        self._cmd_buttons["set_unit_info_btn"].grid(column=1, row=row+1, sticky="w", padx=5, pady=5)

        self._unit_info_str_var = []
        self._unit_info_txt_entry = []
        self._unit_info_label = []

        for i in range(0, len(self._UNIT_INFO_LABELS)):
            str_var = tk.StringVar()
            str_var.set("N/A")
            self._unit_info_str_var.append(str_var)

            txt_var = tk.Entry(self._window, textvariable=self._unit_info_str_var[i], width=30)
            txt_var.grid(column=2, row=row, sticky="w", padx=5, pady=5)
            self._unit_info_txt_entry.append(txt_var)

            lbl_var = tk.Label(self._window, text=self._UNIT_INFO_LABELS[i]).grid(column=3, row=row, sticky="w",
                                                                                  padx=5, pady=5)
            self._unit_info_label.append(lbl_var)

            row += 1
        row -= 1
        # Set the Status text box read only
        self._unit_info_txt_entry[0].configure(state="readonly")

        # BIT Information Widgets
        row += 1
        self._cmd_buttons["get_bit_info_btn"] = tk.Button(self._window, text="Read BIT Info",
                                                          command=self.get_bit_info_cmd)
        self._cmd_buttons["get_bit_info_btn"].grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._bit_info_str_var = []
        self._bit_info_txt_entry = []
        self._bit_info_label = []

        for i in range(0, len(self._BIT_INFO_LABELS)):
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

        # Firmware Update Widgets
        row += 1

        self._cmd_buttons["select_fw_file_btn"] = tk.Button(self._window, text="Select Fw File",
                                                            command=self.select_fw_file_cmd)
        self._cmd_buttons["select_fw_file_btn"].grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._fw_file_var = tk.StringVar()
        self._fw_file_var.set("N/A")
        self._fw_file_txt = tk.Entry(self._window, textvariable=self._fw_file_var, width=40)
        self._fw_file_txt.grid(column=2, row=row, sticky="w", padx=5, pady=5)
        self._fw_file_txt.configure(state="readonly")

        row += 1

        self._cmd_buttons["update_fw_btn"] = tk.Button(self._window, text="Start Fw Update", command=self.update_fw_cmd)
        self._cmd_buttons["update_fw_btn"].grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._update_fw_pb = ttk.Progressbar(self._window, orient="horizontal", length=245, mode="determinate")
        self._update_fw_pb.grid(column=2, row=row, sticky="w", padx=5, pady=5)

        row += 1

        self._update_fw_pb_lbl = tk.Label(self._window, text="Progress:")
        self._update_fw_pb_lbl.grid(column=1, row=row, sticky="w", padx=5, pady=5)

        self._update_fw_progress_lbl = tk.Label(self._window, text="0 %")
        self._update_fw_progress_lbl.grid(column=2, row=row, sticky="w", padx=5, pady=5)

        self._fw_update_running = Event()
        self._fw_update_thread = Thread()

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
        self._window.title("{} - {} - {}".format(SW_NO, SW_NAME, SW_VERSION))
        self._window.geometry("625x625")
        if os.path.isfile(self._ICON_FILE):
            self._window.iconbitmap(default=self._ICON_FILE)

    def _create_interface_object(self, response_timeout=SERIAL_DEFAULT_RESPONSE_TIMEOUT):
        """
        Create and return an interface object based on the drop-down selection
        :return: CTS message interface instance, type is dependent on te  selected interface type
        """
        if self._interface_type.get() == "Serial":
            return CtsSerialMsgInterface(self._com_port_var.get(), DEFAULT_BAUD_RATE, response_timeout)
        else:
            return CtsSerialTcpMsgInterface(self._com_port_var.get(), self._TCP_PORT, response_timeout)

    def ping_cmd(self):
        """
        Command handler for the "Ping" button, sends a Ping message to the
        Active Backplane and processes the response reporting success or failure
        :return: N/A
        """
        self._ping_success_var.set("Pinging...")
        self._ping_success_txt.update()

        try:
            with self._create_interface_object() as csi:
                if csi.send_ping():
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
        :return: N/A
        """
        self._sw_ver_var.set("Reading Sw Version...")
        self._sw_ver_txt.update()

        try:
            with self._create_interface_object() as csi:
                result, msg = csi.get_command(CtsMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                              CtsMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)
                if result:
                    payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                        csi.unpack_get_software_version_number_response(msg)
                    self._sw_ver_var.set("{}.{}.{}:{}".format(sw_major, sw_minor, sw_patch, sw_build))
                else:
                    self._sw_ver_var.set("Sw Version Read Fail")
        except Exception as ex:
            self._sw_ver_var.set("{}".format(ex))

    def get_unit_info_cmd(self):
        """
        Command handler for the "Read Unit Info" button, sends a Read Unit Information
        request to the Active Backplane and processes the response reporting the
        received unit information if the request is successful or an appropriate fault message
        :return: N/A
        """
        self._unit_info_str_var[0].set("Reading Unit Info...")
        for i in range(1, len(self._UNIT_INFO_LABELS)):
            self._unit_info_str_var[i].set("N/A")
        self._unit_info_txt_entry[0].update()

        try:
            with self._create_interface_object() as csi:
                result, msg = csi.get_command(CtsMsgId.GET_UNIT_INFO, CtsMsgPayloadLen.GET_UNIT_INFO)
                if result:
                    payload_version, status, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no = \
                        csi.unpack_get_unit_info_response(msg)
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
        :return: N/A
        """
        self._unit_info_str_var[0].set("Setting Unit Info...")
        self._unit_info_txt_entry[0].update()

        try:
            with self._create_interface_object() as csi:
                if csi.send_set_unit_info(self._unit_info_str_var[1].get(),
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
        :return: N/A
        """
        self._bit_info_str_var[0].set("Reading BIT Info...")
        for i in range(1, len(self._BIT_INFO_LABELS)):
            self._bit_info_str_var[i].set("N/A")
        self._bit_info_txt_entry[0].update()

        try:
            with self._create_interface_object() as csi:
                result, msg = csi.get_command(CtsMsgId.GET_BIT_INFO, CtsMsgPayloadLen.GET_BIT_INFO)
                if result:
                    payload_version, source_payload, source_payload_version, flags, voltage_12v_mv, voltage_3v3_mv, \
                        voltage_n3v3_mv, voltage_5v0_mv, voltage_3v3_if_mv, voltage_3v3_tx_mv, voltage_5v0_tx_mv, \
                        micro_temp_deg, ambient_temp_deg = \
                        csi.unpack_get_bit_info_response(msg)
                    self._bit_info_str_var[0].set("0x{}".format(format(flags, '02x')))
                    self._bit_info_str_var[1].set("{}".format(voltage_12v_mv))
                    self._bit_info_str_var[2].set("{}".format(voltage_3v3_mv))
                    self._bit_info_str_var[3].set("{}".format(voltage_n3v3_mv))
                    self._bit_info_str_var[4].set("{}".format(voltage_5v0_mv))
                    self._bit_info_str_var[5].set("{}".format(voltage_3v3_if_mv))
                    self._bit_info_str_var[6].set("{}".format(voltage_3v3_tx_mv))
                    self._bit_info_str_var[7].set("{}".format(voltage_5v0_tx_mv))
                    self._bit_info_str_var[8].set("{}".format(micro_temp_deg))
                    self._bit_info_str_var[9].set("{}".format(ambient_temp_deg))

                else:
                    self._bit_info_str_var[0].set("BIT Info Read Fail")
        except Exception as ex:
            self._bit_info_str_var[0].set("{}".format(ex))

    def select_fw_file_cmd(self):
        """
        Open a file dialog so the user can select the firmware file to upload.
        :return: N/A
        """
        self._fw_file_var.set(filedialog.askopenfilename(filetypes=(("Binary Files", "*.bin"),)))
        self._fw_file_txt.xview_moveto(1)

    def update_fw_cmd(self):
        """
        Update the board firmware.
        :return: N/A
        """
        if not self._fw_update_running.is_set():
            fw_file = self._fw_file_var.get()
            if not os.path.isfile(fw_file):
                messagebox.showerror("Error", "Invalid Fw File: {}".format(fw_file))
                return

            self._cmd_buttons["update_fw_btn"]["text"] = "Stop Fw Update"
            self._fw_update_thread = Thread(target=self._update_fw_thread, args=(fw_file,))
            self._fw_update_thread.start()
            self._fw_update_running.set()
        else:
            self._cmd_buttons["update_fw_btn"]["state"] = tk.DISABLED
            self._cmd_buttons["update_fw_btn"]["text"] = "Stopping Fw Update"
            self._fw_update_running.clear()

    def _set_update_fw_progress(self, pb_percent, label=None):
        """
        Update the firwmare upload progress bar and status text
        :param pb_percent: percentage of upload completed :type Integer
        :param label: status label text to update :type String
        :return: N/A
        """
        self._update_fw_pb["value"] = pb_percent
        self._update_fw_progress_lbl["text"] = "{} %".format(pb_percent) if label is None else label

    def _update_fw_thread(self, fw_file):
        """
        Thread used to execute the firmware update process, using a thread to allow the process to be stopped and
        ensure the main window widgets can be updated to show progress.
        :param fw_file: *.bin firmware update file
        :return: N/A
        """
        # Disable all the other command buttons whilst the firmware update is in progress
        self._interface_option["state"] = tk.DISABLED
        for btn in self._cmd_buttons:
            if btn != "update_fw_btn":
                self._cmd_buttons[btn]["state"] = tk.DISABLED

        self._set_update_fw_progress(0)

        with self._create_interface_object(response_timeout=7.0) as csi:
            with open(fw_file, mode="rb") as f:
                file_transfer_success = True
                file_transfer_cancelled = False
                fw_file_size = os.path.getsize(fw_file)
                fw_file_crc16 = CRCCCITT(version="FFFF").calculate(open(fw_file, mode="rb").read())
                data_chunk_size_bytes = 240
                chunk_no = 1
                total_chunks = int(fw_file_size / data_chunk_size_bytes)

                # Early versions of fw, before v0.0.3-0 delayed sending Ack messages rather than sending Response
                # messages to synchronise the firmware update process, if the start firmware update command fails when
                # waiting for Response messages, try without waiting and rely on Acks for synchrronisation as the
                # firmware on the board may be old.
                wait_resp_msgs = True
                start_fw_update_success = csi.send_start_file_upload(fw_file_size, fw_file_crc16, wait_resp_msgs)

                if not start_fw_update_success:
                    wait_resp_msgs = False
                    start_fw_update_success = csi.send_start_file_upload(fw_file_size, fw_file_crc16, wait_resp_msgs)

                if start_fw_update_success:
                    chunk = bytearray(f.read(data_chunk_size_bytes))
                    while chunk:
                        if csi.send_file_data(chunk, wait_resp_msgs):
                            chunk_no += 1
                            chunk = bytearray(f.read(data_chunk_size_bytes))
                            self._set_update_fw_progress(int((chunk_no / total_chunks) * 100))
                        else:
                            file_transfer_success = False
                            break

                        if not self._fw_update_running.is_set():
                            file_transfer_cancelled = True
                            break
                else:
                    file_transfer_success = False

            if file_transfer_success and not file_transfer_cancelled:
                cmd_success, resp = csi.verify_file_crc(fw_file_crc16)

                if cmd_success:
                    payload_version, test_msg_type, test_msg_version, file_type, crc_valid, file_crc = \
                        csi.unpack_verify_file_crc_response(resp)
                    self._set_update_fw_progress(100, "Complete - File CRC {}: 0x{:04X}"
                                                      "".format("Valid" if crc_valid else "Invalid", fw_file_crc16))
                    csi.send_relaunch()
                    file_transfer_success = True
                else:
                    file_transfer_success = False

        if not file_transfer_success and not file_transfer_cancelled:
            self._set_update_fw_progress(100, "Failed!")

        if file_transfer_cancelled:
            self._set_update_fw_progress(100, "Cancelled")

        # Re-enable all the command buttons
        self._interface_option["state"] = tk.NORMAL
        for btn in self._cmd_buttons:
            self._cmd_buttons[btn]["state"] = tk.NORMAL

        self._cmd_buttons["update_fw_btn"]["state"] = tk.ACTIVE
        self._cmd_buttons["update_fw_btn"]["text"] = "Start Fw Update"
        self._fw_update_running.clear()


# -----------------------------------------------------------------------------
# FUNCTIONS#
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine, creates the GUI object and runs it
    :return: None
    """
    the_gui = CtsTestGui()
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
