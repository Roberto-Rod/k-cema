#!/usr/bin/env python3
"""
VISA power meter driver class for Keysight U2000 series devices.
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
import pyvisa

# Our own imports ---------------------------------------------------
from power_meter import VisaPowerMeter

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "Agilent Technologies", "model": "U2001A"}
]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class PowerMeterU2001A(VisaPowerMeter):
    MANUFACTURER = "Agilent Technologies"
    MODEL = "U2001A"

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
                self.MIN_FREQUENCY_HZ = 10.0E6
                self.MAX_FREQUENCY_HZ = 6000.0E6
                self.MIN_INPUT_POWER_DBM = -60.0
                self.MAX_INPUT_POWER_DBM = -20.0

                ret_val = True
                for cmd in ["INIT:CONT OFF",            # Set to triggered mode
                            "SENS:DET:FUNC AVER"        # Set to averaging mode
                            "SENS:FREQ 1000000000 HZ"   # Default to 1 GHz
                            "SENS:AVER:COUN:AUTO OFF"   # Turn-off auto-averaging
                            "SENS:AVER:COUN 16"         # Average over 16 readings
                            "SENS:AVER:STAT ON"         # Turn averaging on
                            "SENS:CORR:GAIN2 0.00"      # Set offset correction to 0.00 dB
                            "CORR:GAIN2:STAT OFF"        # Turn offset correction off
                            "FORMAT ASCII"              # ASCII numerical format
                            ]:
                    ret_val = self.send_command(cmd) and ret_val
                    ret_val = self.ieee4882_wait_cmd_complete() and ret_val

        return ret_val

    def zero_sensor(self):
        """
        Zero calibrate the sensor.
        :return: True if successful, else False
        """
        ret_val = False
        if self.send_command("CAL:ZERO:TYPE INT"):
            if self.ieee4882_wait_cmd_complete():
                # The zero calibration routine may take up to 20-seconds
                default_timeout = self.visa_te.timeout
                self.visa_te.timeout = 20000    # ms
                ret_val = int(self.send_query("CAL:ALL?".strip())) == 0
                self.visa_te.timeout = default_timeout
        return ret_val

    def set_freq_hz(self, freq_hz):
        """
        Set the frequency with Hz resolution used for frequency dependent offset-corrections.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        :return: True if successful, else False
        """
        if self.send_command("SENS:FREQ {:.1f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_freq_hz(self):
        """
        Return the current frequency with Hz resolution used for frequency dependent offset-corrections.
        :return frequency with Hz resolution :type Float
        """
        return float(self.send_query("SENS:FREQ?").strip())

    def get_power_dbm(self):
        """
        Return the measured power with dBm resolution.
        :return power_dbm: power in dBm :type Float
        """
        reading = self.send_query("READ?").strip()
        if reading != "":
            ret_val = float(reading)
        else:
            ret_val = self.MIN_INPUT_POWER_DBM
        return ret_val

    def set_offset(self, offset_db):
        """python
        Enable/disable the RF output
        :param offset_db: required offset in dB :type Float
        :return: True if successful, else False
        """
        if self.send_command("SENS:CORR:GAIN2 {:.2f}".format(offset_db)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_offset(self):
        """
        Return the RF output enable state
        :return current offset in dB :type Float
        """
        return float(self.send_query("SENS:CORR:GAIN2?").strip())


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ Look for a connected U2001A Power Meter, connect to it and test the commands """
    resource_manager = pyvisa.ResourceManager()
    for power_meter_type in [PowerMeterU2001A]:
        for resource in resource_manager.list_resources():
            p = power_meter_type(resource)
            if p.find_and_initialise():
                print("Zero Sensor: ", end="", flush=True)
                if p.zero_sensor():
                    print("OK")
                else:
                    print("ERROR")
                    exit()

                print("Set frequency Hz to 100000000: ", end="", flush=True)
                if p.set_freq_hz(100000000):
                    print("OK")
                else:
                    print("ERROR")
                    exit()

                f_hz = p.get_freq_hz()
                print("Get frequency: {} Hz: ".format(f_hz), end="", flush=True)
                if int(f_hz) == 100000000:
                    print("OK")
                else:
                    print("ERROR")
                    exit()

                print("Get Power dBm: {}".format(p.get_power_dbm()))

                print("Set correction offset to 10.57 dB: ", end="", flush=True)
                if p.set_offset(10.57):
                    print("OK")
                else:
                    print("ERROR")
                    exit()

                os_db = p.get_offset()
                print("Get correction offset {:.2f} dB: ".format(os_db), end="", flush=True)
                if os_db == 10.57:
                    print("OK")
                else:
                    print("ERROR")
                    exit()

                print("U2001A All Tests Passed: OK")
