#!/usr/bin/env python3
from os import popen


class I2C:
    def __init__(self, bus_nr, chip_address):
        self.bus_nr = bus_nr
        self.chip_address = chip_address

    def write_byte(self, address, data):
        cmd = "/usr/sbin/i2cset -y -f {} {} {} {} b".format(int(self.bus_nr), hex(self.chip_address), hex(address), hex(data))
        try:
            # Read the output so that we block and wait for command to return
            ret = popen(cmd).read()
        except:
            return False
        return True

    def write_word(self, address, data):
        cmd = "/usr/sbin/i2cset -y -f {} {} {} {} w".format(int(self.bus_nr), hex(self.chip_address), hex(address), hex(data))
        try:
            # Read the output so that we block and wait for command to return
            ret = popen(cmd).read()
        except:
            return False
        return True

    def write_block(self, data):
        cmd = "/usr/sbin/i2cset -y -f {} {}".format(int(self.bus_nr), hex(self.chip_address))
        for d in data:
            cmd += " {}".format(hex(d))
        cmd += " i"
        try:
            # Read the output so that we block and wait for command to return
            ret = popen(cmd).read()
        except:
            return False
        return True

    def read_byte(self, address=None):
        if address is not None:
            cmd = "/usr/sbin/i2cget -y -f {} {} {} b".format(int(self.bus_nr), hex(self.chip_address), hex(address))
        else:
            cmd = "/usr/sbin/i2cget -y -f {} {}".format(int(self.bus_nr), hex(self.chip_address))
        try:
            val = int(popen(cmd).read(), 0)
        except:
            val = -1
        return val

    def read_word(self, address):
        cmd = "/usr/sbin/i2cget -y -f {} {} {} w".format(int(self.bus_nr), hex(self.chip_address), hex(address))
        try:
            val = int(popen(cmd).read(), 0)
        except:
            val = -1
        return val


if __name__ == "__main__":
    print("Module is not intended to be executed stand-alone")
