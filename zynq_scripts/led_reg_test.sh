#!/bin/bash

TESTCOUNT=0
ERRCOUNT=0

# Write checker board pattern to LED register
while true; do
    devmem 0x40030000 32 0xAAAAAAAA
    READBACK=$(devmem 0x40030000 32)
    TESTCOUNT=$((TESTCOUNT+1))
    if [ $READBACK != "0xAAAAAAAA" ]; then
        echo "Read error, expected 0xAAAAAAAA, got $READBACK"
        ERRCOUNT=$((ERRCOUNT+1))
        echo "Errors: $ERRCOUNT in $TESTCOUNT"
    fi

    devmem 0x40030000 32 0x55555555
    READBACK=$(devmem 0x40030000 32)
    TESTCOUNT=$((TESTCOUNT+1))
    if [ $READBACK != "0x55555555" ]; then
        echo "Read error, expected 0x55555555, got $READBACK"
        ERRCOUNT=$((ERRCOUNT+1))
        echo "Errors: $ERRCOUNT in $TESTCOUNT"
    fi
done
