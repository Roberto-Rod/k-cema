#!/bin/bash

# Power down DDS
devmem 0x40080500 32 0x00000007
