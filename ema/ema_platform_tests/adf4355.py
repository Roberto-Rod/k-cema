#!/usr/bin/env python3
from devmem import DevMem
from pl_spi import PLSPI
from time import sleep

import argparse


class ADF4355:
    GPIO_SYNTH_CTRL_ADDR = 0x40015000
    SPI_MASTER_BASE_ADDR = 0x4001B000
    SYNTH_MUXOUT_MASK = 0x80000000
    SYNTH_PDBRF_MASK = 0x00000008
    SYNTH_EN_MASK = 0x00000004

    def __init__(self):
        self.spi = PLSPI(self.SPI_MASTER_BASE_ADDR)

    def enable_device(self):
        DevMem.set(self.GPIO_SYNTH_CTRL_ADDR, self.SYNTH_EN_MASK)

    def disable_device(self):
        DevMem.clear(self.GPIO_SYNTH_CTRL_ADDR, self.SYNTH_EN_MASK)

    def mute_rf(self):
        DevMem.clear(self.GPIO_SYNTH_CTRL_ADDR, self.SYNTH_PDBRF_MASK)

    def unmute_rf(self):
        DevMem.set(self.GPIO_SYNTH_CTRL_ADDR, self.SYNTH_PDBRF_MASK)

    def write_reg(self, addr, data):
        # Write 28-bit data, 4-bit address
        self.spi.write_data(((data & 0x0FFFFFFF) << 4) | (addr & 0xF), 32)

    def write(self, value):
        # Write 32-bit word
        self.spi.write_data(value, 32)

    def set_synth_5000_megahertz(self):
        # PFD = 125 MHz, INT = 40
        # VCO 5 GHz, output divide by 1 (reg val 0)
        self.set_synth(40, 0)

    def set_synth_3000_megahertz(self):
        # PFD = 125 MHz, INT = 48
        # VCO 6 GHz, output divide by 2 (reg val 1)
        self.set_synth(48, 1)

    def set_synth(self, int_val, div_val):
        self.mute_rf()
        self.write(0x0000041c)
        self.write(0x0061300b)
        self.write(0x00c0273a)
        self.write(0x1b1a7cc9)
        self.write(0x102d0428)
        self.write(0x10000067)
        self.write(0x750188f6 | ((div_val << 21) & 0x00E00000))
        self.write(0x00800025)
        self.write(0x30040b84)
        self.write(0x00000003)
        self.write(0x00000012)
        self.write(0x00000001)
        sleep(0.02)
        r0_full_pfd = (int_val << 4) & 0xFF0
        r0_half_pfd = (int_val << 5) & 0xFF0
        self.write(0x00200000 | r0_half_pfd)
        self.write(0x18020b84)
        self.write(0x00000012)
        self.write(0x00000001)
        self.write(r0_full_pfd)
        sleep(0.02)
        self.unmute_rf()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control the ADF4355 Synth")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("-i", "--initialise",
                        help="Initialise the ADF4355 Synth",
                        action="store_true")
    action.add_argument("-d", "--disable",
                        help="Disable the ADF4355 Synth",
                        action="store_true")
    args = parser.parse_args()

    synth = ADF4355()

    if args.initialise:
        synth.enable_device()
        synth.set_synth_5000_megahertz()
        print("Synth initialised")

    if args.disable:
        synth.mute_rf()
        synth.disable_device()
        print("Synth disabled")
