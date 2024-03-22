#!/bin/bash
# Set the NTM attenuator to 0 dB
devmem 0x40080580 32 0x3000

# Configure the DDS to output 1000 MHz CW
devmem 0x40080400 32 0x00010308
devmem 0x40080404 32 0x00800900
devmem 0x4008042C 32 0x55555555
devmem 0x40080430 32 0x035D0000

# Issue DDS IO Update
devmem 0x40080508 32 0x00000000
