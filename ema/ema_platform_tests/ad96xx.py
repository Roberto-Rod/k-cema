#!/usr/bin/env python3
import argparse
import os


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


class AD96xx:
    ADC_TOOL = "./adctool"
    ADC_TRIM = "./adctrim"

    @staticmethod
    def get_device_info():
        cmd = "{} -i".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        device_info = {}
        for r in resp:
            r = r.split(":")
            if len(r) >= 2:
                device_info[r[0]] = r[1].lstrip()
        return device_info

    @staticmethod
    def reset():
        cmd = "{} -R".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if r == "ADC initialised":
                return True
            else:
                return False
        return False

    def set_fast_detect_threshold(val):
        msb = (val >> 8) & 0xFF
        lsb = val & 0xFF
        cmds = ["{} 0x247 0x{:02x}".format(AD96xx.ADC_TOOL, lsb),
                "{} 0x248 0x{:02x}".format(AD96xx.ADC_TOOL, msb),
                "{} 0x249 0x{:02x}".format(AD96xx.ADC_TOOL, lsb),
                "{} 0x24A 0x{:02x}".format(AD96xx.ADC_TOOL, msb)]
        for cmd in cmds:
            # Read response so that command completes before returning
            resp = os.popen(cmd).read()
        return True

    @staticmethod
    def link_up():
        cmd = "{} -L 1".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read()
        if resp.startswith("ADC link up"):
            return True
        return False

    @staticmethod
    def trigger_sysref():
        cmd = "{} -S".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read()
        if resp.startswith("JESD204B SysRef triggered"):
            return True
        return False

    @staticmethod
    def is_input_clock_detected():
        cmd = "{} -l".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if remove_prefix(r, "ADC Input clock is ") == "detected":
                return True
        return False

    @staticmethod
    def is_adc_pll_locked():
        cmd = "{} -l".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if remove_prefix(r, "ADC PLL is ") == "locked":
                return True
        return False

    @staticmethod
    def is_jesd204b_pll_locked():
        cmd = "{} -l".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if remove_prefix(r, "JESD204B PLL is ") == "locked":
                return True
        return False

    @staticmethod
    def is_jesd204b_lane_synchronised():
        cmd = "{} -l".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if remove_prefix(r, "JESD204B lane is ") == "synchronised":
                return True
        return False

    @staticmethod
    def is_jesd204b_link_synchronised():
        cmd = "{} -l".format(AD96xx.ADC_TOOL)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if remove_prefix(r, "JESD204B link is ") == "synchronised":
                return True
        return False

    @staticmethod
    def set_adc_trim_midscale():
        cmd = "{} 0x800".format(AD96xx.ADC_TRIM)
        resp = os.popen(cmd).read().split("\n")
        for r in resp:
            if r.strip() == "OK - set ADC Trim DAC to 0x0800":
                return True
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control timing register")
    parser.add_argument("-f", "--fast_detect", help="Set fast detect threshold", type=int)
    args = parser.parse_args()
    print("Device Info: {}".format(AD96xx.get_device_info()))
    print("is_input_clock_detected: {}".format(AD96xx.is_input_clock_detected()))
    print("is_adc_pll_locked: {}".format(AD96xx.is_adc_pll_locked()))
    print("is_jesd204b_pll_locked: {}".format(AD96xx.is_jesd204b_pll_locked()))
    print("is_jesd204b_lane_synchronised: {}".format(AD96xx.is_jesd204b_lane_synchronised()))
    print("is_jesd204b_link_synchronised: {}".format(AD96xx.is_jesd204b_link_synchronised()))
    if args.fast_detect is not None:
        print("Set fast detect threshold to: 0x{:04x}".format(args.fast_detect))
        AD96xx.set_fast_detect_threshold(args.fast_detect)
