#!/usr/bin/env python3

from enum import Enum

from datetime import datetime
from devmem import DevMem
from time import sleep


class JESD204BDirection(Enum):
    RX = 0,
    TX = 1,
    TXRX = 2


class JESD204B:
    REG_BASE_RX_CORE = 0x40005000  # Tx/Rx for MB/HB
    REG_BASE_RX_PHY = 0x40006000   # Tx/Rx for MB/HB
    REG_BASE_TX_CORE = 0x40009000  # N/A for MB/HB
    REG_BASE_TX_PHY = 0x4001E000   # N/A for MB/HB

    CORE_ADDR_RESET = 0x004
    CORE_ADDR_SCRAMBLING = 0x00C
    CORE_ADDR_SYSREF_HANDLING = 0x010
    CORE_ADDR_OCTETS_PER_FRAME = 0x020
    CORE_ADDR_SUBCLASS = 0x02C
    CORE_ADDR_LANES_IN_USE = 0x028
    CORE_ADDR_LANE_0_ILA_CONFIG_DATA = 0x800
    ILA_CONFIG_DATA_SIZE_PER_LANE = 0x40

    PHY_ADDR_PLL_STATUS = 0x080

    def initialise(self, direction=JESD204BDirection.RX, nlanes=1, octets_per_frame=4):
        print("Configure SoC JESD204B Core: {}".format(direction))
        self.set_scrambling(1, direction)
        self.set_subclass(0, direction)
        self.set_sysref_handling(0x00, direction)  # "Sysref Always" off, sysref not required on re-sync
        self.set_octets_per_frame(octets_per_frame, direction)
        for lane in range(nlanes):
            self.set_ila_config(lane=lane, addr=4, value=0x000F0F01, direction=direction)
            self.set_ila_config(lane=lane, addr=5, value=0x00010000, direction=direction)
        self.set_number_of_lanes(nlanes, direction)
        self.set_reset(0x3, direction)
        self.set_reset(0x1, direction)
        while True:
            rst = self.get_reset(direction)
            if (rst & 0x1) == 0:
                break
            sleep(0.1)
        print("Wait for SoC JESD204B PLL lock... ", end="", flush=True)
        if not self.wait_pll_lock(direction):
            print("FAIL")
            return False
        print("OK")
        return True

    def set_scrambling(self, value, direction=JESD204BDirection.RX):
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_SCRAMBLING, value)

    def set_sysref_handling(self, value, direction=JESD204BDirection.RX):
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_SYSREF_HANDLING, value)

    def set_octets_per_frame(self, octets, direction=JESD204BDirection.RX):
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_OCTETS_PER_FRAME, octets - 1)

    def set_subclass(self, value, direction=JESD204BDirection.RX):
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_SUBCLASS, value)

    def set_number_of_lanes(self, nlanes, direction=JESD204BDirection.RX):
        lanes_in_use = 0
        for i in range(nlanes):
            lanes_in_use |= (1 << i)
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_LANES_IN_USE, lanes_in_use)

    def set_ila_config(self, lane, addr, value, direction=JESD204BDirection.RX):
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_LANE_0_ILA_CONFIG_DATA +
                     (lane * self.ILA_CONFIG_DATA_SIZE_PER_LANE) + (addr * 4), value)

    def set_reset(self, value, direction=JESD204BDirection.RX):
        DevMem.write(self.core_base(direction) + self.CORE_ADDR_RESET, value)

    def get_reset(self, direction=JESD204BDirection.RX):
        return DevMem.read(self.core_base(direction) + self.CORE_ADDR_RESET)

    def wait_pll_lock(self, direction=JESD204BDirection.RX):
        locks = 0
        timeout_loops = 30
        while True:
            pll_status = DevMem.read(self.phy_base(direction) + self.PHY_ADDR_PLL_STATUS)
            #print("PLL Status: {:01x}".format(pll_status))
            if ((pll_status >> 2) & 0x1) == 0x0:
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

    def core_base(self, direction):
        if direction == JESD204BDirection.TX:
            return self.REG_BASE_TX_CORE
        else:
            return self.REG_BASE_RX_CORE

    def phy_base(self, direction):
        if direction == JESD204BDirection.TX:
            return self.REG_BASE_TX_PHY
        else:
            return self.REG_BASE_RX_PHY
