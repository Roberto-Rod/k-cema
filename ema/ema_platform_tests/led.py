#!/usr/bin/env python3
from devmem import *
from enum import Enum


class LEDColour(Enum):
    GREEN = 0,
    YELLOW = 1,
    RED = 2


class LED:
    BASE_ADDR = {LEDColour.GREEN: 0x40030000, LEDColour.YELLOW: 0x40030008, LEDColour.RED: 0x40030010}

    @staticmethod
    def on(LEDColour):
        DevMem.write(LED.BASE_ADDR[LEDColour] + 0, 0xFFFFFFFF)
        DevMem.write(LED.BASE_ADDR[LEDColour] + 4, 0xFFFFFFFF)

    @staticmethod
    def off(LEDColour):
        DevMem.write(LED.BASE_ADDR[LEDColour] + 0, 0x00000000)
        DevMem.write(LED.BASE_ADDR[LEDColour] + 4, 0x00000000)

    @staticmethod
    def all_off():
        for c in LEDColour:
            LED.off(c)


if __name__ == "__main__":
    print("LED Test")
    for i in range(20):
        LED.on(LEDColour.GREEN)
        LED.off(LEDColour.YELLOW)
        LED.on(LEDColour.RED)
        LED.off(LEDColour.GREEN)
        LED.on(LEDColour.YELLOW)
        LED.off(LEDColour.RED)
