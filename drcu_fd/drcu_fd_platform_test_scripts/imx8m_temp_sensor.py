#!/usr/bin/env python3
"""
Module for accessing the IMX8M temperature sensor.
Relies on the dev_mem module to read/write SoC registers.
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
from enum import Enum
import logging
import sys

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from dev_mem import DevMem

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class Imx8mSensor(Enum):
    """ Utility enumeration to define temperature channels """
    MAIN_ANAMIX = 0
    REMOTE_ARM_CORE = 1


class Imx8mTempSensor:
    IMX8M_TMU_TER_REG_ADDRESS = 0x3026_0000
    IMX8M_TMU_TER_REG_ENABLE_BIT = 0x8000_0000
    IMX8M_TMU_TER_REG_ADC_POWER_DOWN_BIT = 0x4000_0000
    IMX8M_TMU_TRITSR_REG_ADDRESS = 0x3026_0020
    IMX8M_TMU_TRITSR_REG_MAIN_TEMP_READY_BIT = 0x4000_0000
    IMX8M_TMU_TRITSR_REG_MAIN_TEMP_RSHIFT = 0
    IMX8M_TMU_TRITSR_REG_REMOTE_TEMP_READY_BIT = 0x8000_0000
    IMX8M_TMU_TRITSR_REG_REMOTE_TEMP_RSHIFT = 16
    IMX8M_TMU_TRITSR_REG_MAIN_TEMP_MASK = 0xFF
    IMX8M_TMU_TRITSR_REG_MAIN_SIGN_BIT = 0x80

    def __init__(self):
        """ Class constructor """
        pass

    def power_down_temp_sensor_adc(self, power_down):
        """
        Powers the temperature sensor ADC on and off
        :param power_down: True to power down ADC, False to power up :type Boolean
        :return: N/A
        """
        if power_down:
            DevMem.set(self.IMX8M_TMU_TER_REG_ADDRESS, self.IMX8M_TMU_TER_REG_ADC_POWER_DOWN_BIT)
        else:
            DevMem.clear(self.IMX8M_TMU_TER_REG_ADDRESS, self.IMX8M_TMU_TER_REG_ADC_POWER_DOWN_BIT)

    def read_temp(self, sensor):
        """
        Reads the specified temperature sensor, returned temperature has resolution of 1 deg C
        :param sensor: one of Imx8mSensor enumerated values :type Imx8mSensor
        :return: channel temperature with 1 deg C resolution, -128 for invalid temperature
        """
        if sensor not in Imx8mSensor:
            raise RuntimeError("Invalid temperature sensor - {}".format(sensor))

        ret_val = -128
        ready_bit = self.IMX8M_TMU_TRITSR_REG_MAIN_TEMP_READY_BIT if sensor == Imx8mSensor.MAIN_ANAMIX \
            else self.IMX8M_TMU_TRITSR_REG_REMOTE_TEMP_READY_BIT
        rshift = self.IMX8M_TMU_TRITSR_REG_MAIN_TEMP_RSHIFT if sensor == Imx8mSensor.MAIN_ANAMIX \
            else self.IMX8M_TMU_TRITSR_REG_REMOTE_TEMP_RSHIFT

        reg_data = DevMem.read(self.IMX8M_TMU_TRITSR_REG_ADDRESS)

        if reg_data & ready_bit:
            temp = (reg_data >> rshift) & self.IMX8M_TMU_TRITSR_REG_MAIN_TEMP_MASK
            ret_val = temp if temp < 128 else temp - 256

        return ret_val


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(argv):
    """
    Creates an instance of AD7415TempSensor on I2C bus 1 then reads and displays the temperature.
    :param argv: system command line options and arguments - currently not used
    :return: N/A
    """
    ts = Imx8mTempSensor()
    ts.power_down_temp_sensor_adc(False)
    log.info("{:<4}\t: Main (ANAMIX) )Temperature (deg C)".format(ts.read_temp(Imx8mSensor.MAIN_ANAMIX)))
    log.info("{:<4}\t: Remote (ARM Core) Temperature (deg C)".format(ts.read_temp(Imx8mSensor.REMOTE_ARM_CORE)))
    # ts.power_down_temp_sensor_adc(True)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Creates an instance of the class and reads temperatures from device 
    """
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    main(sys.argv[1:])
