#!/usr/bin/env python3
from time import sleep

from devmem import *


class PowerSupplies:
    REG_SUPPLY_CONTROL = 0x40014000
    REG_RX_CONTROL = 0x40004000

    # Supplies applicable to LB & MB/HB:
    SUPPLY_TX_EN_MASK = (1 << 7)
    SUPPLY_RX_EN_MASK = (1 << 6)
    SUPPLY_TX_DAC_EN_N_MASK = (1 << 5)
    SUPPLY_IF_ADC_EN_MASK = (1 << 4)
    SUPPLY_3V6_EN_MASK = (1 << 1)

    # Supplies applicable to LB only:
    SUPPLY_7V3_EN_MASK = (1 << 3)
    SUPPLY_5V5_EN_MASK = (1 << 2)
    SUPPLY_NEG_1V8_EN_MASK = (1 << 0)

    # Supplies applicable to MB/HB only:
    SUPPLY_1V3_EN_MASK = (1 << 3)  # same bit as LB 7V3
    SUPPLY_5V3_EN_MASK = (1 << 2)  # same bit as LB 5V5
    SUPPLY_2V1_EN_MASK = (1 << 0)  # same bit as LB NEG_1V8

    RX_IF_ADC_EN_MASK = (1 << 13)

    # Power good:
    PGOOD_TX_DAC = (1 << 24)

    @staticmethod
    def disable_all():
        PowerSupplies.if_adc_en(False)
        PowerSupplies.tx_dac_en(False)
        PowerSupplies.tx_en(False)
        PowerSupplies.rx_en(False)
        PowerSupplies.rail_7v3_en(False)
        PowerSupplies.rail_5v5_en(False)
        PowerSupplies.rail_3v6_en(False)
        PowerSupplies.rail_neg_1v8_en(False)

    @staticmethod
    def tx_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_TX_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_TX_EN_MASK)

    @staticmethod
    def rx_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_RX_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_RX_EN_MASK)

    @staticmethod
    def if_adc_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_RX_CONTROL, PowerSupplies.RX_IF_ADC_EN_MASK)
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_IF_ADC_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_RX_CONTROL, PowerSupplies.RX_IF_ADC_EN_MASK)
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_IF_ADC_EN_MASK)

    @staticmethod
    def tx_dac_en(en=True):
        if en:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_TX_DAC_EN_N_MASK)
        else:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_TX_DAC_EN_N_MASK)

    @staticmethod
    def tx_dac_pgood():
        return (DevMem.read(PowerSupplies.REG_SUPPLY_CONTROL) & PowerSupplies.PGOOD_TX_DAC) != 0

    @staticmethod
    def rail_7v3_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_7V3_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_7V3_EN_MASK)

    @staticmethod
    def rail_5v5_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_5V5_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_5V5_EN_MASK)

    @staticmethod
    def rail_3v6_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_3V6_EN_MASK)
            sleep(0.5)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_3V6_EN_MASK)

    @staticmethod
    def rail_neg_1v8_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_NEG_1V8_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_NEG_1V8_EN_MASK)

    @staticmethod
    def rail_1v3_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_1V3_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_1V3_EN_MASK)

    @staticmethod
    def rail_5v3_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_5V3_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_5V3_EN_MASK)

    @staticmethod
    def rail_2v1_en(en=True):
        if en:
            DevMem.set(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_2V1_EN_MASK)
        else:
            DevMem.clear(PowerSupplies.REG_SUPPLY_CONTROL, PowerSupplies.SUPPLY_2V1_EN_MASK)


if __name__ == "__main__":
    print("This module is not intended to be executed stand-alone")
