from dev_mem import *

REG_GPIO_0_ADDRESS = 0x4000A000
REG_GPIO_0_POWER_KILL_BIT = 0

# Perform read-modify-write operation on the GPIO 0 register
val = DevMem.read(REG_GPIO_0_ADDRESS)
val &= (~(1 << REG_GPIO_0_POWER_KILL_BIT))
DevMem.write(REG_GPIO_0_ADDRESS, val)
