#!/usr/bin/env python3
from devmem import *

from time import sleep
import csv


class DDS:
    CAL_DIR_NAME = "/run/media/mmcblk0p2/calibration/"
    CAL_FILE_NAME = "dds_cal.csv"

    REG_DDS_CONTROL = 0x40080500
    REG_DDS_CLK_COUNT = 0x40080504
    REG_DDS_IO_UPDATE = 0x40080508
    REG_DDS_EXT_ATT = 0x40080580
    REG_DDS_REG_BASE = 0x40080400
    REG_DDS_CFR1 = REG_DDS_REG_BASE + 0x00 # Control Function Register 1
    REG_DDS_CFR2 = REG_DDS_REG_BASE + 0x04 # Control Function Register 2
    REG_DDS_CFR4 = REG_DDS_REG_BASE + 0x0C # Control Function Register 4
    REG_DDS_DRLL = REG_DDS_REG_BASE + 0x10 # Digital Ramp Rate Lower Limit
    REG_DDS_DRUL = REG_DDS_REG_BASE + 0x14 # Digital Ramp Rate Upper Limit
    REG_DDS_DRSS = REG_DDS_REG_BASE + 0x18 # Rising Digital Ramp Rate Step Size
    REG_DDS_DRR = REG_DDS_REG_BASE + 0x20 # Digital Ramp Rate
    REG_DDS_FTW = REG_DDS_REG_BASE + 0x2C # Frequency Tuning Word
    REG_DDS_ASF_POW = REG_DDS_REG_BASE + 0x30 # Amplitude Scale Factor/Phase Offset Word

    DDS_CFR1_SWEEP_MODE = 0x00016308
    DDS_CFR1_CW_MODE = 0x00010308
    DDS_CFR2_SWEEP_MODE = 0x000CA900
    DDS_CFR2_CW_MODE = 0x00800900
    DDS_CFR4_CAL_ENABLE = 0x01052120
    DDS_CFR4_CAL_DISABLE = 0x00052120
    DDS_DRLL_DEFAULT = 0x00000000
    DDS_DRUL_DEFAULT = 0xFFFFFFFF
    DDS_DRSS_DEFAULT = 0x00000000
    DDS_DRR_DEFAULT = 0x00010001
    DDS_ASF_POW_DEFAULT = 0x00000000

    DDS_CONTROL_BRIDGE_RST_MASK = (1 << 2)
    DDS_CONTROL_PDWN_MASK = (1 << 1)
    DDS_CONTROL_RST_MASK = (1 << 0)

    def __init__(self):
        self.synth_freq_Hz = 3240e6
        self.ftw = 0
        self.asf = 0
        self.phase = 0

    @staticmethod
    def enable_power(en = True):
        if en:
            DevMem.clear(DDS.REG_DDS_CONTROL, DDS.DDS_CONTROL_PDWN_MASK)
        else:
            DevMem.set(DDS.REG_DDS_CONTROL, DDS.DDS_CONTROL_PDWN_MASK)

    @staticmethod
    def initialise(sweep_mode = False):
        # Power up DDS and put it in reset, with the bridge (in FPGA)
        # out of reset
        DevMem.set(DDS.REG_DDS_CONTROL, DDS.DDS_CONTROL_RST_MASK)
        DevMem.clear(DDS.REG_DDS_CONTROL, DDS.DDS_CONTROL_BRIDGE_RST_MASK)
        DevMem.clear(DDS.REG_DDS_CONTROL, DDS.DDS_CONTROL_PDWN_MASK)

        # Wait 100 ms
        sleep(0.1)

        # Bring DDS out of reset
        DevMem.clear(DDS.REG_DDS_CONTROL, DDS.DDS_CONTROL_RST_MASK)

        # Enable DAC cal
        DevMem.write(DDS.REG_DDS_CFR4, DDS.DDS_CFR4_CAL_ENABLE)
        DDS.io_update()

        # Disable DAC cal
        DevMem.write(DDS.REG_DDS_CFR4, DDS.DDS_CFR4_CAL_DISABLE)
        DDS.io_update()

        # Initialise DDS registers
        if sweep_mode:
            DevMem.write(DDS.REG_DDS_CFR1, DDS.DDS_CFR1_SWEEP_MODE)
            DevMem.write(DDS.REG_DDS_CFR2, DDS.DDS_CFR2_SWEEP_MODE)
        else:
            DevMem.write(DDS.REG_DDS_CFR1, DDS.DDS_CFR1_CW_MODE)
            DevMem.write(DDS.REG_DDS_CFR2, DDS.DDS_CFR2_CW_MODE)
        DevMem.write(DDS.REG_DDS_DRLL, DDS.DDS_DRLL_DEFAULT)
        DevMem.write(DDS.REG_DDS_DRUL, DDS.DDS_DRUL_DEFAULT)
        DevMem.write(DDS.REG_DDS_DRSS, DDS.DDS_DRSS_DEFAULT)
        DevMem.write(DDS.REG_DDS_DRR, DDS.DDS_DRR_DEFAULT)
        DevMem.write(DDS.REG_DDS_ASF_POW, DDS.DDS_ASF_POW_DEFAULT)
        DDS.io_update()

    @staticmethod
    def clock_count():
        return DevMem.read(DDS.REG_DDS_CLK_COUNT)

    @staticmethod
    def io_update():
        DevMem.write(DDS.REG_DDS_IO_UPDATE, 0)

    def set_frequency(self, frequency_Hz, io_update = False):
        self.ftw = int(round((2 ** 32) * (frequency_Hz / self.synth_freq_Hz), 0))
        DevMem.write(DDS.REG_DDS_FTW, self.ftw)
        if io_update:
            self.io_update()

    def get_asf(self):
        return self.asf

    def set_asf(self, asf, io_update = False):
        self.asf = asf
        self.write_asf_pow(io_update)

    def set_att_dB(self, att_dB, io_update = False):
        ratio = 10 ** (att_dB / 20)
        self.set_asf(int(round(4095 / ratio, 0)), io_update)

    def set_pow(self, phase, io_update = False):
        self.phase = phase
        self.write_asf_pow(io_update)

    def write_asf_pow(self, io_update = False):
        asf_pow = ((self.asf << 16) & 0xFFFF0000) | (self.phase & 0x0000FFFF)
        DevMem.write(DDS.REG_DDS_ASF_POW, asf_pow)
        if io_update:
            self.io_update()

    def get_calibrated_asf(self, frequency_Hz):
        with open(self.CAL_DIR_NAME + self.CAL_FILE_NAME, mode = 'r') as csv_file:
            for i in range(4):
                csv_file.readline()
            csv_reader = csv.reader(csv_file)
            n = 0
            for row in csv_reader:
                if n == 0:
                    freq1 = float(row[0])
                    asf1 = float(row[1])
                    freq2 = freq1
                    asf2 = asf1
                else:
                    if float(row[0]) >= float(frequency_Hz):
                        freq2 = float(row[0])
                        asf2 = float(row[1])
                        break
                    freq1 = float(row[0])
                    asf1 = float(row[1])
                n += 1

            # If there was no data then return 0
            if n == 0:
                asf = 0
            # If we did not find a point within the table then use the asf value from the last point
            elif freq2 <= freq1:
                asf = asf1
            else:
                r = (float(frequency_Hz) - freq1) / (freq2 - freq1)
                asf = (r * (asf2 - asf1)) + asf1

            return int(round(asf, 0))


if __name__ == "__main__":
    print("DDS unit tests:")
    print("  Note that Jamming Engine must be held in reset")
    print("  and synth should be locked before running this test")
    print("")

    # Initialise DDS
    print("Initialise: ", end = "")
    DDS.initialise()
    print("OK")
    sleep(2)

    # Get clock count
    print("Clock count: {}".format(DDS.clock_count()))

    # Set frequency:
    d = DDS()
    d.set_frequency(100e6)
    print("Set frequency 100 MHz, FTW = {}: ".format(hex(d.ftw)), end = "")
    if d.ftw == 132560719:
        print("OK")
    else:
        print("FAIL")

    print("Set ASF to 0xDF (approx. 0 dBm out for attenuators = 0 dB")
    d.set_asf(0xDF)

    print("Set POW to 0x7FFF and issue IO Update")
    d.set_pow(0x7FFF, True)
