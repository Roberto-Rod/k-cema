#!/usr/bin/env python3
"""
Tkinter GUI application to generate K-CEMA BootBlocker command strings
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
import os
import tkinter as tk

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from bootblocker_config import BootBlockerPassword, ConfigDataFlags, BootBlockerConfig

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_VERSION = "V1.0.0"
ICON_FILE = "kirintec_logo.ico"

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class BootBlockerConfigGui:

    def __init__(self):
        self._window = tk.Tk()
        self.initialise_window()

        row = 0

        row += 1
        self._unlock_password_lbl = tk.Label(self._window, text="Unlock Password:").grid(column=0, row=row, sticky="w")

        row += 1
        self._unit_serial_no_lbl = tk.Label(self._window, text="Unit Serial No (8-char max):")
        self._unit_serial_no_lbl.grid(column=0, row=row, sticky="e")
        self._unit_serial_no_txt = tk.Entry(self._window, width=8)
        self._unit_serial_no_txt.grid(column=1, row=row, sticky="w")
        self._unit_serial_no_txt.insert(0, "123456")
        self._unit_serial_no_txt.bind("<Return>", self._unit_serial_no_txt_rtn)

        row += 1
        self._password_lbl = tk.Label(self._window, text="Unlock Cmd:")
        self._password_lbl.grid(column=0, row=row, sticky="e")
        self._password_txt_var = tk.StringVar()
        self._password_txt = tk.Entry(self._window, textvariable=self._password_txt_var, width=12)
        self._password_txt.grid(column=1, row=row, sticky="w")
        self._password_txt.configure(state="readonly")

        self._password_btn = tk.Button(self._window, text="Generate Unlock Cmd", command=self.generate_password_cmd)
        self._password_btn.grid(column=2, row=row, sticky="w")

        self.generate_password_cmd()

        row += 1
        self._config_data_lbl = tk.Label(self._window, text="Configuration Data:").grid(column=0, row=row, sticky="w")
        row += 1
        self._flag_chk = {}
        self._flag_chk_var = {}
        for flag in ConfigDataFlags:
            var = tk.IntVar()
            self._flag_chk[flag.value] = tk.Checkbutton(self._window, text=flag.name, variable=var,
                                                        onvalue=flag.value+1, offvalue=0,
                                                        command=self.generate_config_cmd)
            self._flag_chk[flag.value].grid(column=flag.value // 8, row=row + flag.value % 8, sticky="w")

            if "RESERVED" in flag.name:
                self._flag_chk[flag.value].config(state=tk.DISABLED)

            # Set default state, checked/unchecked
            if flag in BootBlockerConfig.DEFAULT_CONFIG:
                var.set(flag.value+1)
            else:
                var.set(0)
            self._flag_chk_var[flag.value] = var

        row += 8
        self._config_data_cmd_lbl = tk.Label(self._window, text="Set Config Data Cmd:")
        self._config_data_cmd_lbl.grid(column=0, row=row, sticky="e")
        self._config_data_cmd_txt_var = tk.StringVar()
        self._config_data_cmd_txt = tk.Entry(self._window, textvariable=self._config_data_cmd_txt_var, width=40)
        self._config_data_cmd_txt.grid(column=1, row=row, sticky="w")
        self._config_data_cmd_txt.configure(state="readonly")
        self.generate_config_cmd()

    def run(self):
        self._window.mainloop()

    def initialise_window(self):
        """
        Set up the Tkinter window elements
        :return: None
        """
        self._window.title("K-CEMA BootBlocker Config - {}".format(SW_VERSION))
        self._window.geometry("680x340")
        if os.path.isfile(ICON_FILE):
            self._window.iconbitmap(ICON_FILE)

    def _unit_serial_no_txt_rtn(self, event):
        self.generate_password_cmd()

    def generate_password_cmd(self):
        if str.isnumeric(self._unit_serial_no_txt.get()):
            pw = BootBlockerPassword(self._unit_serial_no_txt.get())
            self._password_txt_var.set(pw.get_unlock_command_string())

    def generate_config_cmd(self):
        config = BootBlockerConfig()    # By default all flags are cleared
        for i in range(0, len(self._flag_chk_var)):
            if self._flag_chk_var[i].get() != 0:
                config.set_clear_flag(ConfigDataFlags(self._flag_chk_var[i].get()-1), True)

        self._config_data_cmd_txt_var.set(config.get_write_command_string())


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """
    Main runtime routine
    :return: None
    """
    the_gui = BootBlockerConfigGui()
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
