#!/usr/bin/env python3
from devmem import *


class PLSPI:
    OFFSET_DATA = 0x0
    OFFSET_CSN_MASK = 0x4
    OFFSET_NR_TRANSFER_BITS = 0x8
    OFFSET_NR_INPUT_BITS = 0xC

    DEFAULT_CSN_MASK = 0x00000000

    def __init__(self, base_addr=0x40002000):
        self.base_addr = base_addr
        self.set_cs_n_mask(self.DEFAULT_CSN_MASK)

    def set_nr_input_bits(self, n):
        if n < 32:
            DevMem.write(self.base_addr + self.OFFSET_NR_INPUT_BITS, n)

    def set_nr_transfer_bits(self, n):
        if n <= 32:
            DevMem.write(self.base_addr + self.OFFSET_NR_TRANSFER_BITS, n-1)

    def set_cs_n_mask(self, mask):
        DevMem.write(self.base_addr + self.OFFSET_CSN_MASK, mask)

    def write_data(self, data, bits):
        if bits <= 32:
            # Move data left to be MSB-aligned
            data <<= (32-bits)
        self.set_nr_transfer_bits(bits)
        self.set_nr_input_bits(0)
        DevMem.write(self.base_addr + self.OFFSET_DATA, data)
        
    def read_data(self, wr_data, wr_bits, rd_bits=8):
        if wr_bits <= 32:
            # Move data left to be MSB-aligned
            wr_data <<= (32-wr_bits)
        self.set_nr_transfer_bits(wr_bits + rd_bits)
        self.set_nr_input_bits(rd_bits)
        DevMem.write(self.base_addr + self.OFFSET_DATA, wr_data)
        rd_data = DevMem.read(self.base_addr + self.OFFSET_DATA)
        rd_mask = 0
        for i in range(rd_bits):
            rd_mask |= (1 << i)
        return rd_data


if __name__ == "__main__":    
    spi = PLSPI(0x40013000)
    rd_data = spi.read_data(0x8230, 16, 8)
    print("0x{:X}".format(rd_data))
