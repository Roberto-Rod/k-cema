#!/usr/bin/env python3
from i2c import *
import sys


class MCP4728:
    CHIP_ADDRESS = 0x60
    CMD_WRITE_DAC = 0x4090  # Command=010, DAC=0, UDACn=0, VREF=1 (internal), PD=0 (normal), Gx=1 (x2)

    def __init__(self, i2c_bus=1):
        self.i2c = I2C(i2c_bus, self.CHIP_ADDRESS)

    def write_dac(self, value):
        if value <= 0xFFF:
            block = [self.CMD_WRITE_DAC >> 8, (self.CMD_WRITE_DAC & 0xFF) | (value >> 8), value & 0xFF]
            return self.i2c.write_block(block)
        else:
            return False

    def read_dac(self):
        # Given limitations of i2ctools (without including i2ctransfer) we can only read
        # back 2 bytes (readback is one long string of bytes, no auto-incrementing address)
        # This returns the first two bytes of Channel A DAC Register which can be used
        # to partially verify a write.
        return self.i2c.read_word(0x00)

    def set_dac_midscale(self):
        if self.write_dac(0x672):
            return self.read_dac() == 0x96c0
        else:
            return False


if __name__ == "__main__":    
    m = MCP4728()
    if len(sys.argv) >= 2:
        val = int(sys.argv[1])
        if 0 <= val < 0xFFF:
            print("Set DAC to 0x{:03x}: ".format(val), end="", flush=True)
            if m.write_dac(val):
                print("OK")
            else:
                print("FAIL")
    else:
        print("MCP4728 Tests")
        print("Write DAC: ", end="", flush=True)
        if m.write_dac(0x900):
            print("OK")
        else:
            print("FAIL")

        print("Verify write: ", end="", flush=True)
        if m.read_dac() == 0x99c0:
            print("OK")
        else:
            print("FAIL")

        print("Set DAC to mid-scale: ", end="", flush=True)
        if m.set_dac_midscale():
            print("OK")
        else:
            print("FAIL")
