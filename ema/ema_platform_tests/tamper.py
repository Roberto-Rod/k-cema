#!/usr/bin/env python3
"""
This module includes classes and functions to configure the KT-000-0134/5-00
anti-tamper sensors.  The boards have 2x identical sensors connected to ST
M41ST87W tamper ICs:
Channel 1 - mechanical case switch; normally open/tamper low
Channel 2 - mechanical case switch; normally open/tamper low

The mechanical case switch includes a capacitor on the Tamper Input pin that
must be charged when the channel is armed.  This is achieved by enabling the
channel in the normally open/tamper high configuration whilst the switch is
closed.  Note, the capacitor charging procedure will cause a tamper event so
care must be taken to prevent tamper actions being triggered:
- the TCLR bit is cleared so that the M41ST87W RAM is NOT cleared
- the TIE bit is cleared to stop the Tamper Irq to the processing system
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-a/--arm Arm both tamper channels
-d/--disarm Disarm both tamper channels
-i/--inactive Set both tamper channels to inactive state, mimics BootBlocker tamper_reset_inactive()
-s/--status Print the status of both tamper channels
-r/--rtc_ticking Check if the RTC is ticking and print result message
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
from enum import Enum
import logging
from time import sleep

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from i2c import I2C

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
class TamperChannel(Enum):
    """
    Utility enumeration to define tamper channels
    """
    LIGHT_SENSOR = 0
    MICROSWITCH = 1


class Tamper:
    """
    The main Tamper class, used to arm/disarm channels and check device status
    """
    I2C_BUS = 0
    CHIP_ADDRESS = 0x68
    SECONDS_ADDRESS = 0x01
    FLAG_REG_ADDRESS = 0x0F
    TAMPER1_REG_ADDRESS = 0x14
    TAMPER2_REG_ADDRESS = 0x15
    TAMPER_CLEAR_RAM_BIT = 0x01
    TAMPER_ENABLED_BIT = 0x80
    CHARGE_CAPACITOR_DELAY_S = 3
    CHARGE_CAPACITOR_TAMPER_BITS = 0x94     # Tamper Enabled; Normally Open/Tamper High; 1 MOhm pull-up
    ARM_TAMPER_CH1_BITS = 0xE4          # Tamper Enabled; Tamper Irq Enabled; Normally Open/Tamper Low; 1 MOhm pull-up
    ARM_TAMPER_CH2_BITS = 0xE4          # Tamper Enabled; Tamper Irq Enabled; Normally Open/Tamper Low; 1 MOhm pull-up
    INACTIVE_TAMPER_CH1_BITS = 0x25         # Normally Open/Tamper Low; Clear RAM on Tamper; 1 MOhm pull-up
    INACTIVE_TAMPER_CH2_BITS = 0x25         # Normally Open/Tamper Low; Clear RAM on Tamper; 1 MOhm pull-up

    def __init__(self):
        """
        Class constructor
        """
        self.i2c = I2C(self.I2C_BUS, self.CHIP_ADDRESS)

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "Tamper(I2C bus: {}; I2C bus addr: {})".format(self.I2C_BUS, self.CHIP_ADDRESS)

    def reset(self):
        """
        Disable both tamper channels
        """
        # Clear all bits in TAMPER1 and TAMPER2 registers
        self.i2c.write_word(self.TAMPER1_REG_ADDRESS, 0x0000)

    def inactive(self):
        """
        Mimics the BootBlocker tamper_reset_inactive() function, configures tamper channels
        but leaves them disabled, clears flags and interrupts
        """
        # Ensure the Oscillator Fail bit is clear
        self.i2c.write_byte(self.FLAG_REG_ADDRESS, 0x00)

        # Set TAMPERx registers
        self.i2c.write_byte(self.TAMPER1_REG_ADDRESS, self.INACTIVE_TAMPER_CH1_BITS)
        self.i2c.write_byte(self.TAMPER2_REG_ADDRESS, self.INACTIVE_TAMPER_CH2_BITS)

        # Read the FLAGS register to ensure the irq signal is cleared
        self.i2c.read_byte(self.FLAG_REG_ADDRESS)

    def arm(self, clear_ram=False):
        """
        Enable both tamper channels, charge capacitor before enabling case switch channel
        :param clear_ram: if True set the bit to clear device RAM :type: Boolean
        """
        self.i2c.write_byte(self.TAMPER1_REG_ADDRESS, self.CHARGE_CAPACITOR_TAMPER_BITS)
        sleep(self.CHARGE_CAPACITOR_DELAY_S)

        self.i2c.write_word(self.TAMPER1_REG_ADDRESS, 0x0000)

        if clear_ram:
            tamper1_reg = self.ARM_TAMPER_CH1_BITS | self.TAMPER_CLEAR_RAM_BIT
            tamper2_reg = self.ARM_TAMPER_CH2_BITS | self.TAMPER_CLEAR_RAM_BIT
        else:
            tamper1_reg = self.ARM_TAMPER_CH1_BITS
            tamper2_reg = self.ARM_TAMPER_CH2_BITS

        self.i2c.write_byte(self.TAMPER1_REG_ADDRESS, tamper1_reg)
        self.i2c.write_byte(self.TAMPER2_REG_ADDRESS, tamper2_reg)

        sleep(1)

    def is_armed(self, channel):
        """
        Test if a tamper channel is armed
        :param channel: the Tamper Channel to test :type: TamperChannel
        :return: True if the channel is armed, else False
        """
        if not isinstance(channel, TamperChannel):
            raise TypeError("channel must be an instance of TamperChannel(Enum)")

        if channel == TamperChannel.MICROSWITCH:
            tamper_reg = self.i2c.read_byte(self.TAMPER1_REG_ADDRESS)
        else:
            tamper_reg = self.i2c.read_byte(self.TAMPER2_REG_ADDRESS)

        log.debug(hex(tamper_reg))
        if (tamper_reg & self.TAMPER_ENABLED_BIT) != 0:
            return True
        else:
            return False

    def is_tampered(self, channel):
        """
        Test if a tamper channel is tampered by reading the FLAGS register.
        If the Tamper Irq signal is asserted reading the FLAGS register will clear it.
        :param channel: the Tamper Channel to test :type: TamperChannel
        :return: True if the channel is tampered, else False
        """
        if not isinstance(channel, TamperChannel):
            raise TypeError("channel must be an instance of TamperChannel(Enum)")

        flags = self.i2c.read_byte(self.FLAG_REG_ADDRESS)
        mask = 1 << channel.value

        log.debug(hex(flags))
        if (flags & mask) != 0:
            return True
        else:
            return False

    def is_ticking(self):
        """
        Test if the M41ST87W RTC is ticking
        :return: True if the RTC is ticking, else False
        """
        t1 = self.i2c.read_byte(self.SECONDS_ADDRESS)
        sleep(2)
        t2 = self.i2c.read_byte(self.SECONDS_ADDRESS)
        return t1 != t2

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Execute functions based on command line options
    """
    parser = argparse.ArgumentParser(description="Tamper Device\n"
                                                 "'Error: Read failed' or 'Error: Write failed'"
                                                 "will appear in the stdout if the I2C bus transfer fails.\n"
                                                 "Options are processed in the order specified below.")
    parser.add_argument("-i", "--inactive", dest="inactive", action="store_true",
                        help="Set both tamper channels to inactive state, mimics BootBlocker "
                             "tamper_reset_inactive()")
    parser.add_argument("-d", "--disarm", dest="disarm", action="store_true",
                        help="Disarm both tamper channels")
    parser.add_argument("-a", "--arm", dest="arm", action="store_true",
                        help="Arm both tamper channels")
    parser.add_argument("-s", "--status", dest="status", action="store_true",
                        help="Print the status of both tamper channels")
    parser.add_argument("-r", "--rtc_ticking", dest="rtc_ticking", action="store_true",
                        help="Check if the RTC is ticking and print result message")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO)

    t = Tamper()

    if args.inactive:
        log.info("Setting both tamper channels to inactive")
        t.inactive()

    if args.disarm:
        log.info("Disarming both tamper channels")
        t.reset()

    if args.arm:
        log.info("Arming both tamper channels")
        t.arm(clear_ram=True)

    if args.status:
        log.info("Tamper channel status:")
        for chan in TamperChannel:
            log.info("Channel {} is armed: {}".format(chan, t.is_armed(chan)))
            log.info("Channel {} is tampered: {}".format(chan, t.is_tampered(chan)))

    if args.rtc_ticking:
        log.info("RTC is ticking: {}".format(t.is_ticking()))
