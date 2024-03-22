#!/usr/bin/env python3
from devmem import *
from xadc import *
from enum import Enum


class NTMADCChannel(Enum):
    XADC_CHAN_TX_DAC_3V3A = 0          # LB only
    XADC_CHAN_NEG_1V8 = 1              # LB only
    XADC_CHAN_DC_IN = 2                # All bands
    XADC_CHAN_TX_DAC_3V3D = 3          # LB only
    XADC_CHAN_3V6 = 4                  # All bands (not available in Rev A LB board)
    XADC_CHAN_7V3 = 5                  # LB only
    XADC_CHAN_BASE_TEMPERATURE = 6     # All bands
    XADC_CHAN_IF_ADC_3V3A_XCVR_2V1 = 7 # LB: IF ADC +3V3A, MB/HB: XCVR +2V1
    XADC_CHAN_DDS_CLK_3V3 = 8          # All bands
    XADC_CHAN_TX_5V0 = 9               # LB only (not available in Rev A LB board)
    XADC_CHAN_TX_DAC_5V0 = 10          # LB only
    XADC_CHAN_5V5_5V3 = 11             # LB: +5V5, MB/HB: +5V3
    XADC_CHAN_CURRENT_IN = 14          # All bands (not available in Rev A LB board)
    XADC_CHAN_3V3 = 15                 # All bands

class NTMPowerGood(Enum):
    PGD_ADC_2V5A = 31                  # LB only
    PGD_ADC_1V25A = 30                 # LB only
    PGD_ADC_1V25D = 29                 # LB only
    PGD_MGT_CLK = 28                   # All bands
    PGD_MGT_1V0 = 27                   # All bands
    PGD_MGT_1V2 = 26                   # All bands
    PGD_ETH_1V2 = 25                   # All bands
    PGD_TX_DAC = 24                    # LB only
    PGD_XCVR_1V3 = 23                  # MB/HB only

class BuiltInTest:
    REG_SUPPLY_CONTROL = 0x40014000

    pgood_name = {}
    pgood_name[NTMPowerGood.PGD_ADC_2V5A] = "PGD_ADC_2V5A"
    pgood_name[NTMPowerGood.PGD_ADC_1V25A] = "PGD_ADC_1V25A"
    pgood_name[NTMPowerGood.PGD_ADC_1V25D] = "PGD_ADC_1V25D"
    pgood_name[NTMPowerGood.PGD_MGT_CLK] = "PGD_MGT_CLK"
    pgood_name[NTMPowerGood.PGD_MGT_1V0] = "PGD_MGT_1V0"
    pgood_name[NTMPowerGood.PGD_MGT_1V2] = "PGD_ADC_1V25A"
    pgood_name[NTMPowerGood.PGD_ETH_1V2] = "PGD_ETH_1V2"
    pgood_name[NTMPowerGood.PGD_TX_DAC] = "PGD_TX_DAC"
    pgood_name[NTMPowerGood.PGD_XCVR_1V3] = "PGD_XCVR_1V3"

    chan_name = {}
    chan_name[NTMADCChannel.XADC_CHAN_TX_DAC_3V3A] = "XADC_CHAN_TX_DAC_3V3A"
    chan_name[NTMADCChannel.XADC_CHAN_NEG_1V8] = "XADC_CHAN_NEG_1V8"
    chan_name[NTMADCChannel.XADC_CHAN_DC_IN] = "XADC_CHAN_DC_IN"
    chan_name[NTMADCChannel.XADC_CHAN_TX_DAC_3V3D] = "XADC_CHAN_TX_DAC_3V3D"
    chan_name[NTMADCChannel.XADC_CHAN_3V6] = "XADC_CHAN_3V6"
    chan_name[NTMADCChannel.XADC_CHAN_7V3] = "XADC_CHAN_7V3"
    chan_name[NTMADCChannel.XADC_CHAN_BASE_TEMPERATURE] = "XADC_CHAN_BASE_TEMPERATURE"
    chan_name[NTMADCChannel.XADC_CHAN_IF_ADC_3V3A_XCVR_2V1] = "XADC_CHAN_IF_ADC_3V3A_XCVR_2V1"
    chan_name[NTMADCChannel.XADC_CHAN_DDS_CLK_3V3] = "XADC_CHAN_DDS_CLK_3V3"
    chan_name[NTMADCChannel.XADC_CHAN_TX_5V0] = "XADC_CHAN_TX_5V0"
    chan_name[NTMADCChannel.XADC_CHAN_TX_DAC_5V0] = "XADC_CHAN_TX_DAC_5V0"
    chan_name[NTMADCChannel.XADC_CHAN_5V5_5V3] = "XADC_CHAN_5V5_5V3"
    chan_name[NTMADCChannel.XADC_CHAN_CURRENT_IN] = "XADC_CHAN_CURRENT_IN"
    chan_name[NTMADCChannel.XADC_CHAN_3V3] = "XADC_CHAN_3V3"

    chan_units = {}
    chan_units[NTMADCChannel.XADC_CHAN_TX_DAC_3V3A] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_NEG_1V8] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_DC_IN] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_TX_DAC_3V3D] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_3V6] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_7V3] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_BASE_TEMPERATURE] = " degC"
    chan_units[NTMADCChannel.XADC_CHAN_IF_ADC_3V3A_XCVR_2V1] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_DDS_CLK_3V3] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_TX_5V0] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_TX_DAC_5V0] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_5V5_5V3] = "V"
    chan_units[NTMADCChannel.XADC_CHAN_CURRENT_IN] = "A"
    chan_units[NTMADCChannel.XADC_CHAN_3V3] = "V"

    adc_scaling = {}
    adc_scaling[NTMADCChannel.XADC_CHAN_TX_DAC_3V3A] = 1249 / 249
    adc_scaling[NTMADCChannel.XADC_CHAN_NEG_1V8] = 176 / 25
    adc_scaling[NTMADCChannel.XADC_CHAN_DC_IN] = 4606 / 121
    adc_scaling[NTMADCChannel.XADC_CHAN_TX_DAC_3V3D] = 1249 / 249
    adc_scaling[NTMADCChannel.XADC_CHAN_3V6] = 1249 / 249
    adc_scaling[NTMADCChannel.XADC_CHAN_7V3] = 1121 / 121
    adc_scaling[NTMADCChannel.XADC_CHAN_BASE_TEMPERATURE] = 200
    adc_scaling[NTMADCChannel.XADC_CHAN_IF_ADC_3V3A_XCVR_2V1] = 1249 / 249
    adc_scaling[NTMADCChannel.XADC_CHAN_DDS_CLK_3V3] = 1249 / 249
    adc_scaling[NTMADCChannel.XADC_CHAN_TX_5V0] = 589 / 89
    adc_scaling[NTMADCChannel.XADC_CHAN_TX_DAC_5V0] = 589 / 89
    adc_scaling[NTMADCChannel.XADC_CHAN_5V5_5V3] = 589 / 89
    adc_scaling[NTMADCChannel.XADC_CHAN_CURRENT_IN] = 100 / 55
    adc_scaling[NTMADCChannel.XADC_CHAN_3V3] = 1249 / 249

    adc_offset = {}
    adc_offset[NTMADCChannel.XADC_CHAN_TX_DAC_3V3A] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_NEG_1V8] = -151 / 20
    adc_offset[NTMADCChannel.XADC_CHAN_DC_IN] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_TX_DAC_3V3D] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_3V6] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_7V3] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_BASE_TEMPERATURE] = -50
    adc_offset[NTMADCChannel.XADC_CHAN_IF_ADC_3V3A_XCVR_2V1] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_DDS_CLK_3V3] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_TX_5V0] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_TX_DAC_5V0] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_5V5_5V3] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_CURRENT_IN] = 0
    adc_offset[NTMADCChannel.XADC_CHAN_3V3] = 0

    def __init__(self):
        self.xadc = XADC()

    def power_good(self, rail):
        if not isinstance(rail, NTMPowerGood):
            raise TypeError("rail must be an instance of NTMPowerGood Enum")
        mask = 1 << rail.value
        val = DevMem.read(self.REG_SUPPLY_CONTROL)
        return val & mask != 0

    def value(self, channel):
        if not isinstance(channel, NTMADCChannel):
            raise TypeError("channel must be an instance of NTMADCChannel Enum")
        val = self.xadc.get_external_voltage(channel.value)
        return (val * self.adc_scaling[channel]) + self.adc_offset[channel]


if __name__ == "__main__":
    bit = BuiltInTest()
    print("Built In Test readings:")
    for pgd in NTMPowerGood:
        print("  {}: {}".format(bit.pgood_name[pgd], bit.power_good(pgd)))

    for chan in NTMADCChannel:
        print("  {}: {:.2f} {}".format(bit.chan_name[chan], bit.value(chan), bit.chan_units[chan]))

