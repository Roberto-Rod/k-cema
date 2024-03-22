#!/bin/bash
# Disable +5V5 SMPS & +5V_TX LDO
devmem 0x40014000 32 0x00000000

