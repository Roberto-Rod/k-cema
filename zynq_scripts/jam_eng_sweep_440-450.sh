#!/bin/bash

# Put jamming engine into reset
devmem 0x40084004 32 0x00000001

# Write jamming engine memory
devmem 0x400C0000 32 0x00003101
devmem 0x400C0004 32 0x22C3F35C
devmem 0x400C0008 32 0x00000997
devmem 0x400C000C 32 0x04000000
devmem 0x400C0010 32 0x00001518

# Set start/end line
devmem 0x40084008 32 0x00000000
devmem 0x4008400C 32 0x00000004

# Start jamming engine
#devmem 0x40084004 32 0x00000000
