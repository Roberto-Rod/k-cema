from dev_mem import *

REG_GPIO_0_ADDRESS = 0x4000A000
REG_GPIO_0_POWER_OFF_OVR_BIT = 1


# Perform read-modify-write operation on the GPIO 0 register
def set_power_off_ovr(set_state=False):
    reg_val = DevMem.read(REG_GPIO_0_ADDRESS)
    if set_state:
        reg_val |= (1 << REG_GPIO_0_POWER_OFF_OVR_BIT)
    else:
        reg_val &= (~(1 << REG_GPIO_0_POWER_OFF_OVR_BIT))
    DevMem.write(REG_GPIO_0_ADDRESS, reg_val)
