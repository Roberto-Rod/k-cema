#!/bin/bash
OFFS=32
for i in {0..15}
do
    i2ctransfer -y 0 w1@0x50 $OFFS r1 | awk '{printf "%c", $1}'
    OFFS=$((OFFS+1))
done
