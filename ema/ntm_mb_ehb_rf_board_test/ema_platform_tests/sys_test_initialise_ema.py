#!/usr/bin/env python3
from ad9528 import *
from power_supplies import *
from synth import *
from dds import *
from rf_control import *
from timing_control import *
from band import *
from fans import *
from serial_number import *

import os
import time
import argparse

# Class provided to initialise the EMA ready for RF Board tests
class SysTestInitialiseEMA:
    ATT_MAX_DB = 51.75
    
    band_name = {}
    band_name[Band.LOW] = "Low"
    band_name[Band.MID] = "Mid"
    band_name[Band.HIGH] = "High"

    def init(self, sweep_mode=False):
        error_msg = ""
        
        # First steps
        os.system("/usr/bin/killall KCemaEMAApp; /usr/bin/killall ema_app.bin; sleep 2")
        serial = SerialNumber.get_serial(Module.EMA)

        # We know this is an EMA MB for now...
        band = Band.MID

        print("Initialising EMA-{} Band-{}...".format(serial, self.band_name[band]))
        f = Fans()
        f.initialise()
        f.set_temperature(40)
        time.sleep(2)

        # Enable the RF Board power supplies
        PowerSupplies.rail_1v3_en()
        PowerSupplies.rail_2v1_en()
        PowerSupplies.rail_3v6_en()
        PowerSupplies.rail_5v3_en() # Now 5V4
        PowerSupplies.tx_en()
        PowerSupplies.rx_en()

        # Enable Rx test mode
        tm = TimingControl()
        tm.enable_tx_in_rx_test_mode()
        tm.enable_rx_test_mode()

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

        # Bring AD9528 clock generator out of reset
        os.system("/sbin/devmem 0x40015008 32 1")
        # Initialise AD9528 clock generator
        clk = AD9528()
        clk.initialise()

        # If we got this far then everything worked
        return True, error_msg

    def terminate(self):
        # Put EMA back to the state we started in
        DDS.enable_power(False)
        PowerSupplies.rx_en(False)
        PowerSupplies.tx_en(False)
        PowerSupplies.rail_5v3_en(False)
        PowerSupplies.rail_3v6_en(False)
        PowerSupplies.rail_2v1_en(False)
        PowerSupplies.rail_1v3_en(False)


if __name__ == "__main__":
    o = SysTestInitialiseEMA()
    parser = argparse.ArgumentParser(description = "Initialise the EMA ready for NTM RF Board tests")
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
