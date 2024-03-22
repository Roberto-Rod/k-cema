#!/usr/bin/env python3
"""
VISA spectrum analyser drivers class for Keysight Nxxxx devices.
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

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from spectrum_analyser import VisaSpectrumAnalyser, DbPerDiv

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "Keysight Technologies", "model": "N9342CN"}
]

GET_MARKER_FREQ_CMD = ":CALC:MARK1:X?"
GET_MARKER_POWER_CMD = ":CALC:MARK1:Y?"

DB_DIV_MAP = {
    DbPerDiv.DB_1.name: "DIV1",
    DbPerDiv.DB_2.name: "DIV2",
    DbPerDiv.DB_5.name: "DIV5",
    DbPerDiv.DB_10.name: "DIV10"
}

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class SpectrumAnalyserKeysightN9342CN(VisaSpectrumAnalyser):
    MANUFACTURER = "Keysight Technologies"
    MODEL = "N9342CN"

    def __init__(self, resource_name):
        """
        Class constructor
        :param resource_name: VISA resource name for the piece of TE :type String
        """
        super().__init__(resource_name)

    def device_specific_initialisation(self):
        """
        Concrete class implementation of device specific initialisation, sets capability parameters based on model type.
        :return: True if successful, else False
        """
        ret_val = False
        idn_dict = self.ieee4882_idn_query()

        # Check we haven't got an empty Dictionary
        if len(idn_dict) != 0:
            if idn_dict.get("manufacturer", "") == self.MANUFACTURER and idn_dict.get("model", "") == self.MODEL:
                self.MIN_FREQUENCY_HZ = 0.1E6
                self.MAX_FREQUENCY_HZ = 6000.0E6

                ret_val = True
                for cmd in [":INST:SEL SA",
                            ":INIT:CONT 1",
                            ":FREQ:START 10.00 MHz",
                            ":FREQ:STOP 1550.00 MHz",
                            ":BAND:RES:AUTO ON",
                            ":BAND:VID:AUTO ON",
                            ":POW:ATT:AUTO ON",
                            ":DISP:WIND:TRAC:Y:RLEV 20dBm",
                            ":FORM REAL"]:
                    ret_val = self.send_command(cmd) and ret_val
                    ret_val = self.ieee4882_wait_cmd_complete() and ret_val

        return ret_val

    def set_freq_hz(self, freq_hz):
        """
        Set the spectrum analyser's centre frequency with Hz resolution.
        :param freq_hz: required centre frequency in Hz :type Integer, Float or String
        """
        if self.send_command(":FREQ:CENT {:.1f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_freq_hz(self):
        """
        Get the spectrum analyser's centre frequency with Hz resolution.
        :return centre frequency with Hz resolution :type Float
        """
        return float(self.send_query(":FREQ:CENT?").strip())

    def set_start_freq_hz(self, freq_hz):
        """
        Set the spectrum analyser's start frequency with Hz resolution.
        :param freq_hz: required start frequency in Hz :type Integer, Float or String
        """
        if self.send_command(":FREQ:START {:.1f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def set_stop_freq_hz(self, freq_hz):
        """
        Set the spectrum analyser's stop frequency with Hz resolution.
        :param freq_hz: required stop frequency in Hz :type Integer, Float or String
        """
        if self.send_command(":FREQ:STOP {:.1f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def set_span_hz(self, span_hz):
        """
        Set the spectrum analyser's frequency span with Hz resolution.
        :param span_hz: required frequency span in Hz :type Integer, Float or String
        """
        if self.send_command(":FREQ:SPAN {:.1f} HZ".format(span_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_span_hz(self):
        """
        Get the spectrum analyser's frequency span with Hz resolution.
        :return frequency span with Hz resolution :type Float
        """
        return float(self.send_query(":FREQ:SPAN?").strip())

    def set_res_bw_hz(self, res_bw_hz):
        """
        Set the spectrum analyser's resolution bandwidth with Hz resolution.
        :param res_bw_hz: required resolution bandwidth in Hz :type Integer, Float or String
        """
        if self.send_command(":BAND:RES {:.1f} HZ".format(res_bw_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_res_bw_hz(self):
        """
        Get the spectrum analyser's resolution bandwidthwith Hz resolution.
        :return resolution bandwidth with Hz resolution :type Float
        """
        return float(self.send_query(":BAND:RES?").strip())

    def set_ref_level_dbm(self, ref_level_dbm):
        """
        Set the spectrum analyser's reference level with dBm resolution.
        :param ref_level_dbm: required reference level in dBm :type Integer, Float or String
        """
        if self.send_command(":DISP:WIND:TRAC:Y:RLEV {:.1f} DBM".format(ref_level_dbm)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_ref_level_dbm(self):
        """
        Get the spectrum analyser's reference level with dBm resolution.
        :return reference level in dBm :type Float
        """
        return float(self.send_query(":DISP:WIND:TRAC:Y:RLEV?").strip())

    def set_db_per_div(self, db_per_div):
        """
        Set the spectrum analyser's vertical scale (dB/div).
        :param db_per_div: enumerated DbPerDiv value :type DbPerDiv
        """
        if type(db_per_div) is not DbPerDiv:
            raise TypeError("db_per_div must be type DbPerDiv")

        if self.send_command(":DISP:WIND:TRAC:Y:PDIV {}".format(DB_DIV_MAP[db_per_div.name])):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_db_per_div(self):
        """
        Get the spectrum analyser's vertical scale (dB/div).
        :return enumerated DbPerDiv value :type DbPerDiv
        """
        resp = self.send_query(":DISP:WIND:TRAC:Y:PDIV?").strip()

        def get_key(val):
            for key, value in DB_DIV_MAP.items():
                if val == value:
                    return key

        the_key = get_key(resp)
        return DbPerDiv[the_key]

    def set_cont_trigger(self, cont_trigger):
        """
        Enable/disable the spectrum analyser's continuous trigger.
        :param cont_trigger: True to enable continuous trigger, False to disable :type Boolean
        """
        if self.send_command(":INIT:CONT {}".format("1" if cont_trigger else "0")):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_cont_trigger(self):
        """
        Get the spectrum analyser's continuous trigger state.
        :return True if continuous trigger enabled, False if disabled :type Boolean
        """
        return True if "1" in self.send_query(":INIT:CONT?").strip() else False

    def get_peak(self):
        """
        Get the peak marker reading.

        Executes marker->peak and returns the marker frequency and power readings.
        :return: [0] freq_hz :type Integer
                 [1] power_dbm :type Float
        """
        freq_hz = 0.0
        power_dbm = -255.0

        if self.marker_find_peak():
            freq_hz = float(self.send_query(GET_MARKER_FREQ_CMD).strip())
            power_dbm = float(self.send_query(GET_MARKER_POWER_CMD).strip())

        return freq_hz, power_dbm

    def get_next_peak(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker frequency and power readings.
        :return: [0] freq_hz :type Integer
                 [1] power_dbm :type Float
        """
        freq_hz = 0.0
        power_dbm = -255.0

        if self.marker_find_peak_next():
            freq_hz = float(self.send_query(GET_MARKER_FREQ_CMD).strip())
            power_dbm = float(self.send_query(GET_MARKER_POWER_CMD).strip())

        return freq_hz, power_dbm

    def get_peak_power_dbm(self):
        """
        Get the peak marker reading.
        Executes marker->peak and returns the marker power reading.
        :return: power_dbm :type Float
        """
        power_dbm = -255.0

        if self.marker_find_peak():
            power_dbm = float(self.send_query(GET_MARKER_POWER_CMD).strip())

        return power_dbm

    def get_next_peak_power_dbm(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker power reading.
        :return: power_dbm :type Float
        """
        power_dbm = -255.0

        if self.marker_find_peak_next():
            power_dbm = float(self.send_query(GET_MARKER_POWER_CMD).strip())

        return power_dbm

    def get_peak_freq_hz(self):
        """
        Get the peak marker reading.
        Executes marker->peak and returns the marker frequency reading.
        :return: freq_hz :type Integer
        """
        freq_hz = 0.0

        if self.marker_find_peak():
            freq_hz = float(self.send_query(GET_MARKER_FREQ_CMD).strip())

        return freq_hz

    def get_next_peak_freq_hz(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker frequency reading.
        :return: freq_hz :type Integer
        """
        freq_hz = 0.0

        if self.marker_find_peak():
            freq_hz = float(self.send_query(GET_MARKER_FREQ_CMD).strip())

        return freq_hz

    def marker_find_peak(self):
        """
        Trigger a sweep and then set marker 1 to the peak.
        :return: True if successful, else False
        """
        ret_val = True

        for cmd in [":INIT:IMM", ":CALC:MARK:PEAK:SEAR:MODE MAX", ":CALC:MARK1:MAX"]:
            ret_val = self.send_command(cmd) and ret_val
            ret_val = self.ieee4882_wait_cmd_complete() and ret_val

        return ret_val

    def marker_find_peak_next(self):
        """
        Send the next peak command marker search command.
        :return: True if successful, else False
        """
        if self.send_command(":CALC:MARK1:MAX:NEXT"):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
