#!/usr/bin/env python3
import os


class DevMem:
    @staticmethod
    def read(address):
        cmd = '/sbin/devmem ' + hex(address) + ' 32';
        return int(os.popen(cmd).read(), 0)

    @staticmethod
    def write(address, data):
        cmd = '/sbin/devmem ' + hex(address) + ' 32 ' + hex(data)
        # Read the output so that we block and wait for command to return
        ret = os.popen(cmd).read()
        return True

    # Read/Modify/Write
    # Overwrites only the bits which are set in the mask
    # shifts data to align bit 0 of data with the least significant
    # bit which is set in the mask
    @staticmethod
    def rmw(address, data, mask):
        # Find the least signficant bit which is set in the address
        lsb = 0
        for b in range(31,-1,-1):
            if (mask & (1 << b)) > 0:
                lsb = b
        val = DevMem.read(address)
        val &= ~mask
        val |= (data << lsb) & mask
        DevMem.write(address, val)
        return True

    @staticmethod
    def set(address, mask):
        val = DevMem.read(address)
        DevMem.write(address, val | mask)
        return True

    @staticmethod
    def clear(address, mask):
        val = DevMem.read(address)
        DevMem.write(address, val & ~mask)
        return True


if __name__ == "__main__":
    # Read/write tests; write to first LED register

    # Write LED register
    print("Write 0xFF00FF00 to 0x400030000")
    DevMem.write(0x40030000, 0xFF00FF00)

    # Read LED register
    val = DevMem.read(0x40030000)
    if (val != 0xFF00FF00):
        print("Fail, expected 0xFF00FF00 got " + hex(val))
        exit()

    # Write LED register
    print("Write 0x00000000 to 0x400030000")
    DevMem.write(0x40030000, 0)
    # Read LED register
    val = DevMem.read(0x40030000)
    if (val != 0):
        print("Fail, expected 0 got " + hex(val))
        exit()

    print("OK: all tests passed")
