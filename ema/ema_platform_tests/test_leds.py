#!/usr/bin/env python3
from led import *


def run_test():
    print("")
    print("test_leds")
    print("---------")
    LED.all_off()
    LED.on(LEDColour.GREEN)
    if input("Confirm that GREEN LED is on and no other LEDs are on? (y/n)") != "y":
        return False
    LED.all_off()
    LED.on(LEDColour.YELLOW)
    if input("Confirm that YELLOW LED is on and no other LEDs are on? (y/n)") != "y":
        return False
    LED.all_off()
    LED.on(LEDColour.RED)
    if input("Confirm that RED LED is on and no other LEDs are on? (y/n)") != "y":
        return False
    return True


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
    LED.all_off()