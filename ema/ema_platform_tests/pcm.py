#!/usr/bin/env python3
import argparse


class PCM:
    DEVICE_NODE = "/sys/bus/i2c/devices/0-002c/rdac0"

    RDAC = {}
    RDAC[15] = 1013
    RDAC[16] = 912
    RDAC[17] = 821
    RDAC[18] = 739
    RDAC[19] = 664
    RDAC[20] = 595
    RDAC[21] = 532
    RDAC[22] = 473
    RDAC[23] = 420
    RDAC[24] = 370
    RDAC[25] = 323
    RDAC[26] = 280
    RDAC[27] = 240
    RDAC[28] = 202
    RDAC[29] = 166
    RDAC[30] = 133
    RDAC[31] = 101
    RDAC[32] = 72
    RDAC[33] = 44
    RDAC[34] = 17

    def set_voltage(volts):
        if not volts in PCM.RDAC.keys():
            return False
        try:
            # Open device node for writing
            f = open(PCM.DEVICE_NODE, "w")
            f.write("{}".format(PCM.RDAC[volts]))
        except:
            return False
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control PCM")
    parser.add_argument("voltage", help="Output voltage to set PCM to", type=int, default="28")
    args = parser.parse_args()
    voltage = args.voltage
    if voltage < 15:
        voltage = 15
    elif voltage > 33:
        voltage = 33
    print("Set PCM to +{} V: ".format(voltage), end = "", flush = True)
    if PCM.set_voltage(voltage):
        print("OK")
    else:
        print("FAIL")
