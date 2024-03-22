#!/usr/bin/env python3
"""
This module includes classes and functions to configure the KT-000-0140-00
anti-tamper sensors.  The board has the following sensors connected to an ST
M41ST87W tamper ICs:
Channel 1 - mechanical case switch; normally closed/tamper high
Channel 2 - light sensor; normally open/tamper low
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
-b/--bit Perform unit-level Built-In Test
-d/--disarm Disarm both tamper channels
-i/--inactive Set both tamper channels to inactive state, mimics BootBlocker tamper_reset_inactive()
-r/--rtc_ticking Check if the RTC is ticking and print result message
-s/--status Print the status of both tamper channels
-t/--time_rtc Read the RTC time is ticking and print result message
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
    I2C_BUS = 1
    NO_RETRIES = 2
    CHIP_ADDRESS = 0x68
    SECONDS_ADDRESS = 0x01
    MINUTES_ADDRESS = 0x02
    HOURS_ADDRESS = 0x03
    ALARM_HOUR_ADDRESS = 0x0C
    FLAG_REG_ADDRESS = 0x0F
    TAMPER1_REG_ADDRESS = 0x14
    TAMPER2_REG_ADDRESS = 0x15
    TAMPER_CLEAR_RAM_BIT = 0x01
    TAMPER_ENABLED_BIT = 0x80
    ARM_TAMPER_CH1_BITS = 0xD4      # Tamper Enabled; Tamper Irq Enabled; Normally Closed/Tamper High; 1 MOhm pull-up
    ARM_TAMPER_CH2_BITS = 0xE4      # Tamper Enabled; Tamper Irq Enabled; Normally Open/Tamper Low
    INACTIVE_TAMPER_CH1_BITS = 0x15     # Normally Closed/Tamper High; Clear RAM on Tamper; 1 MOhm pull-up
    INACTIVE_TAMPER_CH2_BITS = 0x25     # Normally Open/Tamper Low; Clear RAM on Tamper

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
        for _ in range(0, self.NO_RETRIES):
            self.i2c.write_byte(self.FLAG_REG_ADDRESS, 0x00)

        # Set TAMPERx registers
        for _ in range(0, self.NO_RETRIES):
            self.i2c.write_byte(self.TAMPER1_REG_ADDRESS, self.INACTIVE_TAMPER_CH1_BITS)
            tamper_reg = self.i2c.read_byte(self.TAMPER1_REG_ADDRESS)
            if tamper_reg == self.INACTIVE_TAMPER_CH1_BITS:
                break

        for _ in range(0, self.NO_RETRIES):
            self.i2c.write_byte(self.TAMPER2_REG_ADDRESS, self.INACTIVE_TAMPER_CH2_BITS)
            tamper_reg = self.i2c.read_byte(self.TAMPER1_REG_ADDRESS)
            if tamper_reg == self.INACTIVE_TAMPER_CH2_BITS:
                break

        # Read the FLAGS register to ensure the irq signal is cleared
        for _ in range(0, self.NO_RETRIES):
            self.i2c.read_byte(self.FLAG_REG_ADDRESS)

        sleep(1)

    def arm(self, clear_ram=False):
        """
        Enable both tamper channels
        :param clear_ram: if True set the bit to clear device RAM :type: Boolean
        """
        if clear_ram:
            tamper1_reg = self.ARM_TAMPER_CH1_BITS | self.TAMPER_CLEAR_RAM_BIT
            tamper2_reg = self.ARM_TAMPER_CH2_BITS | self.TAMPER_CLEAR_RAM_BIT
        else:
            tamper1_reg = self.ARM_TAMPER_CH1_BITS
            tamper2_reg = self.ARM_TAMPER_CH2_BITS

        for _ in range(0, self.NO_RETRIES):
            self.i2c.write_byte(self.TAMPER1_REG_ADDRESS, tamper1_reg)
            tamper_reg = self.i2c.read_byte(self.TAMPER1_REG_ADDRESS)
            if tamper_reg == tamper1_reg:
                break

        for _ in range(0, self.NO_RETRIES):
            self.i2c.write_byte(self.TAMPER2_REG_ADDRESS, tamper2_reg)
            tamper_reg = self.i2c.read_byte(self.TAMPER2_REG_ADDRESS)
            if tamper_reg == tamper2_reg:
                break

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

    def write_reg(self, address, data):
        """
        Write the specified register
        :param address: register address :type Integer
        :param data: register data value: type Integer
        :return: N/A
        """
        self.i2c.write_byte(address, data)

    def read_reg(self, address):
        """
        Write the specified register
        :param address: register address :type Integer
        :return: register data value
        """
        return self.i2c.read_byte(address)


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(inactive, disarm, arm, status, rtc_ticking, time_rtc, bit):
    t = Tamper()

    if inactive:
        log.info("Setting both tamper channels to inactive")
        t.inactive()

    if disarm:
        log.info("Disarming both tamper channels")
        t.reset()

    if arm:
        log.info("Arming both tamper channels")
        t.arm(clear_ram=True)

    if status:
        log.info("Tamper channel status:")
        for channel in TamperChannel:
            log.info("Channel {} is armed: {}".format(channel, t.is_armed(channel)))
            log.info("Channel {} is tampered: {}".format(channel, t.is_tampered(channel)))

    if rtc_ticking:
        log.info("RTC is ticking: {}".format(t.is_ticking()))

    if time_rtc:
        # Write zero to the Alarm Hour register to clear the HT bit and ensure the user RTC registers are being updated
        t.i2c.write_byte(t.ALARM_HOUR_ADDRESS, 0)
        buf = []
        for i in range(0, 8):
            buf.append(t.i2c.read_byte(i))
        log.info("RTC: {}{}:{}{}:{}{}".format((int(buf[t.HOURS_ADDRESS]) & 0x30) >> 4,
                                              int(buf[t.HOURS_ADDRESS]) & 0x0F,
                                              (int(buf[t.MINUTES_ADDRESS]) & 0x70) >> 4,
                                              int(buf[t.MINUTES_ADDRESS]) & 0x0F,
                                              (int(buf[t.SECONDS_ADDRESS]) & 0x70) >> 4,
                                              int(buf[t.SECONDS_ADDRESS]) & 0x0F))
    if bit:
        # Perform a unit-level built-in test, expecting the case switch to be closed to GND and the light sensor
        # driving the tamper input OPEN-CIRCUIT (dark condition) if the the tamper rod is present and the unit
        # is assembled.  Leaves the tamper channels in the INACTIVE state, they will need to be re-ARMED.

        # Case switch test:
        # 1 - Set the Tamper Channel configuration to Normally Open/Tamper Low Configuration, if the tamper rod is
        #     present and the micro-switch is grounded this will trigger a tamper event, don't clear RAM!
        #     Need to test this way as setting the standard Normally Closed to GND/Tamper High configuration will
        #     present a not tampered the state if the micro-switch is open or closed, it is the transition from
        #     closed to open that triggers the tamper.
        reg_val = t.read_reg(t.TAMPER1_REG_ADDRESS)
        reg_val &= (~t.TAMPER_CLEAR_RAM_BIT)
        t.write_reg(t.TAMPER1_REG_ADDRESS, reg_val)
        t.write_reg(t.TAMPER1_REG_ADDRESS, 0xE4)     # Tamper Enabled; Tamper Irq Enabled; Normally Open/Tamper Low

        # 2 - Check the tamper is detected, i.e. the switch is connected to GND
        test_pass = (t.read_reg(t.FLAG_REG_ADDRESS) & (1 << TamperChannel.MICROSWITCH.value)) != 0
        log.info("{} - Micro-switch Test".format("PASS" if test_pass else "FAIL"))

        # Light sensor test:
        # 1- ensure the tamper channel is armed, if there is light on the sensor a tamper will be detected immediately,
        #    don't clear the RAM
        reg_val = t.read_reg(t.TAMPER2_REG_ADDRESS)
        reg_val &= (~t.TAMPER_CLEAR_RAM_BIT)
        t.write_reg(t.TAMPER2_REG_ADDRESS, reg_val)
        t.write_reg(t.TAMPER2_REG_ADDRESS, 0xE4)     # Tamper Enabled; Tamper Irq Enabled; Normally Open/Tamper Low

        # 2 - Check the tamper is NOT detected, i.e. there is no light on the sensor
        test_pass = (t.read_reg(t.FLAG_REG_ADDRESS) & (1 << TamperChannel.LIGHT_SENSOR.value)) == 0
        log.info("{} - Light Sensor Test".format("PASS" if test_pass else "FAIL"))

        # Set the tamper channels back to the inactive state
        t.inactive()


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
    parser.add_argument("-b", "--bit", dest="bit", action="store_true",
                        help="Unit-Level Built-In Test")
    parser.add_argument("-a", "--arm", dest="arm", action="store_true",
                        help="Arm both tamper channels")
    parser.add_argument("-d", "--disarm", dest="disarm", action="store_true",
                        help="Disarm both tamper channels")
    parser.add_argument("-i", "--inactive", dest="inactive", action="store_true",
                        help="Set both tamper channels to inactive state, mimics BootBlocker "
                             "tamper_reset_inactive()")
    parser.add_argument("-s", "--status", dest="status", action="store_true",
                        help="Print the status of both tamper channels")
    parser.add_argument("-r", "--rtc_ticking", dest="rtc_ticking", action="store_true",
                        help="Check if the RTC is ticking and print result message")
    parser.add_argument("-t", "--time_rtc", dest="time_rtc", action="store_true",
                        help="Read the RTC time is ticking and print result message")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(message)s"
    logging.basicConfig(format=fmt, level=logging.DEBUG)

    main(args.inactive, args.disarm, args.arm, args.status, args.rtc_ticking, args.time_rtc, args.bit)
