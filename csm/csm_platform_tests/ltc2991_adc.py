#!/usr/bin/env python3
"""
Module for accessing an Analog Devices LTC2991 I2C bus ADC.
Relies on the I2C module that uses I2C tools to access the I2C bus.
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
import time

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from i2c import I2C

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
DEBUG = False


class LTC2991ADCChannel(Enum):
    CHANNEL_1 = 0xA
    CHANNEL_2 = 0xC
    CHANNEL_3 = 0xE
    CHANNEL_4 = 0x10
    CHANNEL_5 = 0x12
    CHANNEL_6 = 0x14
    CHANNEL_7 = 0x16
    CHANNEL_8 = 0x18
    VCC = 0x1C


# KT-000-0140-00 LTC2991 ADC information
LTC2991_I2C_BUS = 1
LTC2991_I2C_ADDRESS = 0x48
LTC2991_CHANNEL_INFO = [
    (LTC2991ADCChannel.CHANNEL_1, 3.7, "+VBAT_ZER"),
    (LTC2991ADCChannel.CHANNEL_2, 3.7, "+3V3_ZER_BUF"),
    (LTC2991ADCChannel.CHANNEL_3, 1.0, "+3V0_ZER_PROC"),
    (LTC2991ADCChannel.CHANNEL_4, 1.0, "+3V0_ZER_FPGA"),
    (LTC2991ADCChannel.CHANNEL_5, 1.0, "+2V5_ZER"),
    (LTC2991ADCChannel.CHANNEL_6, 1.0, "+2V5_SOM"),
    (LTC2991ADCChannel.CHANNEL_7, 1.0, "+1V2_ZER_FPGA"),
    (LTC2991ADCChannel.CHANNEL_8, 3.7, "+4V2_ZER")
]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class LTC2991ADC:
    LTC2991_CHANNEL_EN_REG_ADDR	= 0x01
    LTC2991_V1V2V3V4_CTRL_REG_ADDR = 0x06
    LTC2991_V5V6V7V8_CTRL_REG_ADDR = 0x07
    LTC2991_CONTROL_REG_ADDR  = 0x08
    LTC2991_V1_REG_ADDR = 0x0A
    LTC2991_V2_REG_ADDR = 0x0C
    LTC2991_V3_REG_ADDR = 0x0E
    LTC2991_V4_REG_ADDR	= 0x10
    LTC2991_V5_REG_ADDR	= 0x12
    LTC2991_V6_REG_ADDR	= 0x14
    LTC2991_V7_REG_ADDR	= 0x16
    LTC2991_V8_REG_ADDR	= 0x18
    LTC2991_INT_TEMP_REG_ADDR = 0x1A
    LTC2991_VCC_REG_ADDR = 0x1C

    LTC2991_CHANNEL_EN_REG_VAL = 0xF8       # V1-V8 enabled; internal temperature/VCC enabled
    LTC2991_V1V2V3V4_CTRL_REG_VAL = 0x00    # all channels single-ended voltage; filter disabled
    LTC2991_V5V6V7V8_CTR_REG_VAL = 0x00     # all channels single-ended voltage; filter disabled
    LTC2991_CONTROL_REG_VAL = 0x10          # PWM disabled; repeated acquisition; internal voltage filter disabled;
                                            # Degrees C temp.
    LTC2991_VOLT_SCALE_FACTOR = 305.18E-3
    LTC2991_VOLT_VALID_BIT = 0x8000
    LTC2991_VOLT_SIGN_BIT = 0x4000
    LTC2991_VOLT_BITS = 0x3FFF
    LTC2991_VCC_OFFSET_MV = 2500

    LTC2991_TEMP_SCALE_FACTOR = 0.0625
    LTC2991_TEMP_VALID_BIT = 0x8000
    LTC2991_TEMP_SIGN_BIT = 0x1000
    LTC2991_TEMP_BITS = 0x0FFF

    MAX_MEASUREMENT_TIME_ALL_CHANNELS_S = 0.277

    def __init__(self, bus, i2c_address):
        """
        Class constructor, creates an I2C object used to access the device, the I2C object uses I2C Tools to interact
        with the bus.  Initialises the ADC with default settings and starts continuous conversions so the ADC can be
        read at any point.
        :param bus: I2C bus that the device resides on :type: Integer
        :param i2c_address: 7-bit I2C bus address : type: Integer
        :return: None
        """
        self.i2c = I2C(bus, i2c_address)
        # Disable all channels
        self.i2c.write_byte(self.LTC2991_CHANNEL_EN_REG_ADDR, 0x00)
        time.sleep(self.MAX_MEASUREMENT_TIME_ALL_CHANNELS_S)
        # Configure ADC channels as single-ended
        self.i2c.write_byte(self.LTC2991_V1V2V3V4_CTRL_REG_ADDR, self.LTC2991_V1V2V3V4_CTRL_REG_VAL)
        self.i2c.write_byte(self.LTC2991_V5V6V7V8_CTRL_REG_ADDR, self.LTC2991_V5V6V7V8_CTR_REG_VAL)
        # Set continuous conversion, internal temperature deg C
        self.i2c.write_byte(self.LTC2991_CONTROL_REG_ADDR, self.LTC2991_CONTROL_REG_VAL)
        # Enable all channels
        self.i2c.write_byte(self.LTC2991_CHANNEL_EN_REG_ADDR, self.LTC2991_CHANNEL_EN_REG_VAL)
        # Allow all channels to be measured before allowing readings
        time.sleep(self.MAX_MEASUREMENT_TIME_ALL_CHANNELS_S)

    def get_channel_mv(self, channel):
        """
        Reads the specified ADC channel and returns the voltage with mV resolution
        :param channel: channel to read :type LTC2991ADCChannel
        :return: voltage in mV, -1 for invalid reading :type integer
        """
        if channel not in LTC2991ADCChannel:
            raise RuntimeError("Invalid channel '{}' must be of type LTC2991ADCChannel".format(channel))

        ret_val = -1
        reg_val = int(self.i2c.read_word(channel.value))
        # Swap the bytes and shift the data into the right place
        reg_val = (((reg_val >> 8) & 0xFF) | ((reg_val << 8) & 0xFF00))

        if reg_val & self.LTC2991_VOLT_VALID_BIT:
            if reg_val & self.LTC2991_VOLT_SIGN_BIT:
                # Negative voltage
                ret_val = int((float(reg_val & self.LTC2991_VOLT_BITS) - float(self.LTC2991_VOLT_SIGN_BIT)) *
                              self.LTC2991_VOLT_SCALE_FACTOR)
            else:
                # Positive voltage
                ret_val = int(float(reg_val & self.LTC2991_VOLT_BITS) * self.LTC2991_VOLT_SCALE_FACTOR)

            if channel == LTC2991ADCChannel.VCC:
                ret_val += self.LTC2991_VCC_OFFSET_MV

        return ret_val

    def read_temp(self):
        """
        Reads the LTC2991 temperature value, returned temperature has resolution of 1 deg C
        :return: channel temperature with 1 deg C resolution, -255.0 for invalid reading :type Float
        """
        ret_val = -255.0
        reg_val = int(self.i2c.read_word(self.LTC2991_INT_TEMP_REG_ADDR))
        # Swap the bytes and shift the data into the right place
        reg_val = (((reg_val >> 8) & 0xFF) | ((reg_val << 8) & 0xFF00))

        if reg_val & self.LTC2991_TEMP_VALID_BIT:
            if reg_val & self.LTC2991_TEMP_SIGN_BIT:
                # Negative temperature
                ret_val = int((float(reg_val & self.LTC2991_TEMP_BITS) - float(self.LTC2991_TEMP_SIGN_BIT)) *
                              self.LTC2991_TEMP_SCALE_FACTOR)
            else:
                # Positive temperature
                ret_val = float(reg_val & self.LTC2991_TEMP_BITS) * self.LTC2991_TEMP_SCALE_FACTOR

        return ret_val


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(argv):
    """
    Creates an instance of LTC2991ADC using default settings then reads and displays the voltages and temperature.
    :param argv: system command line options and arguments - currently not used
    :return: N/A
    """
    adc = LTC2991ADC(LTC2991_I2C_BUS, LTC2991_I2C_ADDRESS)
    for channel, scaling_factor, name in LTC2991_CHANNEL_INFO:
        log.info("{:<6} : {} Voltage (mv)".format(int(adc.get_channel_mv(channel) * scaling_factor), name))
    log.info("{:<6.2f} : Temperature (deg C)".format(adc.read_temp()))


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
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(sys.argv[1:])
