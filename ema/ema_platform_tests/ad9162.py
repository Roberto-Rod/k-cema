#!/usr/bin/env python3
from devmem import DevMem
from pl_spi import PLSPI
from power_supplies import PowerSupplies
from time import sleep

import argparse
import csv


class AD9162:
    CAL_DIR_NAME = "/run/media/mmcblk0p2/calibration/"
    CAL_FILE_NAME = "dac_cal.csv"

    SPI_MASTER_BASE_ADDR = 0x40013000
    GPIO_TX_DAC_CTRL_ADDR = 0x40015000
    DAC_TX_EN_MASK = 0x00000002
    DAC_RST_N_MASK = 0x00000001
    IRQ_STATUS = 0x024
    IRQ_ENABLE = 0x020
    ANA_DAC_BIAS_PD = 0x040
    PRIVATE_REG_58 = 0x058
    CLK_PD = 0x080
    PLL_REF_CLK_PD = 0x084
    DLL_PD = 0x090
    DLL_CTRL = 0x091
    DLL_STATUS = 0x092
    PRIVATE_REG_9E = 0x09E
    PRIVATE_REG_D2 = 0x0D2
    PRIVATE_REG_E8 = 0x0E8
    INTERP_MODE = 0x110
    DATAPATH_CFG = 0x111
    DIG_TEST = 0x150
    DECODE_MODE = 0x152
    MASTER_PD = 0x200
    PHY_PD = 0x201
    CDR_RESET = 0x206
    CDR_OPERATING_MODE_REG_0 = 0x230
    SYNTH_ENABLE_CNTRL = 0x280
    PLL_STATUS = 0x281
    REF_CLK_DIVIDER_LDO = 0x289
    TERM_BLK1_CTRLREG0 = 0x2A7
    TERM_BLK2_CTRLREG0 = 0x2AE
    PRIVATE_REG_29E = 0x29E
    GENERAL_JRX_CTRL_0 = 0x300
    PHY_PRBS_TEST_THRESHOLD_LOBITS = 0x317
    ILS_DID = 0x450
    ILS_BID= 0x451
    ILS_LID0 = 0x452
    ILS_SCR_L = 0x453
    ILS_F = 0x454
    ILS_K = 0x455
    ILS_M = 0x456
    ILS_CS_N = 0x457
    ILS_NP = 0x458
    ILS_S = 0x459
    ILS_HD_CF = 0x45A
    ILS_RES1 = 0x45B
    ILS_RES2 = 0x45C
    ILS_CHECKSUM = 0x45D
    CODE_GRP_SYNC = 0x470
    FRAME_SYNC = 0x471
    GOOD_CHECKSUM = 0x472
    INIT_LANE_SYNC = 0x473
    CTRLREG0 = 0x475
    ECNT_CTRL_BASE = 0x480
    JESD_IRQ_ENABLEA = 0x4B8
    JESD_IRQ_ENABLEB = 0x4B9
    JESD_IRQ_STATUSA = 0x4BA
    JESD_IRQ_STATUSB = 0x4BB
    PRIVATE_REG_604 = 0x604
    PRIVATE_REG_606 = 0x606
    PRIVATE_REG_607 = 0x607

    DAC_FULL_SCALE = 5120  # DAC amplitude to match DDS full-scale

    def __init__(self, fdac=5e9):
        self.spi = PLSPI(self.SPI_MASTER_BASE_ADDR)
        self.amplitude = 0
        self.fdac = fdac

    @staticmethod
    def enable_power():
        PowerSupplies.tx_dac_en(True)
        return True

    @staticmethod
    def disable_power():
        PowerSupplies.tx_dac_en(False)
        return True

    def enable_tx(self):
        DevMem.set(self.GPIO_TX_DAC_CTRL_ADDR, self.DAC_TX_EN_MASK)
        return True

    def disable_tx(self):
        DevMem.clear(self.GPIO_TX_DAC_CTRL_ADDR, self.DAC_TX_EN_MASK)
        return True

    def assert_reset(self):
        DevMem.clear(self.GPIO_TX_DAC_CTRL_ADDR, self.DAC_RST_N_MASK)
        return True

    def deassert_reset(self):
        DevMem.set(self.GPIO_TX_DAC_CTRL_ADDR, self.DAC_RST_N_MASK)
        return True

    def read_reg(self, addr):
        # Write 16-bits (1-bit RW flag [1], 15-bit address), read 8-bit data
        rd_data = self.spi.read_data(0x8000 | addr, 16, 8)
        return rd_data & 0xFF

    def write_reg(self, addr, data):
        # Write 1-bit RW flag [0], 15-bit address, 8-bit data
        self.spi.write_data(((addr & 0x7FFF) << 8) | (data & 0xFF), 24)
        return True

    def initialise(self, test_mode=True):
        self.disable_tx()
        self.assert_reset()
        self.enable_power()
        self.deassert_reset()
        if not self.run_startup_sequence():
            return False
        if test_mode:
            if not self.setup_nco(nco_only_mode=True):
                return False
            self.enable_tx()
        return True

    def initialise_jesd204b(self, nlanes=1, interpolation=1):
        # Determine AD9162 interpolation value
        if interpolation == 1:
            interp_val = 0x0
        elif interpolation == 2:
            interp_val = 0x1
        elif interpolation == 3:
            interp_val = 0x2
        elif interpolation == 4:
            interp_val = 0x3
        elif interpolation == 6:
            interp_val = 0x4
        elif interpolation == 8:
            interp_val = 0x5
        elif interpolation == 12:
            interp_val = 0x6
        elif interpolation == 16:
            interp_val = 0x7
        elif interpolation == 24:
            interp_val = 0x8
        # Formulate lanes in use bitmask
        lanes_in_use = 0
        for i in range(nlanes):
            lanes_in_use |= (1 << i)
        # Power down PHYs not in use
        phy_pd_val = ~lanes_in_use & 0xFF
        self.write_reg(self.GENERAL_JRX_CTRL_0, 0x00)  # Ensure SERDES links are disabled before configuring them
        self.write_reg(self.JESD_IRQ_ENABLEA, 0xFF)  # Enable JESD204B interrupts
        self.write_reg(self.JESD_IRQ_ENABLEB, 0x01)  # Enable JESD204B interrupts
        for offset in range(8):
            self.write_reg(self.ECNT_CTRL_BASE + offset, 0x38)  # Enable SERDES error counters
        self.write_reg(self.INTERP_MODE, ((nlanes << 4) & 0xF0) | (interp_val & 0x0F))
        self.write_reg(self.DATAPATH_CFG, 0x10)  # Configure the datapath options
        self.write_reg(self.CDR_OPERATING_MODE_REG_0, 0x08)  # Configure CDR Block, see datasheet Table 20
        self.write_reg(self.REF_CLK_DIVIDER_LDO, 0x01)  # Set up SERDES PLL divider - divide by 2
        self.write_reg(self.PLL_REF_CLK_PD, 0x00)  # Set up the PLL reference clock rate - mult by 1
        self.write_reg(self.MASTER_PD, 0x00)  # Enable JESD204B block
        self.write_reg(self.CTRLREG0, 0x09)  # Soft reset JESD204B quad-byte deframer
        self.write_reg(self.ILS_SCR_L, 0x80)  # Enable scrambling
        self.write_reg(self.ILS_NP, 0x0F)  # Set the subclass type: 0b000 = Subclass 0, 0b001 = Subclass 1, NP = 16
        self.write_reg(self.ILS_S, 0x20)  # Set JESD204 version to B
        # Calculate checksum
        checksum = 0
        checksum += self.read_reg(self.ILS_DID)
        checksum += self.read_reg(self.ILS_BID)
        checksum += self.read_reg(self.ILS_LID0) & 0x1F
        checksum += (self.read_reg(self.ILS_SCR_L) >> 7) & 0x01
        checksum += self.read_reg(self.ILS_F)
        checksum += self.read_reg(self.ILS_K) & 0x1F
        checksum += self.read_reg(self.ILS_M)
        checksum += self.read_reg(self.ILS_CS_N) & 0x1F
        checksum += (self.read_reg(self.ILS_NP) >> 5) & 0x07
        checksum += self.read_reg(self.ILS_NP) & 0x1F
        checksum += (self.read_reg(self.ILS_S) >> 5) & 0x07
        checksum += self.read_reg(self.ILS_S) & 0x1F
        checksum += (self.read_reg(self.ILS_HD_CF) >> 7) & 0x01
        checksum %= 256
        self.write_reg(self.ILS_CHECKSUM, checksum)
        self.write_reg(self.CTRLREG0, 0x01)  # Bring JESD204B quad-byte deframer out of reset
        self.write_reg(self.PHY_PD, phy_pd_val)  # Set any bits to power down that lane
        self.write_reg(self.TERM_BLK1_CTRLREG0, 0x01)  # Calibrate PHY termination block 0 1 6 7
        self.write_reg(self.TERM_BLK2_CTRLREG0, 0x01)  # Calibrate PHY termination block 2 3 4 5
        self.write_reg(self.PRIVATE_REG_29E, 0x1F)  # Override defaults in the serdes pll settings
        self.write_reg(self.CDR_RESET, 0x00)  # Reset the CDR
        self.write_reg(self.CDR_RESET, 0x01)  # Enable the CDR
        self.write_reg(self.SYNTH_ENABLE_CNTRL, 0x05)  # Enable the SERDES PLL
        self.write_reg(self.SYNTH_ENABLE_CNTRL, 0x01)
        sleep(1)
        if not self.wait_pll_lock():
            print("ERROR: PLL lock failed")
            return False
        print("SERDES PLL locked")
        self.write_reg(self.GENERAL_JRX_CTRL_0, 0x01)  # Enable SERDES links
        cgs = self.read_reg(self.CODE_GRP_SYNC)
        if cgs != lanes_in_use:
            print("ERROR: JESD link failed to sync (CODE_GRP_SYNC 0x{:02x})".format(cgs))
            return False
        print("JESD204B Code Group Sync complete")
        fs = self.read_reg(self.FRAME_SYNC)
        if fs != lanes_in_use:
            print("ERROR: JESD link failed to sync (FRAME_SYNC 0x{:02x})".format(fs))
            return False
        print("JESD204B Frame Sync complete")
        gc = self.read_reg(self.GOOD_CHECKSUM)
        if gc != lanes_in_use:
            print("ERROR: JESD link failed to sync (GOOD_CHECKSUM 0x{:02x})".format(gc))
            return False
        print("JESD204B checksums good")
        ils = self.read_reg(self.INIT_LANE_SYNC)
        if ils != lanes_in_use:
            print("ERROR: JESD link failed to sync (INIT_LANE_SYNC 0x{:02x})".format(ils))
            return False
        print("JESD204B lane synchronisation complete")
        self.write_reg(self.IRQ_STATUS, 0x1F)  # Clear the interrupts
        self.write_reg(self.JESD_IRQ_STATUSA, 0xFF)  # Clear the serdes interrupts
        self.write_reg(self.JESD_IRQ_STATUSB, 0x01)  # Clear the serdes interrupts
        return True

    def disable(self):
        self.disable_tx()
        self.assert_reset()
        self.disable_power()

    def wait_dll_lock(self):
        locks = 0
        timeout_loops = 30
        while True:
            dll_status = self.read_reg(self.DLL_STATUS)
            #print("DLL Status: {:01x}".format(dll_status))
            if (dll_status & 0x3) == 0x1:
                locks += 1
                # Note: seeing lock on every cycle during PCB level test, consider reducing count
                # or reducing delay between checks so that we don't take 100 ms in this check
                if locks == 10:
                    return True
            else:
                locks = 0
                if timeout_loops == 0:
                    return False
                timeout_loops -= 1
            if (dll_status & 0x2) == 0x2:
                self.write_reg(self.DLL_STATUS, 0)
            sleep(0.01)  # Sleep for 10 ms

    def wait_pll_lock(self):
        locks = 0
        timeout_loops = 30
        while True:
            pll_status = self.read_reg(self.PLL_STATUS)
            if (pll_status & 0x1) == 0x1:
                locks += 1
                # Note: seeing lock on every cycle during PCB level test, consider reducing count
                # or reducing delay between checks so that we don't take 100 ms in this check
                if locks == 10:
                    return True
            else:
                locks = 0
                if timeout_loops == 0:
                    return False
                timeout_loops -= 1
            sleep(0.01)  # Sleep for 10 ms

    def run_startup_sequence(self):
        # DAC start-up sequence as per Table 42 of the AD9162 datasheet:
        # https://www.analog.com/media/en/technical-documentation/data-sheets/AD9161-9162.pdf
        # (skip first step; operating in 3-wire SPI mode)
        self.write_reg(self.PRIVATE_REG_D2, 0x52)
        self.write_reg(self.PRIVATE_REG_D2, 0xD2)
        self.write_reg(self.PRIVATE_REG_606, 0x02)
        self.write_reg(self.PRIVATE_REG_607, 0x00)
        self.write_reg(self.PRIVATE_REG_604, 0x01)
        sleep(0.001)
        # skip reading CHIP_TYPE, PROD_ID, PROD_GRAD, DEV_REVISION
        # Skip boot load test as it always seems to fail...
        val = self.read_reg(self.PRIVATE_REG_604)
        if (val & 0x02) == 0x02:
            print("Boot Load: success")
        else:
            print("Boot Load: ** FAIL **")
        self.write_reg(self.PRIVATE_REG_58, 0x03)
        self.write_reg(self.DLL_PD, 0x1E)
        self.write_reg(self.CLK_PD, 0x00)
        self.write_reg(self.ANA_DAC_BIAS_PD, 0x00)
        self.write_reg(self.IRQ_ENABLE, 0x0F)
        self.write_reg(self.PRIVATE_REG_9E, 0x85)
        self.write_reg(self.DLL_CTRL, 0xE9)
        if self.wait_dll_lock():
            self.write_reg(self.PRIVATE_REG_E8, 0x20)
            self.write_reg(self.DECODE_MODE, 0x00)
            print("DLL locked")
            return True
        else:
            print("ERROR: DLL lock failed")
            return False

    def set_frequency(self, frequency_Hz):
        val = self.read_reg(0x113)  # FTW request
        if val:
            print("ERROR: could not set DAC frequency")
            return False
        ftw = int(((frequency_Hz / self.fdac) * (2 ** 48)) + 0.5)
        # Write 6-byte FTW
        for i in range(6):
            self.write_reg(0x114 + i, ftw & 0xFF)
            ftw >>= 8

        self.write_reg(0x113, 0x01)  # FTW update
        self.write_reg(0x113, 0x00)  # FTW update
        return True

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude=0x40):
        self.write_reg(0x14E, (amplitude >> 8) & 0xFF)  # Amplitude MSBs
        self.write_reg(0x14F, amplitude & 0xFF)  # Amplitude LSBs
        self.amplitude = amplitude

    def set_att_dB(self, att_dB):
        ratio = 10 ** (att_dB / 20)
        self.set_amplitude(int(round(self.DAC_FULL_SCALE / ratio, 0)))
        return True

    def setup_nco(self, nco_only_mode, freq_megahertz=100, amplitude=0):
        if nco_only_mode:
            self.write_reg(self.INTERP_MODE, 0x80)
        self.write_reg(self.DATAPATH_CFG, 0x50)
        if nco_only_mode:
            self.write_reg(self.DIG_TEST, 0x02)
            self.set_amplitude(amplitude)
        return self.set_frequency(freq_megahertz * 1e6)

    def get_calibrated_amplitude(self, frequency_Hz):
        with open(self.CAL_DIR_NAME + self.CAL_FILE_NAME, mode='r') as csv_file:
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
    parser = argparse.ArgumentParser(description="Control the AD9162 DAC")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("-i", "--initialise",
                        help="Initialise the AD9162 TxDAC",
                        action="store_true")
    action.add_argument("-d", "--disable",
                        help="Disable the AD9162 TxDAC",
                        action="store_true")
    action.add_argument("-r", "--reg_test",
                        help="Run register test (don't initialise Tx)",
                        action="store_true")
    parser.add_argument("-f", "--frequency",
                        help="NCO Frequency in MHz")
    parser.add_argument("-a", "--amplitude",
                        help="Amplitude, 0 to 65,535")
    args = parser.parse_args()

    dac = AD9162()

    if args.initialise:
        dac.initialise()
        print("TxDAC Initialised")
        exit(1)
    elif args.disable:
        dac.disable()
        print("TxDAC Disabled")
        exit(1)
    elif args.reg_test:
        test_pass = True
        dac.assert_reset()
        dac.deassert_reset()
        val = dac.read_reg(dac.CDR_OPERATING_MODE_REG_0)
        if val == 0x28:
            print("CDR_OPERATING_MODE_REG_0 - got expected value (0x28)")
        else:
            print("CDR_OPERATING_MODE_REG_0 - got unexpected value (got {} expected 0x28)".format(val))
            test_pass = False
        val = dac.read_reg(dac.PHY_PRBS_TEST_THRESHOLD_LOBITS)
        if val == 0:
            print("PHY_PRBS_TEST_THRESHOLD_LOBITS - got expected value (0x00)")
        else:
            print("CDR_OPERATING_MODE_REG_0 - got unexpected value (got {} expected 0x00)".format(val))
            test_pass = False
        dac.write_reg(dac.PHY_PRBS_TEST_THRESHOLD_LOBITS, 0xAA)
        val = dac.read_reg(dac.PHY_PRBS_TEST_THRESHOLD_LOBITS)
        if val == 0xAA:
            print("PHY_PRBS_TEST_THRESHOLD_LOBITS - got expected value (0xAA)")
        else:
            print("CDR_OPERATING_MODE_REG_0 - got unexpected value (got {} expected 0xAA)".format(val))
            test_pass = False
        if test_pass:
            print("*** TEST PASSED ***")
        else:
            print("*** TEST FAILED ***")
        exit(1)

    if args.frequency:
        freq_MHz = int(args.frequency)
        print("Set TxDAC to {} MHz".format(freq_MHz))
        dac.set_frequency(freq_MHz * 1e6)
    if args.amplitude:
        if args.amplitude.startswith("0x"):
            amplitude = int(args.amplitude, 16)
        else:
            amplitude = int(args.amplitude)
        print("Set TxDAC to Amplitude 0x{:04x}".format(amplitude))
        dac.set_amplitude(amplitude)
