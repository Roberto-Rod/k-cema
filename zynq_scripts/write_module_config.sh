#!/bin/bash
# Write 128 bytes in 16 byte chunks
OFFS=0
for P in {0..7}
do
    i2ctransfer -y 0 w17@0x50 $OFFS $(hexdump -n 16 -s $OFFS -v -e '1/1 "0x%02x "' $1)
    OFFS=$(($OFFS+16))
done
