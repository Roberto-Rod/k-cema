#!/usr/bin/env python3
"""
Built-in test reporting module, prints BIT information for all KT-000-0199-00
Fill-Device motherboard BIT sensors connected to the SoC.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
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
from built_in_test_0199 import BitChannel, BuiltInTest
from ad7415_temp_sensor import AD7415TempSensor
from imx8m_temp_sensor import Imx8mTempSensor, Imx8mSensor

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
    b = BuiltInTest()
    for ch in BitChannel:
        log.info("{:<6.2f}\t: {} ({})".format(b.value(ch), b.chan_name[ch], b.chan_units[ch]))

    ts = AD7415TempSensor(1)
    log.info("{:<6.2f}\t: AD7415 Temperature (deg C)".format(ts.read_temp()))

    imx = Imx8mTempSensor()
    imx.power_down_temp_sensor_adc(False)
    log.info("{:<6.2f}\t: Main (ANAMIX) Temperature (deg C)".format(imx.read_temp(Imx8mSensor.MAIN_ANAMIX)))
    log.info("{:<6.2f}\t: Remote (ARM Core) Temperature (deg C)".format(imx.read_temp(Imx8mSensor.REMOTE_ARM_CORE)))
    imx.power_down_temp_sensor_adc(True)


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
