#!/bin/bash
# Enable the DDS synth
devmem 0x40080540 32 0x00000003

# Power Up DDS and hold in reset
devmem 0x40080500 32 0x00000001

# Configure the synth to output 1.00 GHz
devmem 0x40080544 32 0x00580005
usleep 10000
devmem 0x40080544 32 0x00aa003c
usleep 10000
devmem 0x40080544 32 0x000004b3
usleep 10000
devmem 0x40080544 32 0x62005e42
usleep 10000
devmem 0x40080544 32 0x00008011
usleep 10000
devmem 0x40080544 32 0x00640000

# Read synth status
usleep 200000
devmem 0x40080540
