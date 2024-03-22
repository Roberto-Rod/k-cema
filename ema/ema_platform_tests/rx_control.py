#!/usr/bin/env python3
from devmem import *
import argparse
import os

from band import *


class RxControl:
    MAX_COMMAND_ATTEMPTS = 5
    REG_RX_CONTROL = 0x40004000
    RX_CONTROL_FAST_DETECT_MASK = 0x00000004
    CENTRE_FREQ_MHZ_MIN = 45
    CENTRE_FREQ_MHZ_MAX = 495

    def __init__(self):
        if os.path.exists("/run/media/mmcblk0p2/test/rftool"):
            self.rf_tool = "/run/media/mmcblk0p2/test/rftool"
        else:
            self.rf_tool = "/tmp/test/rftool"
        self.synth_nr = 1
        self.set_active_synth(self.synth_nr)

    @staticmethod
    def fast_detect():
        return (DevMem.read(RxControl.REG_RX_CONTROL) & RxControl.RX_CONTROL_FAST_DETECT_MASK) != 0

    def get_mixer_level_mv(self):
        attempts = 0
        while attempts < 5:
            resp = os.popen("{} -m".format(self.rf_tool)).read()
            try:
                return int(resp.split(" ")[2])
            except ValueError as e:
                attempts += 1
        return 0

    def get_mixer_level_dbm(self):
        # 1650 mV = -20 dBm
        # 43 dB / mV slope
        mv = self.get_mixer_level_mv()
        return -20.0 + ((mv - 1650.0) / 43)

    def set_active_synth(self, synth_nr):
        if synth_nr == 1 or synth_nr == 2:
            self.synth_nr = synth_nr
            command = "{} -S {}".format(self.rf_tool, synth_nr)
            expected_response = "Synth {} selected".format(synth_nr)
            return self.send_command(command, expected_response)
        else:
            return False

    def set_lna_enable(self, enable, band=Band.LOW):
        if isinstance(enable, bool):
            if (enable and band == Band.LOW) or (not enable and band != Band.LOW):
                command = "{} -L 1".format(self.rf_tool)
                expected_response = "LNA enabled"
            else:
                command = "{} -L 0".format(self.rf_tool)
                expected_response = "LNA bypassed"
            return self.send_command(command, expected_response)
        return False

    def set_rf_attenuator(self, att):
        try:
            att_f = float(att)
            att_f = round(att_f * 2.0) / 2.0
            if att_f < 0.0 or att_f > 31.5:
                return False
            command = "{} -R {:.1f}".format(self.rf_tool, att_f)
            expected_response = "RF attenuator set to {:.1f} dB".format(att_f)
            return self.send_command(command, expected_response)
        except ValueError as e:
            print("ERROR in set_rf_attenuator: {}".format(e))
        return False

    def set_if_attenuator(self, att):
        try:
            att_f = float(att)
            att_f = round(att_f * 2.0) / 2.0
            if att_f < 0.0 or att_f > 31.5:
                return False
            command = "{} -I {:.1f}".format(self.rf_tool, att_f)
            expected_response = "IF attenuator set to {:.1f} dB".format(att_f)
            return self.send_command(command, expected_response)
        except ValueError as e:
            print("ERROR in set_if_attenuator: {}".format(e))
        return False

    def set_preselector(self, preselector):
        try:
            p = int(preselector)
            if p < 0 or p > 7:
                return False
            command = "{} -P {}".format(self.rf_tool, p)
            expected_response = "Pre-selector band {} selected".format(p)
            return self.send_command(command, expected_response)
        except ValueError as e:
            print("ERROR in set_preselector: {}".format(e))
        return False

    def is_synth_locked(self):
        command = "{} -s".format(self.rf_tool)
        response = os.popen(command).read().splitlines()
        # Check lock status of the active synth
        if len(response) >= self.synth_nr:
            fields = response[self.synth_nr-1].split(" ")
            if len(fields) == 3:
                if fields[2] == "locked":
                    return True
        return False

    def initialise_synths(self):
        ok = True
        for synth_nr in range(1, 3):
            ok = ok and self.write_synth_reg(synth_nr, 0x00580005)
            ok = ok and self.write_synth_reg(synth_nr, 0x00A2863C)
            ok = ok and self.write_synth_reg(synth_nr, 0x00800003)
            ok = ok and self.write_synth_reg(synth_nr, 0x7A007E42)
            ok = ok and self.write_synth_reg(synth_nr, 0x0800A001)
            ok = ok and self.write_synth_reg(synth_nr, 0x00000E78)
        return ok

    def set_centre_frequency_mhz(self, freq_mhz):
        try:
            if freq_mhz < self.CENTRE_FREQ_MHZ_MIN or freq_mhz > self.CENTRE_FREQ_MHZ_MAX:
                return False
            int_val = int(round((freq_mhz / 5)) + 113)
            reg_val = 0x00000E78 | ((int_val << 15) & 0x7FFF8000)
            return self.write_synth_reg(self.synth_nr, reg_val)
        except ValueError as e:
            print("ERROR in set_centre_frequency_mhz: {}".format(e))

    def write_synth_reg(self, synth_nr, reg_val):
        command = "{} -D {} -Y 0x{:08x}".format(self.rf_tool, synth_nr, reg_val)
        expected_response = "Synth {} written: 0x{:08x}".format(synth_nr, reg_val)
        return self.send_command(command, expected_response)

    def send_command(self, command, expected_response=None):
        attempts = 0
        while attempts < self.MAX_COMMAND_ATTEMPTS:
            response = os.popen(command).read()
            if expected_response is None:
                return True
            else:
                if response.strip() == expected_response.strip():
                    return True
            attempts += 1
        return False


def print_status(ok):
    if ok:
        print("OK")
    else:
        print("FAIL")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control timing register")
    parser.add_argument("-t", "--initialise", help="Initialise the synthesisers", action="store_true")
    parser.add_argument("-m", "--get_mixer_level", help="Get mixer level (dBm)", action="store_true")
    parser.add_argument("-d", "--get_fast_detect", help="Get IF ADC Fast Detect state", action="store_true")
    parser.add_argument("-k", "--lock_status", help="Get lock status of active synth", action="store_true")
    parser.add_argument("-s", "--synth_nr", help="Set selected synthesiser (1 or 2)", type=int)
    parser.add_argument("-l", "--lna_enable", help="Set enabled state of LNA (0 or 1)", type=int)
    parser.add_argument("-r", "--rf_att", help="Set RF attenuator value in dB (0 to 31.5)", type=float)
    parser.add_argument("-i", "--if_att", help="Set IF attenuator value in dB (0 to 31.5)", type=float)
    parser.add_argument("-p", "--preselector", help="Set preselector (0 to 7, 7=isolation)", type=int)
    parser.add_argument("-f", "--frequency", help="Set centre frequency of active synth in MHz", type=int)
    args = parser.parse_args()
    r = RxControl()
    if args.initialise:
        print("Initialise synths: ", end="")
        print_status(r.initialise_synths())
    if args.frequency is not None:
        print("Set synth {} centre frequency to {} MHz: ".format(r.synth_nr, args.frequency), end="")
        print_status(r.set_centre_frequency_mhz(args.frequency))
    if args.get_mixer_level:
        print("Mixer level: {} mV".format(r.get_mixer_level_mv()))
        print("Mixer level: {:.2f} dBm".format(r.get_mixer_level_dbm()))
    if args.get_fast_detect:
        print("IF ADC Fast Detect: {}".format(r.fast_detect()))
    if args.lock_status:
        print("Synth {} lock status: {}".format(r.synth_nr, r.is_synth_locked()))
    if args.synth_nr is not None:
        print("Set active synth to {}: ".format(args.synth_nr), end="")
        print_status(r.set_active_synth(args.synth_nr))
    if args.lna_enable is not None:
        en = None
        if args.lna_enable == 0:
            en = False
        elif args.lna_enable == 1:
            en = True
        print("Set LNA enable to {}: ".format(en), end="")
        print_status(r.set_lna_enable(en))
    if args.rf_att is not None:
        print("Set RF attenuator to {} dB: ".format(args.rf_att), end="")
        print_status(r.set_rf_attenuator(args.rf_att))
    if args.if_att is not None:
        print("Set IF attenuator to {} dB: ".format(args.if_att), end="")
        print_status(r.set_if_attenuator(args.if_att))
    if args.preselector is not None:
        print("Set preselector to {}: ".format(args.preselector), end="")
        print_status(r.set_preselector(args.preselector))
