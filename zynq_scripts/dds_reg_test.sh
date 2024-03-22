#!/bin/bash

# Put jamming engine into reset
devmem 0x40084004 32 0x00000001

# Bring DDS out of reset
devmem 0x40080500 32 0x00000000

TESTCOUNT=0
ERRCOUNT=0

# Write checker board pattern to DDS address 0x13
while true; do
#    usleep 100000
    devmem 0x4008044C 32 0xAAAAAAAA
#    usleep 100000
    devmem 0x40080508 32 0x00000000 # IO Update
    READBACK=$(devmem 0x4008044C 32)
    TESTCOUNT=$((TESTCOUNT+1))
    if [ $READBACK != "0xAAAAAAAA" ]; then
        echo "Read error, expected 0xAAAAAAAA, got $READBACK"
        ERRCOUNT=$((ERRCOUNT+1))
        echo "Errors: $ERRCOUNT in $TESTCOUNT"
    fi

#    usleep 100000
    devmem 0x4008044C 32 0x55555555
#    usleep 100000
    devmem 0x40080508 32 0x00000000 # IO Update
    READBACK=$(devmem 0x4008044C 32)
    TESTCOUNT=$((TESTCOUNT+1))
    if [ $READBACK != "0x55555555" ]; then
        echo "Read error, expected 0x55555555, got $READBACK"
        ERRCOUNT=$((ERRCOUNT+1))
        echo "Errors: $ERRCOUNT in $TESTCOUNT"
    fi
done
