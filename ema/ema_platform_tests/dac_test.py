import argparse
import time

from xcvr_control import *
from adf4355 import *
from ad9162 import *
from ad9528 import *
from jesd204b import *
from mcp4728 import *
from power_supplies import *


class DACTest:
    def tune_lb(self, freq_MHz, att_dB=50):
        FREQ_MIN_MHZ = 20
        FREQ_MAX_MHZ = 520
        ATT_MAX_DB = 52.75

        # Transceiver test tone amplitude (-3 dBFS)
        # TEST_TONE_AMP = 0x02D5  # -3 dBFS
        TEST_TONE_AMP = 0x0144  # -10 dBFS
        NVME_AMP = 0x0080

        jesd204b_source = JESD204BSource.NVME
        test_mode = False

        # Xcvr object used to control SoC JESD204B blocks
        xcvr = XcvrControl()

        if not FREQ_MIN_MHZ <= freq_MHz <= FREQ_MAX_MHZ:
            print("Error: frequency out of bounds ({} MHz - {} MHz)".format(FREQ_MIN_MHZ, FREQ_MAX_MHZ))
            return False
        if not att_dB <= ATT_MAX_DB:
            print("Error: attenuation out of bounds (0 dB - {} dB)".format(ATT_MAX_DB))
            return False

        print("Enable DAC power supplies: ", end="", flush=True)
        PowerSupplies.rail_neg_1v8_en()
        PowerSupplies.tx_dac_en()
        for attempts in range(10):
            print(".", end="", flush=True)
            time.sleep(1)
            if PowerSupplies.tx_dac_pgood():
                print("OK")
                break
        if not PowerSupplies.tx_dac_pgood():
            print("FAIL - PGOOD not asserted")
            return False
        print("Initialise DAC synth: ", end="")
        dac_synth = ADF4355()
        dac_synth.enable_device()
        dac_synth.set_synth_3000_megahertz()
        print("OK")
        print("Initialise DAC... ")
        dac = AD9162(fdac=3e9)
        if not dac.initialise(test_mode=test_mode):
            return False
        if not test_mode:
            print("Initialise SoC JESD204B...")
            jesd204b = JESD204B()
            if not jesd204b.initialise(direction=JESD204BDirection.TX, nlanes=1, octets_per_frame=4):
                return False
            print("Initialise DAC JESD204B...")
            if not dac.initialise_jesd204b(nlanes=1, interpolation=24):
                return False
            print("Set JESD204B source to {}: ".format(str(jesd204b_source)), end="", flush=True)
            if not xcvr.jesd204b_stream_select(jesd204b_source):
                print("ERROR")
                return False
            print("OK")
            print("Set stream amplitude: ", end="", flush=True)
            if jesd204b_source == JESD204BSource.Tone:
                amp = TEST_TONE_AMP
            else:
                amp = NVME_AMP
            if not xcvr.set_test_tone_amplitude(amp):
                print("ERROR")
                return False
            print("OK")
            print("Initialise DAC NCO and set frequency to {} MHz: ".format(freq_MHz), end="", flush=True)
            if not dac.setup_nco(nco_only_mode=False, freq_megahertz=freq_MHz):
                print("ERROR")
                return False
            print("OK")
        else:
            # Set DAC frequency
            print("Set DAC frequency to {} MHz: ".format(freq_MHz), end="", flush=True)
            if not dac.set_frequency(freq_MHz * 1e6):
                print("ERROR")
                return False
            print("OK")
        print("Set DAC attenuator to {} dB: ".format(att_dB), end="", flush=True)
        if not dac.set_att_dB(att_dB):
            print("ERROR")
            return False
        print("OK")
        print("Enable DAC Tx: ", end="", flush=True)
        if not dac.enable_tx():
            print("ERROR")
            return False
        print("OK")
        return True


    def tune_mbhb(self, freq_MHz, att_dB=40):
        FREQ_MIN_MHZ = 400
        FREQ_MAX_MHZ = 6000

        XCVR_ATT_MAX_MILLI_DB = 41950
        ATT_MAX_DB = XCVR_ATT_MAX_MILLI_DB / 1000

        # Transceiver test tone amplitude (-3 dBFS)
        # TEST_TONE_AMP = 0x02D5  # -3 dBFS
        TEST_TONE_AMP = 0x0144  # -10 dBFS
        NVME_AMP = 0x0180

        jesd204b_source = JESD204BSource.NVME

        if not FREQ_MIN_MHZ <= freq_MHz <= FREQ_MAX_MHZ:
            print("Error: frequency out of bounds ({} MHz - {} MHz)".format(FREQ_MIN_MHZ, FREQ_MAX_MHZ))
            return False
        if not att_dB <= ATT_MAX_DB:
            print("Error: attenuation out of bounds (0 dB - {} dB)".format(ATT_MAX_DB))
            return False

        xcvr = XcvrControl()
        print("Connect to transceiver driver...")
        if not xcvr.connect():
            print("ERROR: Failed to connect to transceiver driver")
            return False
        # Trim Clock DAC to mid-rail
        print("Set Trim DAC to Mid-Rail: ", end="", flush=True)
        trim = MCP4728()
        if trim.set_dac_midscale():
            print("OK")
        else:
            print("FAIL")
        # Initialise Clock Generator
        print("Initialise Clock Generator: ", end="", flush=True)
        xcvr.reset(False)
        clk = AD9528()
        if clk.initialise():
            print("OK")
        else:
            print("FAIL")
            return False
        # Run the transceiver initialisation
        print("Initialise transceiver device (typ. 45 seconds)...", flush=True)
        if not xcvr.initialise():
            print("ERROR: Failed to initialise transceiver")
            return False
        print("Enable Tx mode: ", end="", flush=True)
        if not xcvr.enable_tx_mode():
            print("ERROR: Failed to enter Tx mode")
            return False
        print("OK")
        print("Set Tx attenuation: ", end="", flush=True)
        if not xcvr.set_tx_att(XCVR_ATT_MAX_MILLI_DB):
            print("ERROR: Failed to set Tx attenuation")
            return False
        print("OK")
        print("Enable NTM RF Tx path: ", end="", flush=True)
        if not xcvr.tx_en():
            print("ERROR: Failed to enable NTM RF Tx")
            return False
        print("OK")
        print("Set JESD204B source ({}): ".format(jesd204b_source), end="", flush=True)
        if not xcvr.jesd204b_stream_select(jesd204b_source):
            print("ERROR")
            return False
        print("OK")
        print("Set stream amplitude: ", end="", flush=True)
        if jesd204b_source == JESD204BSource.Tone:
            amp = TEST_TONE_AMP
        else:
            amp = NVME_AMP
        if not xcvr.set_test_tone_amplitude(amp):
            print("ERROR")
            return False
        print("OK")
        print("Set DAC frequency to {} MHz: ".format(freq_MHz), end="", flush=True)
        if not xcvr.set_frequency(freq_MHz):
            print("ERROR")
            return False
        print("OK")
        print("Set DAC attenuator to {} dB: ".format(att_dB), end="", flush=True)
        att_milli_dB = att_dB * 1000
        # http://jira.kirintec.local/browse/KCEMA-1310 work-around write Tx att twice...
        if not (xcvr.set_tx_att(att_milli_dB) and xcvr.set_tx_att(att_milli_dB)):
            print("ERROR - failed to set transceiver Tx attenuation")
            return False
        print("OK")
        return True


if __name__ == "__main__":
    if len(sys.argv) > 2:
        freq_MHz = int(sys.argv[1])
        band = str(sys.argv[2]).upper()
        dac = DACTest()
        if band == "LB":
            dac.tune_lb(freq_MHz, att_dB=10)
        elif band == "MB" or band == "HB":
            dac.tune_mbhb(freq_MHz, att_dB=10)
        else:
            print("Band not recognised")
    else:
        print("Usage: dac_test.py freq_MHz [LB|MB|HB]")
