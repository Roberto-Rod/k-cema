#!/usr/bin/env python3
from i2c import *
import sys


class AD9528:
    CHIP_ADDRESS = 0x55
    VENDOR_ID_ADDRESS = 0x000C
    IO_UPDATE_ADDRESS = 0x000F
    VCO_CAL_ADDRESS = 0x0203
    SYSREF_CTRL_LSB_ADDRESS = 0x0402
    SYSREF_CTRL_MSB_ADDRESS = 0x0403
    STATUS_0_ADDRESS = 0x0508
    STATUS_1_ADDRESS = 0x0509
    IO_UPDATE_VALUE = 0x01
    # Initialise AD9528 using settings detailed on this Confluence page:
    # http://confluence.kirintec.local/display/KEW/EMA+FPGA+AD9528+Settings
    INIT_REGS_SYSREF_STANDARD = [
        [0x0100, 0x01],
        [0x0102, 0x01],
        [0x0104, 0x04],
        [0x0109, 0x24],
        [0x0201, 0xC0],
        [0x0204, 0x03],
        [0x0300, 0x40],
        [0x0302, 0x00],
        [0x0303, 0x20],
        [0x0306, 0x40],
        [0x0308, 0x00],
        [0x0309, 0x20],
        [0x030A, 0x40], # XCVR refclk = LVDS (Boost Mode)
        [0x032D, 0x0B],
        [0x0401, 0x01],
        [0x0402, 0x98],
        [0x0403, 0x96],
        [0x0501, 0xF0],
        [0x0502, 0x3F],
        [0x0503, 0x0F],
        [0x0504, 0xC0]
    ]
    
    INIT_REGS_SYSREF_ALT = [
        [0x0100, 0x01],
        [0x0102, 0x01],
        [0x0104, 0x04],
        [0x0106, 0x8C],
        [0x0109, 0x24],
        [0x010A, 0x08],
        [0x0201, 0x87],
        [0x0203, 0x04],
        [0x0204, 0x03],
        [0x0207, 0x01],
        [0x0208, 0x09],
        [0x0300, 0x40],
        [0x0302, 0x13],
        [0x0303, 0x00],
        [0x0305, 0x09],
        [0x0306, 0x40],
        [0x0308, 0x13],
        [0x0309, 0x00],
        [0x030B, 0x09],
        [0x032D, 0x0A],
        [0x0400, 0x01],
        [0x0403, 0x96],
        [0x0501, 0xF0],
        [0x0502, 0x3F],
        [0x0503, 0x0F],
        [0x0504, 0xC0]
    ]

    INIT_REGS_SYSREF_CLOCK = [
        [0x0100, 0x01],
        [0x0102, 0x01],
        [0x0104, 0x04],
        [0x0106, 0x8C],
        [0x0109, 0x24],
        [0x010A, 0x08],
        [0x0201, 0x87],
        [0x0203, 0x04],
        [0x0204, 0x03],
        [0x0207, 0x01],
        [0x0208, 0x09],
        [0x0300, 0x00],
        [0x0302, 0x13],
        [0x0303, 0x00],
        [0x0305, 0x09],
        [0x0306, 0x00],
        [0x0308, 0x13],
        [0x0309, 0x00],
        [0x030B, 0x09],
        [0x032D, 0x00],
        [0x0400, 0x01],
        [0x0403, 0x96],
        [0x0501, 0xF0],
        [0x0502, 0x3F],
        [0x0503, 0x0F],
        [0x0504, 0xC0]
    ]

    def __init__(self, i2c_bus=1):
        self.i2c = I2C(i2c_bus, self.CHIP_ADDRESS)

    def write_reg(self, address, data):
        block = [(address >> 8) & 0xFF, address & 0xFF, data]
        return self.i2c.write_block(block)

    def read_reg(self, address):
        # Write 16-bit address as 1 byte address + 1 byte data
        self.i2c.write_byte((address >> 8) & 0xFF, address & 0xFF)
        return self.i2c.read_byte()

    def get_vendor_id(self):
        return (self.read_reg(0x000D) << 8) | self.read_reg(0x000C)

    def check_vendor_id(self):
        return self.get_vendor_id() == 0x456
        
    def sysref_reset(self, rst=True):
        ctrl = self.read_reg(self.SYSREF_CTRL_LSB_ADDRESS)
        if rst:
            ctrl |= 0x01
        else:
            ctrl &= ~0x01
        if self.write_reg(self.SYSREF_CTRL_LSB_ADDRESS, ctrl):
            return self.io_update()
        else:
            return False

    def sysref_request(self, enable=True):
        ctrl = self.read_reg(self.SYSREF_CTRL_MSB_ADDRESS)
        if enable:
            ctrl |= 0x01
        else:
            ctrl &= ~0x01
        if self.write_reg(self.SYSREF_CTRL_MSB_ADDRESS, ctrl):
            return self.io_update()
        else:
            return False

    def calibrate_vco(self):
        ok = True
        ok = ok and self.write_reg(AD9528.VCO_CAL_ADDRESS, 0x04)
        ok = ok and self.io_update()
        ok = ok and self.write_reg(AD9528.VCO_CAL_ADDRESS, 0x05)
        ok = ok and self.io_update()
        return ok

    def io_update(self):
        return self.write_reg(self.IO_UPDATE_ADDRESS, self.IO_UPDATE_VALUE)

    def initialise(self, validate=True):
        ok = True
        for reg in self.INIT_REGS_SYSREF_STANDARD:
            ok = ok and self.write_reg(reg[0], reg[1])
        ok = ok and self.io_update()
        if validate:
            for reg in self.INIT_REGS_SYSREF_STANDARD:
                val = self.read_reg(reg[0])
                ok = ok and (val == reg[1])
        ok = ok and self.calibrate_vco()
        return ok


if __name__ == "__main__":
    print("AD9528 tests:")
    a = AD9528()
    status_req = False
    calibrate_vco = False
    sysref_req = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 's':
            status_req = True
        elif sys.argv[1] == 'c':
            calibrate_vco = True
        elif sys.argv[1] == 'q':
            sysref_req = True

    if sysref_req:
        print("Sysref Request...")
        a.sysref_reset(True)
        a.sysref_reset(False)
        a.sysref_request(True)
    elif calibrate_vco:
        print("Calibrate VCO...")
        a.calibrate_vco()
    elif status_req:
        print("Status...")
        a.sysref_request(False)
    else:
        print("Check Vendor ID: ", end="", flush=True)
        if a.check_vendor_id():
            print("OK")
        else:
            print("FAIL")

        print("Initialise: ", end="", flush=True)
        if a.initialise(validate=True):
            print("OK")
        else:
            print("FAIL")

    print("Status 0: 0x{:02x}".format(a.read_reg(AD9528.STATUS_0_ADDRESS)))
    print("Status 1: 0x{:02x}".format(a.read_reg(AD9528.STATUS_1_ADDRESS)))
