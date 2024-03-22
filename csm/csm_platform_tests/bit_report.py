#!/usr/bin/env python3
"""
Built-in test reporting module, prints BIT information for all KT-000-0140-00
BIT sensors connected to the SoM.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from built_in_test import CsmAdcChannel, CsmPowerGood, BuiltInTest
from ad7415_temp_sensor import AD7415TempSensor
from ltc2991_adc import LTC2991ADC, LTC2991_CHANNEL_INFO, LTC2991_I2C_BUS, LTC2991_I2C_ADDRESS
from tmp442_temp_sensor import Tmp442TempSensor, TempChannels
from xadc import XADC, XADCInternalVoltage

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


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    # Monitored power rails
    log.info("")
    log.info("Power Rails:")

    a = AD7415TempSensor(1)
    b = BuiltInTest()
    t = Tmp442TempSensor(1)
    t.init_device()
    x = XADC()
    l = LTC2991ADC(LTC2991_I2C_BUS, LTC2991_I2C_ADDRESS)

    for ch in XADCInternalVoltage:
        log.info("{:<6.2f}\tV SoC {}".format(x.get_internal_voltage(ch), str(ch)))
    for ch in CsmAdcChannel:
        log.info("{:<6.2f}\t{} {}".format(b.value(ch), b.chan_units[ch], b.chan_name[ch]))
    for channel, scaling_factor, name in LTC2991_CHANNEL_INFO:
        log.info("{:<6.2f}\tV {}".format(l.get_channel_mv(channel) * scaling_factor / 1000.0, name))
    for ch in CsmPowerGood:
        log.info("{:<6}\t{}".format(b.power_good(ch), b.pgood_name[ch]))

    # Temperatures...
    log.info("")
    log.info("Temperatures:")
    log.info("{:<6.2f}\tdeg C AD7415 Ambient".format(a.read_temp()))
    log.info("{:<6.2f}\tdeg C TMP442 Ambient".format(t.read_temp(TempChannels.INTERNAL)))
    log.info("{:<6.2f}\tdeg C Eth Switch".format(t.read_temp(TempChannels.REMOTE1)))
    log.info("{:<6.2f}\tdeg C Eth Phy".format(t.read_temp(TempChannels.REMOTE2)))
    log.info("{:<6.2f}\tdeg C SoC".format(x.get_internal_temperature()))
    log.info("{:<6.2f}\tdeg C LTC2991".format(l.read_temp()))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Call runtime procedure 
    """

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main()
