from dev_mem import *
import time

GPIO0_REG_ADDRESS = 0x4000A000
GPIO0_PTP_PHY_RESET_N_BIT = 0x8

reg_val = DevMem.read(GPIO0_REG_ADDRESS)
reg_val &= (~GPIO0_PTP_PHY_RESET_N_BIT)
DevMem.write(GPIO0_REG_ADDRESS, reg_val)
time.sleep(0.1)
reg_val |= GPIO0_PTP_PHY_RESET_N_BIT
DevMem.write(GPIO0_REG_ADDRESS, reg_val)
