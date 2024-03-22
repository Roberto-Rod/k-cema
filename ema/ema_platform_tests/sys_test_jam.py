#!/usr/bin/env python3
from dds import *
from band import *
from fans import *
from ipam import *

from sys_test_full_power_tone import *
from sys_test_initialise import *
from sys_test_terminate import *
from sys_test_ipam_set_mute import *

import argparse
import math


# Class provided to configure the jamming engine to run at full power
class SysTestJam:
    JAM_ENGINE_CTRL = 0x40084004
    JAM_ENGINE_START_LINE = 0x40084008
    JAM_ENGINE_END_LINE = 0x4008400C
    JAM_ENGINE_LINE_BASE = 0x400C0000
    DDS_DAC_FREQ_HZ = 3240e6
    DDS_SYNC_FREQ_HZ = DDS_DAC_FREQ_HZ / 24
    LINE_OFFSET_CTRL = 0 * 4
    LINE_OFFSET_FTW = 1 * 4
    LINE_OFFSET_DFTW = 2 * 4
    LINE_OFFSET_POW_ASF = 3 * 4
    LINE_OFFSET_DUR = 4 * 4
    LINE_SIZE_WORDS = 5
    LINE_SIZE_BYTES = LINE_SIZE_WORDS * 4
    FREQ_MIN_MHZ = 20
    FREQ_MAX_MHZ = 6000
    SWEEP_MIN_NS = 200  # 200 ns
    SWEEP_MAX_NS = 100e6  # 100 ms
    REPEAT_MAX = 63

    def __init__(self, verbose=False):
        self.fpt = SysTestFullPowerTone()
        self.init = SysTestInitialise()
        self.term = SysTestTerminate()
        self.fans = Fans()
        # Get IPAM band if IPAM is already up
        if IPAM.wait_comms_good(0.1):
            self.band = IPAM.get_rf_band()
        else:
            self.band = Band.UNKNOWN
        self.dds = DDS()
        self.error_msg = ""
        self.verbose = verbose

    def initialise(self, rx_en=False):
        self.terminate()
        ok, error_msg = self.init.init(sweep_mode=True, rx_en=rx_en)
        if ok:
            self.band = IPAM.get_rf_band()
        else:
            print(error_msg)
        return ok

    def terminate(self):
        self.stop_jamming()
        ok, error_msg = self.term.terminate()
        if not ok:
            print(error_msg)
        return ok

    def force_fans(self):
        # Set fans to full by setting temperature to 100 °C
        self.fans.set_temperature(100)
        return True

    def start_jamming(self):
        if self.verbose:
            print("Start jamming engine: {} lines". format(self.get_nr_lines()))
        # Start jamming engine
        DevMem.write(self.JAM_ENGINE_CTRL, 0x0)
        # Reset IPAM BIT flags
        IPAM.reset_bit_flags()
        # Unmute IPAM
        IPAM.force_mute(False)
        # Set fans to full by setting temperature to 100 °C
        self.fans.set_temperature(100)
        return True

    def stop_jamming(self, no_clear=False, fans_on=False):
        if self.verbose:
            print("Stop jamming engine")
        # Mute IPAM
        IPAM.force_mute(True)
        # Stop jamming engine
        DevMem.write(self.JAM_ENGINE_CTRL, 0x1)
        if not fans_on:
            # Stop fans by setting temperature to 0 °C
            self.fans.set_temperature(0)
        if not no_clear:
            self.clear_lines()
        return True

    def clear_lines(self):
        DevMem.write(self.JAM_ENGINE_START_LINE, 0)
        DevMem.write(self.JAM_ENGINE_END_LINE, 0)
        return True

    def get_nr_lines(self):
        val = DevMem.read(self.JAM_ENGINE_END_LINE)
        if val == 0:
            return 0
        else:
            return int((val + 1) / self.LINE_SIZE_WORDS)

    def increment_nr_lines(self):
        val = DevMem.read(self.JAM_ENGINE_END_LINE)
        if val == 0:
            val = self.LINE_SIZE_WORDS - 1
        else:
            val += self.LINE_SIZE_WORDS
        DevMem.write(self.JAM_ENGINE_END_LINE, val)

    def add_blank_line(self, time_ns, adjust_allow=True):
        return self.add_jam_line(time_ns, force_blank=True, adjust_allow=adjust_allow)

    def add_jam_line(self, time_ns, start_MHz=0, stop_MHz=0, phase_degrees=0, repeat=0, rand_phase=True,
                     adjust_allow=False, blank_restart=True, force_blank=False):
        path_headroom_MHz = 1

        if self.band == Band.UNKNOWN:
            self.error_msg = "IPAM band is unknown"
            return False

        dds_nr_steps = int(round((time_ns * 1e-9) * self.DDS_SYNC_FREQ_HZ, 0))

        if force_blank:
            path = 0
            asf = 0
            src_att = 0x0
            dblr_att = 0xFF
            dds_start_Hz = 20e6
            dds_step_Hz = 0
        else:
            # Get the Tx path from the table
            path = None
            for freq_band in self.fpt.FREQ_BANDS:
                # Find the right IPAM band first
                if freq_band[0] == self.band:
                    # Now find the first Tx path that brackets the requested frequencies
                    if ((freq_band[2] - path_headroom_MHz) <= start_MHz <= (freq_band[3] + path_headroom_MHz)) and\
                       ((freq_band[2] - path_headroom_MHz) <= stop_MHz <= (freq_band[3] + path_headroom_MHz)):
                        path = freq_band[1]
                        path_end_MHz = freq_band[3]
                        break
            if path is None:
                self.error_msg = "requested frequency band is invalid"
                return False

            # Get the PA cal (att) setting
            mid_frequency_Hz = (start_MHz + stop_MHz) * 1e6 / 2
            if mid_frequency_Hz > path_end_MHz * 1e6:
                mid_frequency_Hz = path_end_MHz * 1e6
            get_att_dB = self.fpt.get_calibrated_att(self.fpt.band_name[self.band], path, mid_frequency_Hz)
            if get_att_dB[1]:
                att_dB = get_att_dB[0]
            else:
                self.error_msg = "calibration point for the requested frequency was not found"
                return False

            if self.band == Band.LOW:
                # Set ASF to level calibrated to drive PA for low band
                ratio = 10 ** (att_dB / 20)
                asf = int(round(4095 / ratio, 0))
                dblr_att = 0
                src_att = 0x3
            else:
                # Set ASF to level calibrated to drive multiplier for mid/high band
                asf = int(self.dds.get_calibrated_asf(mid_frequency_Hz))
                # Calculate doubler attenuator value, 1 LSB = 0.25 dB
                dblr_att = int(round((att_dB * 4), 0))
                src_att = 0x3

            # Get the DDS start frequency and frequency step
            dds_start_Hz = (start_MHz * 1e6) / RFControl.get_multiplier(path, self.band)
            dds_stop_Hz = (stop_MHz * 1e6) / RFControl.get_multiplier(path, self.band)
            dds_step_Hz = (dds_stop_Hz - dds_start_Hz) / dds_nr_steps

        # Calculate the jamming line parameters
        ctrl = 0
        ctrl |= (repeat & 0x3F) << 24
        ctrl |= (dblr_att & 0xFF) << 16
        ctrl |= (src_att & 0x3) << 12
        ctrl |= (path & 0x7) << 4
        if rand_phase:
            ctrl |= (1 << 30)
        if adjust_allow:
            ctrl |= (1 << 14)
        if blank_restart:
            ctrl |= (1 << 10)
        if force_blank:
            ctrl |= (1 << 9)

        ftw = int(round((dds_start_Hz / self.DDS_DAC_FREQ_HZ) * (2 ** 32), 0))
        dftw = int(round((dds_step_Hz / self.DDS_DAC_FREQ_HZ) * (2 ** 32), 0))
        pow = int(round((65536 * (phase_degrees % 360)) / 360, 0))
        pow_asf = ((asf & 0xFFFF) << 16) | (pow & 0xFFFF)

        line_addr = self.JAM_ENGINE_LINE_BASE + (self.get_nr_lines() * self.LINE_SIZE_BYTES)
        DevMem.write(line_addr + self.LINE_OFFSET_CTRL, ctrl)
        DevMem.write(line_addr + self.LINE_OFFSET_FTW, ftw)
        DevMem.write(line_addr + self.LINE_OFFSET_DFTW, dftw)
        DevMem.write(line_addr + self.LINE_OFFSET_POW_ASF, pow_asf)
        DevMem.write(line_addr + self.LINE_OFFSET_DUR, dds_nr_steps)
        self.increment_nr_lines()

        if self.verbose:
            print("Line {}: ".format(self.get_nr_lines()))
            print("CTRL:    0x{:08x}".format(ctrl))
            print("FTW:     0x{:08x}".format(ftw))
            print("DFTW:    0x{:08x}".format(dftw))
            print("POW_ASF: 0x{:08x}".format(pow_asf))
            print("DUR:     0x{:08x}".format(dds_nr_steps))
        
        # If we got this far then everything worked    
        return True

    def print_status(self, ok):
        if ok:
            print("OK")
        else:
            print("Error: " + self.error_msg)
            exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control the EMA module to generate DDS jamming waveforms")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("-i", "--initialise",
                        help="initialise the EMA module",
                        action="store_true")
    action.add_argument("-t", "--terminate",
                        help="terminate tests, de-initialise EMA module",
                        action="store_true")
    action.add_argument("-j", "--jam",
                        help="start jamming (use this after initialising and defining one or more lines)",
                        action="store_true")
    action.add_argument("-s", "--stop",
                        help="stop jamming (use this after jamming to allow new lines to be loaded "
                             "before jamming again)",
                        action="store_true")
    action.add_argument("-a", "--append",
                        help="append a jamming or blanking line to the jamming table",
                        action="store_true")
    action.add_argument("-F", "--force-fans",
                        help="force fans to 100%%, do nothing else",
                        action="store_true")
    parser.add_argument("-v", "--verbose",
                        help="print information to aid debug",
                        action="store_true")
    parser.add_argument("-n", "--no-clear",
                        help="do not clear jamming lines, use this with --stop to leave the jamming lines in memory",
                        action="store_true")
    parser.add_argument("-f", "--fans-on",
                        help="use this with --stop to leave the fans running",
                        action="store_true")
    parser.add_argument("-r", "--rx-on",
                        help="use this with --initialise to power-up and initialise receiver",
                        action="store_true")
    parser.add_argument("start", nargs="?", default=0,
                        help="sweep start frequency in MHz (use 0 for a blanking line)")
    parser.add_argument("end", nargs="?", default=0,
                        help="sweep end frequency in MHz (use 0 for a blanking line)")
    parser.add_argument("sweep_time", nargs="?", default=1000,
                        help="sweep time in nanoseconds")
    parser.add_argument("phase", nargs="?", default=0,
                        help="phase in degrees")
    parser.add_argument("repeat", nargs="?", default=0,
                        help="number of sweep repeats; 0 to 63 (0 runs the sweep once, 63 runs the sweep 64 times)")
    parser.add_argument("--rand-phase",
                        help="use random phase for this line (ignore phase value)",
                        action="store_true")
    parser.add_argument("--adjust-allow",
                        help="allow timing adjustments on this line (for use with sync TP)",
                        action="store_true")
    parser.add_argument("--blank-restart",
                        help="restart this line if hit by an async TP period",
                        action="store_true")
    args = parser.parse_args()

    jam = SysTestJam(verbose=args.verbose)

    if args.initialise:
        if jam.initialise(rx_en=args.rx_on):
            print("OK: initialised EMA module")
        else:
            print("ERROR: {}".format(jam.error_msg))
    elif args.terminate:
        if jam.terminate():
            print("OK: terminated tests on EMA module")
        else:
            print("ERROR: {}".format(jam.error_msg))
    elif args.force_fans:
        if not jam.force_fans():
            print("ERROR: {}".format(jam.error_msg))
    elif args.jam:
        if jam.start_jamming():
            print("OK: started jamming")
        else:
            print("ERROR: {}".format(jam.error_msg))
    elif args.stop:
        if jam.stop_jamming(args.no_clear, args.fans_on):
            print("OK: stopped jamming ", end="", flush=True)
            if args.no_clear:
                print("(did not clear lines)")
            else:
                print("(cleared lines)")
        else:
            print("ERROR: {}".format(jam.error_msg))
    elif args.append:
        # Check parameters
        start = float(args.start)
        end = float(args.end)
        sweep_time = float(args.sweep_time)
        phase = float(args.phase)
        repeat = int(args.repeat)
        if end < start:
            print("ERROR: end frequency must be greater than or equal to start frequency")
            exit()
        if sweep_time < SysTestJam.SWEEP_MIN_NS:
            print("ERROR: sweep time must be greater than or equal to {} ns".format(SysTestJam.SWEEP_MIN_NS))
            exit()
        if sweep_time > SysTestJam.SWEEP_MAX_NS:
            print("ERROR: sweep time must be less than or equal to {} ns".format(SysTestJam.SWEEP_MAX_NS))
            exit()
        if phase < 0:
            print("ERROR: phase must be non-negative")
            exit()
        if repeat < 0:
            print("ERROR: repeat must be non-negative")
            exit()
        if repeat > SysTestJam.REPEAT_MAX:
            print("ERROR: repeat must be less than or equal to {}".format(SysTestJam.REPEAT_MAX))
            exit()
        if start == 0 and end == 0:
            if jam.add_blank_line(sweep_time, args.adjust_allow):
                print("OK: appended blanking line")
            else:
                print("ERROR: {}".format(jam.error_msg))
        else:
            # Check start/end frequency
            if start < SysTestJam.FREQ_MIN_MHZ:
                print("ERROR: start frequency must be greater than or equal to {} MHz".format(SysTestJam.FREQ_MIN_MHZ))
                exit()
            if end > SysTestJam.FREQ_MAX_MHZ:
                print("ERROR: end frequency must be less than or equal to {} MHz".format(SysTestJam.FREQ_MAX_MHZ))
                exit()
            if args.verbose:
                print("Start MHz:     {}".format(start))
                print("End MHz:       {}".format(end))
                print("Sweep Time ns: {}".format(sweep_time))
                print("Phase:         {}". format(phase))
                print("Repeat:        {}".format(repeat))
                print("Rand Phase:    {}".format(args.rand_phase))
                print("Adjust Allow:  {}".format(args.adjust_allow))
                print("Blank Restart: {}".format(args.blank_restart))
            if jam.add_jam_line(time_ns=sweep_time,
                                start_MHz=start,
                                stop_MHz=end,
                                phase_degrees=phase,
                                repeat=repeat,
                                rand_phase=args.rand_phase,
                                adjust_allow=args.adjust_allow,
                                blank_restart=args.blank_restart):
                print("OK: appended jamming line")
            else:
                print("ERROR: {}".format(jam.error_msg))
    else:
        parser.print_help()
        exit()

    if args.verbose:
        print("Jamming engine now contains {} lines".format(jam.get_nr_lines()))
