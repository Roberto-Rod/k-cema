#!/usr/bin/env python3
from dev_mem import *

from enum import Enum

class XADCInternalVoltage(Enum):
    VCCINT = 0x204
    VCCAUX = 0x208
    VCCBRAM = 0x218
    VCCPINT = 0x234
    VCCPAUX = 0x238
    VCCO_DDR = 0x23C
    
class XADC:
    REG_XADC_BASE = 0x4000E000
    REG_XADC_CHAN_TEMPERATURE = REG_XADC_BASE + 0x200
    REG_XADC_CHAN_EXT_0 = REG_XADC_BASE + 0x240
    REG_XADC_SEQ_0 = REG_XADC_BASE + 0x320
    REG_XADC_SEQ_1 = REG_XADC_BASE + 0x324
    REG_XADC_NR_EXT_CHANNELS = 16

    SEQ_0_DEFAULT = 0x77E1
    SEQ_1_DEFAULT = 0xCFFF

    # Internal temperature scaling:
    # ((ADC code (16-bit) * 503.975) / 65536) -273.15

    # Unipolar input scaling:
    # ADC code (16-bit) / 65536

    # Internal voltage scaling:
    # (ADC code (16-bit) / 65536) * 3

    def __init__(self):
        DevMem.write(self.REG_XADC_SEQ_0, self.SEQ_0_DEFAULT)
        DevMem.write(self.REG_XADC_SEQ_1, self.SEQ_1_DEFAULT)

    def get_internal_temperature(self):
        reading = DevMem.read(self.REG_XADC_CHAN_TEMPERATURE) & 0xFFFF
        return ((reading * 503.975) / 65536) - 273.15

    def get_internal_voltage(self, internal_rail):
        if not isinstance(internal_rail, XADCInternalVoltage):
            raise TypeError("internal_rail must be an instance of XADCInternalVoltage Enum")
        reading = DevMem.read(self.REG_XADC_BASE + internal_rail.value) & 0xFFFF
        return (reading * 3) / 65536

    def get_external_voltage(self, channel_number):
        if channel_number >= self.REG_XADC_NR_EXT_CHANNELS:
            raise ValueError("channel_number must be <= {}".format(self.REG_XADC_NR_EXT_CHANNELS - 1))
        reading = DevMem.read(self.REG_XADC_CHAN_EXT_0 + (channel_number * 4)) & 0xFFFF
        return reading / 65536


if __name__ == "__main__":
    xadc = XADC()
    print("Read XADC:")    
    print("  Internal temperature: {:.1f} degC".format(xadc.get_internal_temperature()))
    print("  Internal VCCINT: {:.2f} V".format(xadc.get_internal_voltage(XADCInternalVoltage.VCCINT)))
    print("  Internal VCCAUX: {:.2f} V".format(xadc.get_internal_voltage(XADCInternalVoltage.VCCAUX)))
    print("  Internal VCCBRAM: {:.2f} V".format(xadc.get_internal_voltage(XADCInternalVoltage.VCCBRAM)))
    print("  Internal VCCPINT: {:.2f} V".format(xadc.get_internal_voltage(XADCInternalVoltage.VCCPINT)))
    print("  Internal VCCPAUX: {:.2f} V".format(xadc.get_internal_voltage(XADCInternalVoltage.VCCPAUX)))
    print("  Internal VCCO_DDR: {:.2f} V".format(xadc.get_internal_voltage(XADCInternalVoltage.VCCO_DDR)))
    for chan in range(0, xadc.REG_XADC_NR_EXT_CHANNELS):
        print("  External channel {}: {:.2f} V".format(chan, xadc.get_external_voltage(chan)))

