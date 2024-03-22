#!/usr/bin/env python3

from datetime import datetime
from devmem import DevMem

REG_BASE_CORE = 0x40005000  # S00
REG_BASE_PHY = 0x40006000  # S01

now = datetime.now()
filename = "/run/media/mmcblk0p2/{}-jesd204b-reg.txt".format(now.strftime("%Y-%m-%d-%H-%M-%S"))
print("Dumping JESD204B registers to {}".format(filename))
file = open(filename, "w")
file.write("JESD204B Core:\n")
for reg in range(0, 0x834, 4):
    if 0 <= reg <= 0x3C or 0x800 <= reg <= 0x830:
        addr = REG_BASE_CORE + reg
        val = DevMem.read(addr)
        file.write("0x{:04x}\t0x{:08x}\n".format(reg, val))

file.write("JESD204B PHY:\n")
for reg in range(0, 0x614, 4):
    if 0 <= reg <= 0xE8 or 0x104 <= reg <= 0x11C or 0x204 <= reg <= 0x21C or 0x304 <= reg <= 0x308 or \
            0x404 <= reg <= 0x434 or 0x504 <= reg <= 0x524 or 0x604 <= reg <= 0x610:
        addr = REG_BASE_PHY + reg
        val = DevMem.read(addr)
        file.write("0x{:04x}\t0x{:08x}\n".format(reg, val))
file.close()
print("DONE")
