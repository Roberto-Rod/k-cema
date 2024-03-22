#!/usr/bin/env python3
from devmem import *
from band import *
from blank_control import *
from time import sleep
from enum import Enum
import argparse


class IPAMModule(Enum):
    ASSEMBLY = 0,
    CONTROL_BOARD = 1,
    RF_BOARD = 2


class IPAMPowerClass(Enum):
    UNKNOWN = 0,
    VEHICLE = 1,
    MANPACK = 2


class IPAM:
    REG_JAMMING_ENGINE_BASE = 0x40080000
    REG_IPAM_CONTROL = REG_JAMMING_ENGINE_BASE + (0x170 * 4)
    REG_BRIDGE_BASE = 0x40031000
    REG_BRIDGE_CTRL_STAT = REG_BRIDGE_BASE + 0x0
    REG_BRIDGE_ADDRESS = REG_BRIDGE_BASE + 0x4
    REG_BRIDGE_DATA = REG_BRIDGE_BASE + 0x8
    REG_BRIDGE_IPAM_STATUS = REG_BRIDGE_BASE + 0xC

    CTRL_STAT_START_MASK = 0x00000001
    CTRL_STAT_READ_MASK = 0x00000002
    CTRL_STAT_READY_MASK = 0x00000004
    CTRL_STAT_ERROR_MASK = 0x00000008
    CTRL_STAT_COMMS_GOOD_MASK = 0x80000000

    IPAM_CTRL_FORCE_MUTE = 0x00000004
    IPAM_CTRL_PWR_EN_N_MASK = 0x00000002

    IPAM_REG_ADDR_PART_NUMBER = {IPAMModule.ASSEMBLY: 0x0001,
                                 IPAMModule.CONTROL_BOARD: 0x0003,
                                 IPAMModule.RF_BOARD: 0x0008}

    IPAM_REG_ADDR_SERIAL_NUMBER = {IPAMModule.ASSEMBLY: 0x0002,
                                   IPAMModule.CONTROL_BOARD: 0x0004,
                                   IPAMModule.RF_BOARD: 0x0009}
    IPAM_REG_ADDR_FIRMWARE_VERS = 0x0006
    IPAM_REG_ADDR_RF_BOARD_SER_REV = 0x0009
    IPAM_REG_ADDR_BIT_FLAGS_LOWER = 0x0050
    IPAM_REG_ADDR_BIT_FLAGS_UPPER = 0x0051
    IPAM_REG_ADDR_RF_PATH_CTRL = 0x005A
    IPAM_REG_ADDR_BASE_ATT = 0x005B
    IPAM_REG_ADDR_USER_ATT = 0x005C
    IPAM_REG_ADDR_ADC_BASE = 0x0060
    IPAM_REG_ADDR_VSWR_CONTROL = 0x0100
    IPAM_REG_ADDR_VSWR_STATUS = 0x0101
    IPAM_REG_ADDR_VSWR_RESULTS = 0x0102
    IPAM_REG_ADDR_VSWR_THRESH = 0x0103
    IPAM_REG_ADDR_IIR_COEFF = 0x0111
    IPAM_REG_ADDR_POWER_MONITOR = 0x0112

    PA_BAND_SEL_MASK = 1 << 25
    PA_PORT_PRI = 0
    PA_PORT_EXT = 1

    ADC_CHAN_CORE_TEMP = 0
    ADC_CHAN_BASE_TEMP = 1
    ADC_CHAN_INPUT_VOLTAGE = 17
    ADC_CHAN_INPUT_CURRENT = 18

    POWER_ENABLE_TIMEOUT_S = 10

    def enable_power(en = True):
        if en:
            DevMem.clear(IPAM.REG_IPAM_CONTROL, IPAM.IPAM_CTRL_PWR_EN_N_MASK)
        else:
            DevMem.set(IPAM.REG_IPAM_CONTROL, IPAM.IPAM_CTRL_PWR_EN_N_MASK)

    def force_mute(mute = True):
        if mute:
            DevMem.set(IPAM.REG_IPAM_CONTROL, IPAM.IPAM_CTRL_FORCE_MUTE)
        else:
            BlankControl.set_ext_blank_n_enabled(False)
            DevMem.clear(IPAM.REG_IPAM_CONTROL, IPAM.IPAM_CTRL_FORCE_MUTE)

    def get_part_number(module=IPAMModule.ASSEMBLY):
        reg = IPAM.reg_read(IPAM.IPAM_REG_ADDR_PART_NUMBER[module])
        index = (reg >> 8) & 0xFFFF
        var = reg & 0xFF
        if module == IPAMModule.ASSEMBLY:
            prefix = "KT-950"
        else:
            prefix = "KT-000"
        return "{}-{:04d}-{:02d}".format(prefix, index, var)

    def get_serial_number(module=IPAMModule.ASSEMBLY):
        reg = IPAM.reg_read(IPAM.IPAM_REG_ADDR_SERIAL_NUMBER[module])
        ser = reg & 0xFFFF
        # Board level serial numbers need to have an offset of 200000 applied as
        # the register is 16-bits and doesn't handle the PCB manufacturer serial
        # number format
        if module != IPAMModule.ASSEMBLY:
            ser += 200000
        return "{:06d}".format(ser)

    def get_rf_rev():
        reg = IPAM.reg_read(IPAM.IPAM_REG_ADDR_RF_BOARD_SER_REV)
        rev_int = (reg >> 16) & 0xFF
        return chr(0x41 + rev_int)

    def get_rf_band():
        part_number = IPAM.get_part_number()
        if part_number == "KT-950-0340-00":     # LB-R, 100 W
            return Band.LOW
        elif part_number == "KT-950-0341-00":   # MB-R, 100 W
            return Band.MID
        elif part_number == "KT-950-0342-00":   # HB-R, 50 W
            return Band.HIGH
        elif part_number == "KT-950-0405-00":   # HB-A, 50 W
            return Band.HIGH
        elif part_number == "KT-950-0500-00":   # LB-R, 15 W
            return Band.LOW
        elif part_number == "KT-950-0501-00":   # MB-R, 15 W
            return Band.MID
        elif part_number == "KT-950-0502-00":   # HB-R, 15 W, 8 GHz
            return Band.HIGH
        elif part_number == "KT-950-0502-01":   # HB-R, 15 W, 6 GHz
            return Band.HIGH

        # Didn't find a known part number
        return Band.UNKNOWN

    def is_extended_high_band():
        part_number = IPAM.get_part_number()
        return part_number == "KT-950-0502-00"

    def get_power_class():
        part_number = IPAM.get_part_number()
        if part_number == "KT-950-0340-00":  # LB-R, 100 W
            return IPAMPowerClass.VEHICLE
        elif part_number == "KT-950-0341-00":  # MB-R, 100 W
            return IPAMPowerClass.VEHICLE
        elif part_number == "KT-950-0342-00":  # HB-R, 50 W
            return IPAMPowerClass.VEHICLE
        elif part_number == "KT-950-0405-00":  # HB-A, 50 W
            return IPAMPowerClass.VEHICLE
        elif part_number == "KT-950-0500-00":  # LB-R, 15 W
            return IPAMPowerClass.MANPACK
        elif part_number == "KT-950-0501-00":  # MB-R, 15 W
            return IPAMPowerClass.MANPACK
        elif part_number == "KT-950-0502-00":  # HB-R, 15 W, 8 GHz
            return IPAMPowerClass.MANPACK
        elif part_number == "KT-950-0502-01":  # HB-R, 15 W, 6 GHz
            return IPAMPowerClass.MANPACK

        # Didn't find a known part number
        return IPAMPowerClass.UNKNOWN

    def set_pa_port(port):
        if port == IPAM.PA_PORT_PRI or port == IPAM.PA_PORT_EXT:
            val = IPAM.reg_read(IPAM.IPAM_REG_ADDR_RF_PATH_CTRL)
            if val >= 0:
                if port == IPAM.PA_PORT_PRI:
                    val &= ~IPAM.PA_BAND_SEL_MASK
                else:
                    val |= IPAM.PA_BAND_SEL_MASK
                return IPAM.reg_write(IPAM.IPAM_REG_ADDR_RF_PATH_CTRL, val)
        return False

    def initialise_vswr():
        ok = True
        diff_thresh = 0
        fwd_thresh = 0
        band = IPAM.get_rf_band()
        if band == Band.LOW:
            diff_thresh = 286
            fwd_thresh = 2146
        elif band == Band.MID:
            diff_thresh = 286
            fwd_thresh = 2621
        elif band == Band.HIGH:
            diff_thresh = 196
            fwd_thresh = 1535
        else:
            ok = False
        if ok:
            thresholds = ((fwd_thresh << 16) & 0xFFF0000) & (diff_thresh & 0xFFF)
            # Write thresholds, enable VSWR, forward power and mute-on-fail
            ok = IPAM.reg_write(IPAM.IPAM_REG_ADDR_VSWR_THRESH, thresholds) and \
                 IPAM.reg_write(IPAM.IPAM_REG_ADDR_VSWR_CONTROL, 0xB)
        return ok

    def get_vswr_status():
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_VSWR_STATUS)

    def get_vswr_results():
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_VSWR_RESULTS)

    def get_user_base_att_index():
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_BASE_ATT)

    def set_user_att_index(att_index):
        att_index += IPAM.get_user_base_att()
        return IPAM.reg_write(IPAM.IPAM_REG_ADDR_USER_ATT)

    def set_user_att_db(att_dB):
        IPAM.set_user_att_index(round(int(att_dB * 2), 0))

    def is_responsive():
        part_number = IPAM.get_part_number()
        responsive = True
        if part_number == "KT-950-0405-00":    # HB-A
            responsive = False
        return responsive

    def get_firmware_version():
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_FIRMWARE_VERS)

    def get_firmware_version_string():
        vers = IPAM.get_firmware_version()
        major = (vers >> 24) & 0xFF
        minor = (vers >> 8) & 0xFFFF
        patch = vers & 0xFF
        return ("{}.{}.{}".format(major, minor, patch))

    def get_temperature():
        core = ((IPAM.get_adc(IPAM.ADC_CHAN_CORE_TEMP) * (2.5 / 4096)) - 0.5) * 100
        base = ((IPAM.get_adc(IPAM.ADC_CHAN_BASE_TEMP) * (2.5 / 4096)) - 0.5) * 100
        if core > base:
            return core
        else:
            return base

    def get_input_voltage():
        return ((IPAM.get_adc(IPAM.ADC_CHAN_INPUT_VOLTAGE) * (5.0 / 4096))) * 11

    def get_input_current(manpack=False):
        reading = IPAM.get_adc(IPAM.ADC_CHAN_INPUT_CURRENT)
        if manpack:
            return ((reading * (5.0 / 4096)) / 19.5) * 50
        else:
            return ((reading * (5.0 / 4096)) / 19.5) * 100

    def get_input_power(manpack=False):
        return IPAM.get_input_voltage() * IPAM.get_input_current(manpack)

    def get_adc(channel):
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_ADC_BASE + channel)

    def get_bit_flags_lower():
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_BIT_FLAGS_LOWER)

    def get_bit_flags_upper():
        return IPAM.reg_read(IPAM.IPAM_REG_ADDR_BIT_FLAGS_UPPER)

    def reset_bit_flags():
        IPAM.reg_write(IPAM.IPAM_REG_ADDR_BIT_FLAGS_LOWER, 0)
        IPAM.reg_write(IPAM.IPAM_REG_ADDR_BIT_FLAGS_UPPER, 0)

    def prepare_power_monitor():
        # Set the time constant to 0.01 s
        return IPAM.reg_write(IPAM.IPAM_REG_ADDR_IIR_COEFF, 0x106 * 100)

    def get_power_monitor_readings():
        reg = IPAM.reg_read(IPAM.IPAM_REG_ADDR_POWER_MONITOR)
        values = {}
        values["fwd"] = reg & 0xFFF
        values["rev"] = (reg >> 16) & 0xFFF
        return values

    def reg_write(address, data):
        if IPAM.wait_comms_good():
            DevMem.write(IPAM.REG_BRIDGE_ADDRESS, address)
            DevMem.write(IPAM.REG_BRIDGE_DATA, data)
            DevMem.clear(IPAM.REG_BRIDGE_CTRL_STAT, IPAM.CTRL_STAT_READ_MASK)
            DevMem.set(IPAM.REG_BRIDGE_CTRL_STAT, IPAM.CTRL_STAT_START_MASK)
            if IPAM.wait_ready():
                if not IPAM.error():
                    return True
            else:
                print("ERROR - IPAM.reg_write timeout on wait_ready")
        else:
            print("ERROR - IPAM.reg_write timeout on wait_comms_good")
        return False

    def reg_read(address):
        if IPAM.wait_comms_good():
            DevMem.write(IPAM.REG_BRIDGE_ADDRESS, address)
            DevMem.set(IPAM.REG_BRIDGE_CTRL_STAT, IPAM.CTRL_STAT_READ_MASK)
            DevMem.set(IPAM.REG_BRIDGE_CTRL_STAT, IPAM.CTRL_STAT_START_MASK)
            if IPAM.wait_ready():
                if not IPAM.error():
                    return DevMem.read(IPAM.REG_BRIDGE_DATA)
            else:
                print("ERROR - IPAM.reg_read timeout on wait_ready")
        else:
            print("ERROR - IPAM.reg_read timeout on wait_comms_good")
        return -1

    def wait_comms_good(timeout = 10):
        for n in range(0, int(timeout * 10)):
            if IPAM.comms_good():
                return True
            sleep(0.1)
        return False

    def wait_ready(timeout = 1):
        for n in range(0, timeout * 10):
            if IPAM.ready():
                return True
            sleep(0.1)
            print(int(n))
        return False

    def comms_good():
        return (DevMem.read(IPAM.REG_BRIDGE_CTRL_STAT) & IPAM.CTRL_STAT_COMMS_GOOD_MASK) != 0

    def ready():
        return (DevMem.read(IPAM.REG_BRIDGE_CTRL_STAT) & IPAM.CTRL_STAT_READY_MASK) != 0

    def error():
        return (DevMem.read(IPAM.REG_BRIDGE_CTRL_STAT) & IPAM.CTRL_STAT_ERROR_MASK) != 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control IPAM")
    parser.add_argument("-e", "--enable", help="Leave IPAM enabled after running tests", action="store_true")
    parser.add_argument("-d", "--disable", help="Just disable IPAM, do not run tests", action="store_true")
    parser.add_argument("-b", "--band_type", help="Get IPAM band and type", action="store_true")
    parser.add_argument("-f", "--bit_flags", help="Get IPAM BIT flags", action="store_true")
    parser.add_argument("-r", "--read_addr", help="Read register address")
    args = parser.parse_args()
    if args.bit_flags:
        if IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S):
            print("Bit Flags, Lower: 0x{:08x}".format(IPAM.get_bit_flags_lower()))
            print("Bit Flags, Upper: 0x{:08x}".format(IPAM.get_bit_flags_upper()))
            print("VSWR Status: 0x{:08x}".format(IPAM.get_vswr_status()))
            print("VSWR Results: 0x{:08x}".format(IPAM.get_vswr_results()))
            print("RF rev: {}".format(IPAM.get_rf_rev()))
    elif args.band_type:
        type = "Type Unknown"
        band = "Band Unknown"
        IPAM.enable_power(True)
        if IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S):
            if IPAM.is_responsive():
                type = "responsive"
            else:
                type = "active"
            band = IPAM.get_rf_band()
        if args.disable:
            IPAM.enable_power(False)
        print("{},{}".format(band, type))
    else:
        if not args.disable:
            IPAM.enable_power(True)
            print("Wait for IPAM comms good...")
            if not IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S):
                print("ERROR - timed out")
                exit()
            if args.read_addr is not None:
                print("0x{:02x}: 0x{:08x}".format(int(args.read_addr, 0), IPAM.reg_read(int(args.read_addr, 0))))
            #print("IPAM Firmware Version: {}".format(IPAM.get_firmware_version_string()))
            #print("IPAM Assembly Part Number:        {}".format(IPAM.get_part_number(IPAMModule.ASSEMBLY)))
            #print("IPAM Assembly Serial Number:      {}".format(IPAM.get_serial_number(IPAMModule.ASSEMBLY)))
            #print("IPAM Control Board Part Number:   {}".format(IPAM.get_part_number(IPAMModule.CONTROL_BOARD)))
            #print("IPAM Control Board Serial Number: {}".format(IPAM.get_serial_number(IPAMModule.CONTROL_BOARD)))
            #print("IPAM RF Board Part Number:        {}".format(IPAM.get_part_number(IPAMModule.RF_BOARD)))
            #print("IPAM RF Board Serial Number:      {}".format(IPAM.get_serial_number(IPAMModule.RF_BOARD)))
        elif args.disable or not args.enable:
            IPAM.enable_power(False)
