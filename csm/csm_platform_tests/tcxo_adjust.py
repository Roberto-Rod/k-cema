#!/usr/bin/env python3
"""
Utility class to adjust the 10 MHz TCXO output frequency.  Relies on the GPS 1PPS counter,
therefore a GPS antenna must be connected to the KT-000-0140-00 when using this class.
Assumes that trim DAC is Microchip MCP4725
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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
import time

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from dev_mem import *
from i2c import I2C

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
TCXO_COUNT_REGISTER_ADDRESS = 0x4000D000
TCXO_COUNT_REGISTER_GPS_1PPS_BIT = 0x80000000
TCXO_COUNT_TARGET = 10000000
DAC_I2C_BUS_ADDRESS = 0x60
DAC_I2C_BUS = 0
DAC_MAX_VALUE = 4095

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class TcxoAdjust:
    def __init__(self, tcxo_count_register_address=TCXO_COUNT_REGISTER_ADDRESS,
                 dac_i2c_bus=DAC_I2C_BUS, dac_i2c_bus_address=DAC_I2C_BUS_ADDRESS):
        """
        Class constructor
        :param tcxo_count_register_address: memory address of TCXO count register
        :param dac_i2c_bus: number of I2C bus for DAC access
        :param dac_i2c_bus_address: I2C bus address for DAC
        """
        self.tcxo_count_register_address = tcxo_count_register_address
        self._dac_i2c_bus = dac_i2c_bus
        self._dac_i2c_bus_address = dac_i2c_bus_address
        self.i2c = I2C(dac_i2c_bus, dac_i2c_bus_address)

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "TcxoAdjust({!r}, {!r}, {!r})".format(self.tcxo_count_register_address,
                                                     self._dac_i2c_bus,
                                                     self._dac_i2c_bus_address)

    def get_tcxo_count(self):
        """
        Read and return the TCXO count, checks if the GPS 1PPS input is present
        :return: [0] True if GPS 1PPS is present else False :type: boolean
                 [1] TCXO count in Hz :type: integer
        """
        # Read the TCXO counter register twice with a 1-second pause between readings,
        # register bit 31 toggles on the rising-edge of the GPS 1PPS signal
        val1 = DevMem.read(self.tcxo_count_register_address)
        val2 = 0
        timeout = time.perf_counter() + 2.0
        while time.perf_counter() < timeout:
            val2 = DevMem.read(self.tcxo_count_register_address)
            if val2 != val1:
                break

        # Check GPS 1PPS input bit has toggled
        if (val1 & TCXO_COUNT_REGISTER_GPS_1PPS_BIT) ^ (val2 & TCXO_COUNT_REGISTER_GPS_1PPS_BIT):
            gps_pps_present = True
            log.debug("GPS present")
        else:
            gps_pps_present = False
            log.debug("GPS NOT present: x{:X}; x{:X}".format(val1, val2))

        tcxo_count = val2 & ~TCXO_COUNT_REGISTER_GPS_1PPS_BIT
        log.debug("tcxo_count: {}".format(tcxo_count))

        return gps_pps_present, tcxo_count

    def set_trim_dac(self, value, set_eeprom=False):
        """
        Assumes that the I2C transactions are successful and an exception will be raised halting
        script execution if something goes wrong
        :param value: value to be writte to DAC
        :param set_eeprom: write value to DAC EEPROM if True :type: boolean
        :return: No return value
        """
        if not isinstance(value, int):
            raise ValueError("value must be an integer!")

        data = []
        if set_eeprom:
            data.append(0x60)
            data.append((value >> 4) & 0xFF)
            data.append((value << 4) & 0xF0)
        else:
            data.append((value >> 8) & 0x0F)
            data.append(value & 0xFF)

        self.i2c.write_block(data)

    def trim_dac(self, target, set_eeprom=False):
        """
        Trim the TCXO to the target TCXO count value, the DAC is adjusted using the binary search algorithm
        until the required value is achieved.
        :param target: target TCXO count in Hz :type: integer
        :param set_eeprom: write trim value for target to DAC EEPROM if True :type: boolean
        :return: True if TCXO trimmed to target value else False :type: boolean
        """
        if not isinstance(target, int) or target == 0:
            raise ValueError("target must be non-zero integer!")

        trim_range_lower = 0
        trim_range_upper = DAC_MAX_VALUE + 1

        while True:
            # Set the trim value
            trim_value = int(trim_range_lower + ((trim_range_upper - trim_range_lower) / 2))
            self.set_trim_dac(trim_value)
            time.sleep(1)
            # Check if the trim value gives the required TCXO count, break loop if we've found value or GPS unavailable
            gps_pps_present, tcxo_count = self.get_tcxo_count()
            if not gps_pps_present or tcxo_count == target:
                break
            # Modify the trim range and go again
            if tcxo_count > target:
                trim_range_upper = trim_value
            else:
                trim_range_lower = trim_value
            log.debug("tcxo_count: {}\ttrim_value: {}\ttrim_range_upper: {}\ttrim_range_lower: {}"
                      "".format(tcxo_count, trim_value, trim_range_upper, trim_range_lower))
            # Exhausted all values so break
            if trim_range_upper == 0 or trim_range_lower == DAC_MAX_VALUE:
                break

        if tcxo_count == target and set_eeprom:
            self.set_trim_dac(trim_value, set_eeprom=True)
            log.debug("Set trim DAC EEPROM value to: {}".format(trim_value))
        elif tcxo_count == target:
            log.debug("Trim successful: {}".format(trim_value))
        else:
            log.debug("Failed to trim DAC")

        return True if tcxo_count == target and gps_pps_present else False


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    ta = TcxoAdjust()
    log.info("{} - SoM 1PPS & TCXO Input Test".format("PASS" if ta.trim_dac(TCXO_COUNT_TARGET) else "FAIL"))
    # ta.trim_dac(TCXO_COUNT_TARGET / 2)  # Unachievable LOW target
    # ta.trim_dac(TCXO_COUNT_TARGET * 2)  # Unachievable HIGH target


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run main() routine
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main()
