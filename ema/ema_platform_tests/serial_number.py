#!/usr/bin/env python3
from enum import Enum


class Module(Enum):
    EMA = 0,
    PCM = 1,
    NTM_DIGITAL = 2,
    NTM_RF = 3


class SerialNumber:
    file_node = {}
    file_node[Module.EMA] = "/sys/bus/i2c/devices/0-0050/eeprom"
    file_node[Module.PCM] = "/sys/bus/i2c/devices/0-0057/eeprom"
    file_node[Module.NTM_DIGITAL] = "/sys/bus/i2c/devices/0-0051/eeprom"
    file_node[Module.NTM_RF] = "/sys/bus/i2c/devices/1-0050/eeprom"

    module_name = {}
    module_name[Module.EMA] = "EMA"
    module_name[Module.PCM] = "PCM"
    module_name[Module.NTM_DIGITAL] = "NTM Digital Board"
    module_name[Module.NTM_RF] = "NTM RF Board"

    def get_serial(module):
        try:
            with open(SerialNumber.file_node[module], "rb") as file:
                file.seek(32)
                serial = file.read(16)
                return serial.decode("utf-8").rstrip('\x00')
        except:
            pass
        return "000000"


if __name__ == "__main__":
    for m in Module:
        print("{} Serial Number: {}".format(SerialNumber.module_name[m], SerialNumber.get_serial(m)))
