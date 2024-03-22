#!/usr/bin/env python3
from devmem import *
from time import sleep


class Synth:
    REG_SYNTH_BASE = 0x40080540
    REG_SYNTH_CONTROL = REG_SYNTH_BASE + 0x0
    REG_SYNTH_REGISTERS = REG_SYNTH_BASE + 0x4

    SYNTH_CONTROL_READY_MASK = (1 << 31)
    SYNTH_CONTROL_LOCKED_MASK = (1 << 30)
    SYNTH_CONTROL_MUXOUT_MASK = (1 << 29)
    SYNTH_CONTROL_PDRF_N_MASK = (1 << 1)
    SYNTH_CONTROL_CE_MASK = (1 << 0)

    @staticmethod
    def initialise():
        # Set CE = 1, PDRF_N = 1
        mask = Synth.SYNTH_CONTROL_CE_MASK | Synth.SYNTH_CONTROL_PDRF_N_MASK
        DevMem.set(Synth.REG_SYNTH_CONTROL, mask)

        # Set the synth to output 3240 MHz
        # Register values as per:
        # http://confluence.kirintec.local/display/KEW/ADF4351+Synth+Settings
        Synth.write_reg(0x00580005)
        Synth.write_reg(0x008A003C)
        Synth.write_reg(0x000004B3)
        Synth.write_reg(0x62005E42)
        Synth.write_reg(0x00008011)
        Synth.write_reg(0x00510000)

    @staticmethod
    def disable():
        # Set CE = 0, PDRF_N = 0
        mask = Synth.SYNTH_CONTROL_CE_MASK | Synth.SYNTH_CONTROL_PDRF_N_MASK
        DevMem.clear(Synth.REG_SYNTH_CONTROL, mask)

    @staticmethod
    def is_ready():
        val = DevMem.read(Synth.REG_SYNTH_CONTROL)
        if val & Synth.SYNTH_CONTROL_READY_MASK == Synth.SYNTH_CONTROL_READY_MASK:
            return True
        else:
            return False

    @staticmethod
    def is_locked():
        val = DevMem.read(Synth.REG_SYNTH_CONTROL)
        if val & Synth.SYNTH_CONTROL_LOCKED_MASK == Synth.SYNTH_CONTROL_LOCKED_MASK:
            return True
        else:
            return False

    @staticmethod
    def wait_ready(timeout = 1):
        count = 0
        count_lim = timeout * 10
        while count < count_lim:
            count += 1
            if Synth.is_ready():
                return True
            sleep(0.1)
        return False

    @staticmethod
    def wait_locked(timeout = 5):
        count = 0
        count_lim = timeout * 10
        while count < count_lim:
            count += 1
            if Synth.is_locked():
                return True
            sleep(0.1)
        return False

    @staticmethod
    def write_reg(val):
        if Synth.wait_ready():
            DevMem.write(Synth.REG_SYNTH_REGISTERS, val)
        else:
            print("ERROR: timed out waiting for synth ready")


if __name__ == "__main__":
    print("Synth tests:")
    print("  Note that DDS power must be enabled to power synth,")
    print("  synth will only tune and lock if DDS power enabled")
    print("  before running this test")
    print("")
    print("  Disable")
    Synth.disable()
    print("  Enable & initialise")
    Synth.initialise()
    print("  Locked: {}".format(Synth.wait_locked()))

