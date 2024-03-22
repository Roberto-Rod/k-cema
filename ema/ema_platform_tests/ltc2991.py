#!/usr/bin/env python3
from i2c import *
from time import sleep
import argparse


class LTC2991:
    CHIP_ADDRESS_BASE = 0x48
    REG_STATUS_LOW = 0x00
    REG_TRIGGER = 0x01
    REG_V1_BASE = 0x0A
    REG_TEMP_BASE = 0x1A
    REG_VCC_BASE = 0x1C
    CONFIG = [
        # Configuration data: address, data
        [0x08, 0x10],   # Repeated acquisition
        [0x01, 0xF8]    # Enable V1-V8 & trigger
    ]

    def __init__(self, bus, offset):
        self.i2c = I2C(bus, self.CHIP_ADDRESS_BASE + offset)
        for reg in self.CONFIG:
            self.i2c.write_byte(reg[0], reg[1])

    def read_channel_volts(self, channel):
        try:
            if channel == 8:
                # Channel 8 = VCC
                return self.read_vcc_volts()
            else:
                # Channel 0-7 = V1-V8 inputs
                val = self.read_channel(channel)
            return val * 5 / 16384
        except Exception as e:
            print("LTC2991 e1: {}".format(e))
            return 0

    def read_channel(self, channel):
        try:
            while True:
                reg_msb = self.REG_V1_BASE + (channel * 2)
                reg_lsb = reg_msb + 1
                lsb = self.i2c.read_byte(reg_lsb)
                msb = self.i2c.read_byte(reg_msb)
                val = ((msb & 0x3F) << 8) | lsb
                if val > 0x3000:
                    val = 0
                if (msb & 0x80) == 0x80:
                    break
                sleep(0.01)
            return val
        except Exception as e:
            print("LTC2991 e2: {}".format(e))
            return 0
            
    def read_vcc_volts(self):
        try:
            while True:
                reg_msb = self.REG_VCC_BASE
                reg_lsb = reg_msb + 1
                lsb = self.i2c.read_byte(reg_lsb)
                msb = self.i2c.read_byte(reg_msb)
                val = ((msb & 0x3F) << 8) | lsb
                if val > 0x3000:
                    val = 0
                if (msb & 0x80) == 0x80:
                    break
                sleep(0.01)
            return 2.5 + (val * 5 / 16384)
        except Exception as e:
            print("LTC2991 e2: {}".format(e))
            return 0

    def channel_ready(self, channel):
        return (self.i2c.read_byte(self.REG_STATUS_LOW) & (1 << channel)) != 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read the LTC2991 channel voltages")
    parser.add_argument("offset", nargs='?', default=4, type=int, help="Offset added to chip base address of 0x48")
    args = parser.parse_args()
    print("LTC2991 Tests")
    ltc = LTC2991(1, args.offset)
    for ch in range(9):
        print("Channel {}: {:.2f} V".format(ch, ltc.read_channel_volts(ch)))