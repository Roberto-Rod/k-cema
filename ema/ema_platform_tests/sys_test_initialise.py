#!/usr/bin/env python3
from ad96xx import *
from power_supplies import *
from synth import *
from dds import *
from hardware_unit_config import *
from rf_control import *
from rx_control import *
from timing_control import *
from band import *
from ipam import *
from fans import *
from pcm import *
from serial_number import *

import os
import time
import argparse

# Class provided to initialise the EMA ready for system tests
class SysTestInitialise:
    ATT_MAX_DB = 63.75
    # ADC fast detect threshold, -6 dBFS = 0x1000
    # Set to -20 dBFS = 0x0333
    ADC_FAST_DETECT_THRESHOLD = 0x333

    band_name = {}
    band_name[Band.LOW] = "Low"
    band_name[Band.MID] = "Mid"
    band_name[Band.HIGH] = "High"

    voltage = {}
    voltage[Band.LOW] = 30
    voltage[Band.MID] = 32
    voltage[Band.HIGH] = 30

    def init(self, sweep_mode=False, rx_en=True):
        error_msg = ""
        
        # First steps
        os.system("/usr/bin/killall KCemaEMAApp; /usr/bin/killall ema_app.bin; sleep 2")
        serial = SerialNumber.get_serial(Module.EMA)
        # Force mute then enable IPAM and get band
        IPAM.force_mute(True)
        IPAM.enable_power(True)
        ok = IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S) and \
             IPAM.prepare_power_monitor() and \
             IPAM.initialise_vswr()
        if not ok:
            error_msg = ": IPAM did not become ready"
            self.terminate()
            return False, error_msg
        band = IPAM.get_rf_band()

        if band == Band.UNKNOWN:
            error_msg = ": IPAM band is unknown"
            self.terminate()
            return False, error_msg

        # Determine if IPAM is eHB type
        ipam_ehb = False
        if band == Band.HIGH:
            if IPAM.is_extended_high_band():
                ipam_ehb = True

        # Determine if NTM is eHB type
        ntm_ehb = False
        status, config = get_config_info(AssemblyType.EMA_LB_R)
        if status:
            try:
                if "Assembly Part Number" in config.keys():
                    assy_nr = config["Assembly Part Number"]
                    if assy_nr.startswith("KT-950-0505"):
                        ntm_ehb = True
            except Exception:
                error_msg = ": could not get Assembly Part Number"
                return False, error_msg

        if band == Band.LOW and rx_en:
            rx_test_enabled = True
        else:
            rx_test_enabled = False

        print("Initialising EMA-{} Band-{}{}...".format(serial, self.band_name[band], " (eHB)" if ipam_ehb and ntm_ehb else ""))
        f = Fans()
        f.initialise()
        f.set_temperature(0)
        time.sleep(2)

        # Set PCM voltage according to IPAM band
        if not PCM.set_voltage(self.voltage[band]):
            error_msg = ": failed to set PCM to +{} V: ".format(self.voltage[band])
            self.terminate()
            return False, error_msg

        # Enable Tx & Rx power supplies
        PowerSupplies.rail_5v5_en()
        PowerSupplies.rail_3v6_en()
        PowerSupplies.tx_en()

        if rx_test_enabled:
            PowerSupplies.rail_7v3_en()
            PowerSupplies.rx_en()
            PowerSupplies.if_adc_en()

            # Enable Rx test mode
            tm = TimingControl()
            tm.enable_tx_in_rx_test_mode()
            tm.enable_rx_test_mode()

            # Initialise IF ADC
            time.sleep(1)
            if not AD96xx.reset():
                error_msg = ": failed to reset AD9690"
                self.terminate()
                return False, error_msg

            # Set IF ADC Fast Detect threshold
            if not AD96xx.set_fast_detect_threshold(self.ADC_FAST_DETECT_THRESHOLD):
                error_msg = ": failed to set AD9690 fast detect threshold"
                self.terminate()
                return False, error_msg

            # Initialise Rx synths
            rx = RxControl()
            if not rx.initialise_synths():
                error_msg = ": failed to initialise Rx synths"
                self.terminate()
                return False, error_msg

            # Set selected synth to 1
            if not rx.set_active_synth(1):
                error_msg = ": failed to set Rx synth"
                self.terminate()
                return False, error_msg

            # Set Rx RF attenuation to 30 dB
            if not rx.set_rf_attenuator(30):
                error_msg = ": failed to set Rx RF attenuator"
                self.terminate()
                return False, error_msg

            # Disable Rx LNA
            if not rx.set_lna_enable(False, band):
                error_msg = ": failed to disable Rx LNA"
                self.terminate()
                return False, error_msg

        # Initialise DDS synth
        Synth.initialise()
        if not Synth.is_locked():
            error_msg = ": synth is not locked"
            self.terminate()
            return False, error_msg

        # Initialise DDS
        d = DDS()
        d.initialise(sweep_mode)

        # Set source attenuation
        RFControl.set_source_att(0)

        # Set doubler/multiplier attenuation
        RFControl.set_doubler_att(self.ATT_MAX_DB)
        RFControl.en_doubler_att_20_dB(False)

        if rx_test_enabled:
            # Enable Rx test mode
            tm = TimingControl()
            tm.enable_tx_in_rx_test_mode()
            tm.enable_rx_test_mode()

        # If we got this far then everything worked
        return True, error_msg

    def terminate(self):
        # Put EMA back to the state we started in
        IPAM.enable_power(False)
        DDS.enable_power(False)
        PowerSupplies.disable_all()
        fans = Fans()
        fans.set_temperature(0)


if __name__ == "__main__":
    o = SysTestInitialise()
    parser = argparse.ArgumentParser(description = "Initialise the EMA ready for system tests")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()
    ok, error_msg = o.init()
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
