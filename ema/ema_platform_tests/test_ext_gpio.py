#!/usr/bin/env python3
from devmem import *
from band import *
from ltc2991 import *
from pl_spi import *
from power_supplies import *
from time import sleep
import sys

BIT_ADC = 0x00000000 # Dummy value to identify BIT ADC as an input
SPI_IF_ADC_BASE   = 0x40002000
SPI_DAC_READBACK  = 0x40071008
GPIO_TEST_0_BASE  = 0x40070000
GPIO_TEST_2_BASE  = 0x40070008
GPIO_TEST_1_BASE  = 0x40071000
GPIO_1_0_BASE     = 0x40014000
GPIO_1_1_BASE     = 0x40014008
GPIO_TX_CTRL_BASE = 0x40015000
GPIO_DATA_OFFSET  = 0
GPIO_DIR_OFFSET   = 4

TEST_LOOPS = {
    Band.LOW: [
        # Connector, Pin 1, Pin 2, Reg. Addr., Bit 1, Bit 2
        ["J5", "A2", "A3", GPIO_TEST_1_BASE, 11, GPIO_TEST_1_BASE, 12],
        ["J5", "A4", "A5", GPIO_TEST_1_BASE, 13, GPIO_TEST_1_BASE, 14],
        ["J5", "A6", "A7", GPIO_TEST_1_BASE, 5, GPIO_TEST_0_BASE, 26],
        ["J5", "A9", "A10", GPIO_TEST_1_BASE, 18, GPIO_1_0_BASE, 6],
        ["J5", "A11", "A12", GPIO_1_0_BASE, 7, GPIO_TEST_0_BASE, 20],
        ["J5", "A13", "A14", GPIO_TEST_0_BASE, 22, GPIO_TEST_0_BASE, 24],
        ["J5", "A15", "A16", GPIO_TEST_0_BASE, 19, GPIO_TEST_1_BASE, 21],
        ["J5", "A17", "A18", GPIO_TEST_1_BASE, 22, GPIO_TEST_1_BASE, 23],
        ["J5", "B3", "B4", GPIO_TEST_1_BASE, 9, GPIO_TEST_1_BASE, 10],
        ["J5", "B5", "B6", GPIO_TEST_1_BASE, 17, GPIO_TEST_1_BASE, 16],
        ["J5", "B10", "B11", GPIO_TEST_1_BASE, 19, GPIO_TEST_0_BASE, 31],
        ["J5", "B13", "B14", GPIO_TEST_0_BASE, 21, GPIO_TEST_0_BASE, 23],
        ["J5", "C2", "C3", GPIO_TEST_1_BASE, 4, GPIO_TEST_0_BASE, 28],
        ["J5", "C5", "C6", GPIO_TEST_0_BASE, 29, GPIO_TEST_1_BASE, 6],
        ["J5", "C7", "C8", GPIO_TEST_0_BASE, 27, GPIO_TEST_1_BASE, 0],
        ["J5", "C9", "C10", GPIO_TEST_0_BASE, 25, GPIO_TEST_1_BASE, 29],
        ["J5", "C11", "C12", GPIO_TEST_0_BASE, 6, GPIO_TEST_0_BASE, 8],
        ["J5", "C13", "C14", GPIO_TEST_1_BASE, 26, GPIO_TEST_1_BASE, 28],
        ["J5", "C15", "C16", GPIO_TEST_0_BASE, 10, GPIO_TEST_0_BASE, 12],
        ["J5", "C17", "C18", GPIO_TEST_0_BASE, 14, GPIO_TEST_0_BASE, 16],
        ["J5", "C19", "BIT.V3", GPIO_TEST_0_BASE, 18, BIT_ADC, 2],
        ["J5", "D3", "D4", GPIO_TEST_1_BASE, 3, GPIO_TEST_1_BASE, 8],
        ["J5", "D5", "D6", GPIO_TEST_1_BASE, 7, GPIO_TEST_1_BASE, 15],
        ["J5", "D7", "D8", GPIO_TEST_1_BASE, 2, GPIO_TEST_1_BASE, 1],
        ["J5", "D9", "D12", GPIO_TEST_0_BASE, 30, GPIO_TEST_0_BASE, 7],
        ["J5", "D13", "D14", GPIO_TEST_0_BASE, 9, GPIO_TEST_1_BASE, 27],
        ["J5", "D16", "D17", GPIO_TEST_0_BASE, 11, GPIO_TEST_0_BASE, 13],
        ["J5", "D18", "D19", GPIO_TEST_0_BASE, 15, GPIO_TEST_0_BASE, 17],
        ["P2", "4/3", "1/2", GPIO_TEST_0_BASE, 5, GPIO_TEST_0_BASE, 4],
        ["P2", "5", "8", GPIO_TEST_0_BASE, 3, GPIO_TEST_1_BASE, 24],
        ["P2", "6", "10", GPIO_TEST_0_BASE, 2, GPIO_TEST_0_BASE, 0],
        ["P2", "7", "11", GPIO_TEST_0_BASE, 1, GPIO_TEST_1_BASE, 25],
        ["J4", "18", "22", GPIO_TEST_1_BASE, 20, GPIO_TEST_1_BASE, 30],
        ["J4", "26", "30", GPIO_1_1_BASE, 16, GPIO_1_1_BASE, 18]
    ],
    Band.MID_HIGH: [
        # Connector, Pin 1, Pin 2, Reg. Addr., Bit 1, Bit 2
        ["P5", "A13", "A14", GPIO_TEST_0_BASE, 10, GPIO_TEST_0_BASE, 11],
        ["P5", "A15", "A16", GPIO_TEST_0_BASE, 12, GPIO_TEST_0_BASE, 13],
        ["P5", "A17", "A18", GPIO_TEST_0_BASE, 14, GPIO_TEST_0_BASE, 15],
        ["P5", "A19", "A20", GPIO_TEST_0_BASE, 16, GPIO_TEST_0_BASE, 17],
        ["P5", "A21", "A22", GPIO_TEST_0_BASE, 18, GPIO_TEST_0_BASE, 19],
        ["P5", "A25", "A26", GPIO_TEST_0_BASE, 20, GPIO_TEST_0_BASE, 21],
        ["P5", "A27", "A28", GPIO_TEST_0_BASE, 22, GPIO_TEST_0_BASE, 23],
        ["J5", "A29", "BIT.V5", GPIO_TEST_0_BASE, 24, BIT_ADC, 4],
        ["P5", "B3", "B4", GPIO_TEST_1_BASE, 15, GPIO_TEST_1_BASE, 0],
        ["P5", "B5", "B6", GPIO_TEST_1_BASE, 1, GPIO_TEST_1_BASE, 2],
        ["P5", "B8", "B9", GPIO_TEST_0_BASE, 6, GPIO_TEST_0_BASE, 7],
        ["P5", "B10", "B11", GPIO_TEST_0_BASE, 8, GPIO_TEST_0_BASE, 9],
        ["P5", "B17", "B20", GPIO_TEST_2_BASE, 1, GPIO_1_0_BASE, 31],      # SYNCIN_N / SYNCOUT_N (PGD_ADC_2V5_A)
        ["P5", "B18", "B21", GPIO_TEST_2_BASE, 0, GPIO_TEST_2_BASE, 2],    # SYNCIN_P / SYNCOUT_P
        ["P5", "B29", "B30", GPIO_TEST_2_BASE, 4, GPIO_TEST_2_BASE, 5],    # xcvr_gpio[8] / xcvr_gpio[9]
        ["P5", "C11", "C12", GPIO_TX_CTRL_BASE, 0, GPIO_TEST_2_BASE, 13],  # tx_dac_rst_n / tx_dac_irq_n
        ["P5", "C16", "C15", GPIO_TX_CTRL_BASE, 1, GPIO_TEST_2_BASE, 12],  # tx_dac_tx_en / xcvr_rx_en
        ["P5", "C19", "C20", GPIO_TEST_2_BASE, 6, GPIO_TEST_2_BASE, 7],    # xcvr_gpio[10] / xcvr_gpio[11]
        ["P5", "C23", "C24", GPIO_TEST_2_BASE, 8, GPIO_TEST_2_BASE, 9],    # xcvr_gpio[12] / xcvr_gpio[13]
        ["P5", "C27", "C28", GPIO_TEST_2_BASE, 10, GPIO_TEST_2_BASE, 11],  # xcvr_gpio[14] / xcvr_gpio[15]
        ["P2", "4/3", "1/2", GPIO_TEST_0_BASE, 5, GPIO_TEST_0_BASE, 4],
        ["P2", "5", "8", GPIO_TEST_0_BASE, 3, GPIO_TEST_1_BASE, 24],
        ["P2", "6", "10", GPIO_TEST_0_BASE, 2, GPIO_TEST_0_BASE, 0],
        ["P2", "7", "11", GPIO_TEST_0_BASE, 1, GPIO_TEST_1_BASE, 25],
        ["J4", "18", "22", GPIO_TEST_1_BASE, 20, GPIO_TEST_1_BASE, 30],
        ["J4", "26", "30", GPIO_1_1_BASE, 16, GPIO_1_1_BASE, 18]
]
}


def run_test(band):
    '''
    Test the external GPIO loopbacks on NTM Digital Boards including those on the RF Daughter Board connector
    and those on the IPAM connector. The loopback board must be fitted (part of the KT-000-0161-00 test jig)
    and the IPAM loopback cable must be fitted. All pins are treated as GPIO and this function only works
    with the EMA FPGA Test Image.
    :param band: the band the NTM under test is associated with must be Band.LOW or Band.MID_HIGH
    :return: True if all tests pass, otherwise False
    '''
    ok = True
    print("")
    print("test_ext_gpio")
    print("-------------")
    initialise(band)
    for loop in TEST_LOOPS[band]:
        print("Test GPIO loopback on {}, pin {} to {}: ".format(loop[0], loop[1], loop[2]), end="", flush=True)
        if test_loop(loop[3], loop[4], loop[5], loop[6]):
            print("OK")
        else:
            print("FAIL")
            ok = False
    if band == Band.MID_HIGH:
        print("Test SPI loopback on P5 (B23 to B24, B25 to B26, B27 to B28): ", end="", flush=True)
        if not test_spi_loopback(0xAA):
            ok = False
        if not test_spi_loopback(0x55):
            ok = False
        if not test_spi_loopback(0xAA):
            ok = False
        if ok:
            print("OK")
        else:
            print("FAIL")

    PowerSupplies.disable_all()
    return ok


def test_loop(base_addr1, bit1, base_addr2, bit2):
    ok = True
    bit1_mask = (1 << bit1)
    bit2_mask = (1 << bit2)
    # Set bit 1 to output
    DevMem.clear(base_addr1 + GPIO_DIR_OFFSET, bit1_mask)
    # Set bit 2 to input
    if base_addr2 != BIT_ADC:
        DevMem.set(base_addr2 + GPIO_DIR_OFFSET, bit2_mask)
    # Drive bit 1 high
    DevMem.set(base_addr1 + GPIO_DATA_OFFSET, bit1_mask)
    # Read bit 2
    if base_addr2 != BIT_ADC:
        if DevMem.read(base_addr2 + GPIO_DATA_OFFSET) & bit2_mask != bit2_mask:
            ok = False
    else:
        ltc = LTC2991(1, 4)
        sleep(0.05)
        if (ltc.read_channel_volts(bit2) * 3.7) < 1.0:
            ok = False
    # Drive bit 1 low
    DevMem.clear(base_addr1 + GPIO_DATA_OFFSET, bit1_mask)
    # Read bit 2
    if base_addr2 != BIT_ADC:
        if DevMem.read(base_addr2 + GPIO_DATA_OFFSET) & bit2_mask != 0:
            ok = False
    else:
        ltc = LTC2991(1, 4)
        sleep(0.05)
        if (ltc.read_channel_volts(bit2) * 3.7) > 1.0:
            ok = False
    return ok


def test_spi_loopback(pattern):
    spi = PLSPI(SPI_IF_ADC_BASE)
    spi.write_data(pattern, 8)
    readback = DevMem.read(SPI_DAC_READBACK)
    return readback == pattern


def initialise(band):
    # Set all GPIO to outputs and drive 0 so there is no contention but any shorts to
    # other pins being tested will be detected as a failure
    DevMem.write(GPIO_TEST_0_BASE + GPIO_DATA_OFFSET, 0x00000000)
    DevMem.write(GPIO_TEST_1_BASE + GPIO_DATA_OFFSET, 0x00000000)
    DevMem.write(GPIO_TEST_0_BASE + GPIO_DIR_OFFSET,  0x00000000)
    DevMem.write(GPIO_TEST_1_BASE + GPIO_DIR_OFFSET,  0x00000000)
    # Enable +5V5 rail so that BIT ADC on the RF test board can be read
    PowerSupplies.disable_all()
    PowerSupplies.rail_5v5_en(True)


if __name__ == "__main__":
    if run_test(get_band_opt(sys.argv, ntm_digital=True)):
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
