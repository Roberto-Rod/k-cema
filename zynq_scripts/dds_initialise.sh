#!/bin/bash

# Put jamming engine into reset
devmem 0x40084004 32 0x00000001

# Bring DDS out of reset
devmem 0x40080500 32 0x00000000

# Initialise DDS and run calibration
devmem 0x4008040C 32 0x01052120
devmem 0x40080508 32 0x00000000 # IO Update
devmem 0x4008040C 32 0x00052120
devmem 0x40080508 32 0x00000000 # IO Update

# Initialise DDS registers
devmem 0x40080400 32 0x00016308
devmem 0x40080404 32 0x000ca900
devmem 0x40080410 32 0x00000000
devmem 0x40080414 32 0xffffffff
devmem 0x40080418 32 0x00000000
devmem 0x40080420 32 0x00010001
devmem 0x40080430 32 0x00000000
devmem 0x40080508 32 0x00000000 # IO Update

