#!/usr/bin/env python3
"""
Built-in test module, tests the SoM Xilinx Zynq XADC channel BIT data
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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
import argparse
from enum import Enum
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from dev_mem import DevMem
from xadc import *

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
class CsmAdcChannel(Enum):
    XADC_CHAN_3V3 = 0
    XADC_CHAN_3V0_GPS = 6
    XADC_CHAN_12V = 15
    XADC_CHAN_1V0_ETH = 12
    XADC_CHAN_2V5_ETH = 13


class CsmPowerGood(Enum):
    PGD_BAT_5V = 9
    PGD_GBE = 8


class BuiltInTest:
    _REG_GPIO_0_ADDRESS = 0x4000A000

    pgood_name = {CsmPowerGood.PGD_BAT_5V: "PGOOD_+5V_BAT", CsmPowerGood.PGD_GBE: "PGOOD_GBE"}

    chan_name = {CsmAdcChannel.XADC_CHAN_3V3: "BIT.+3V3", CsmAdcChannel.XADC_CHAN_3V0_GPS: "BIT.+3V0_GPS",
                 CsmAdcChannel.XADC_CHAN_12V: "BIT.+12V", CsmAdcChannel.XADC_CHAN_1V0_ETH: "BIT.+1V0_ETH",
                 CsmAdcChannel.XADC_CHAN_2V5_ETH: "BIT.+2V5_ETH"}

    chan_nom = {CsmAdcChannel.XADC_CHAN_3V3: 3.3, CsmAdcChannel.XADC_CHAN_3V0_GPS: 3.0,
                CsmAdcChannel.XADC_CHAN_12V: 12.0, CsmAdcChannel.XADC_CHAN_1V0_ETH: 1.0,
                CsmAdcChannel.XADC_CHAN_2V5_ETH: 2.5}

    chan_units = {CsmAdcChannel.XADC_CHAN_3V3: "V", CsmAdcChannel.XADC_CHAN_3V0_GPS: "V",
                  CsmAdcChannel.XADC_CHAN_12V: "V", CsmAdcChannel.XADC_CHAN_1V0_ETH: "V",
                  CsmAdcChannel.XADC_CHAN_2V5_ETH: "V"}

    _adc_scaling = {CsmAdcChannel.XADC_CHAN_3V3: 1249 / 249, CsmAdcChannel.XADC_CHAN_3V0_GPS: 1249 / 249,
                    CsmAdcChannel.XADC_CHAN_12V: 219 / 14, CsmAdcChannel.XADC_CHAN_1V0_ETH: 1249 / 249,
                    CsmAdcChannel.XADC_CHAN_2V5_ETH: 1249 / 249}

    _adc_offset = {CsmAdcChannel.XADC_CHAN_3V3: 0, CsmAdcChannel.XADC_CHAN_3V0_GPS: 0, CsmAdcChannel.XADC_CHAN_12V: 0,
                   CsmAdcChannel.XADC_CHAN_1V0_ETH: 0, CsmAdcChannel.XADC_CHAN_2V5_ETH: 0}

    def __init__(self):
        self.xadc = XADC()
        
    def power_good(self, rail):
        """
        Check if a Power Good (PGOOD) signal is asserted
        :param rail: PGOOD rail to check :type CSMPowerGood
        :return: True if Power Good signal is asserted, else False
        """
        if not isinstance(rail, CsmPowerGood):
            raise TypeError("Rail must be an instance of CSMPowerGood Enum")
        mask = 1 << rail.value
        val = DevMem.read(self._REG_GPIO_0_ADDRESS)
        return val & mask != 0

    def value(self, channel):
        if not isinstance(channel, CsmAdcChannel):
            raise TypeError("channel must be an instance of CSMADCChannel Enum")
        val = self.xadc.get_external_voltage(channel.value)

        return (val * self._adc_scaling[channel]) + self._adc_offset[channel]


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(channel):
    bit = BuiltInTest()

    if hasattr(CsmPowerGood, channel):
        log.info("INFO - {}: {}".format(bit.pgood_name[getattr(CsmPowerGood, channel)],
                                        bit.power_good(getattr(CsmPowerGood, channel))))
    elif hasattr(CsmAdcChannel, channel):
        log.info("INFO - {} {:.2f} {}".format(bit.chan_name[getattr(CsmAdcChannel, channel)],
                                              bit.value(getattr(CsmAdcChannel, channel)),
                                              bit.chan_units[getattr(CsmAdcChannel, channel)]))
    else:
        log.info("INFO - Invalid channel!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Call runtime procedure and print requested parameter value
    """
    parser = argparse.ArgumentParser(description="CSM UART Test")
    parser.add_argument("-c", "--channel", required=True, dest="channel", action="store",
                        help="Channel to read and return: XADC_CHAN_3V3; XADC_CHAN_3V0_GPS; XADC_CHAN_12V = 15;"
                             "XADC_CHAN_1V0_ETH;  XADC_CHAN_2V5_ETH; PGD_BAT_5V; PGD_GBE")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args.channel)
