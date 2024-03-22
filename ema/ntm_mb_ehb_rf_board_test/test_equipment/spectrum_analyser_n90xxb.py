import pyvisa

#   Currently supported models:
#       N9010B

class SpectrumAnalyserN90XXB:
    def __init__(self, debug=False):
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sa = None
        self.debug = debug

    def __del__(self):
        if self.sa:
            self.sa.close()

    def find_and_initialise(self):
        self.resource = None
        for res in self.rm.list_resources():
            if res:
                self.resource = res
                try:
                    if self.initialise_device():
                        print("Found and initialised N90XXB Spectrum Analyser: {}".format(res))
                        return True
                    else:
                        self.resource = None
                except:
                    self.resource = None
        print("ERROR: did not find an N90XXB Spectrum Analyser")
        return False

    def initialise_device(self):
        try:
            self.sa = self.rm.open_resource(self.resource)            
            str = self.details()
            if "N9010B" in str:
                # Set 5 second timeout since Preset takes ~3 seconds
                self.sa.timeout = 5000
                if self.send_command("SYST:PRES") and self.wait_command_complete():
                    ok = True
                else:
                    ok = False
                    self.sa.close()
            else:
                ok = False
                self.sa.close()
        except:
            if self.sa:
                self.sa.close()
                print("Could not open resource: {}".format(self.resource))
            else:
                print("Resource busy: {}".format(self.resource))
            ok = False
        return ok

    def details(self):
        return self.send_query("*IDN?")

    def resource_name(self):
        return self.resource

    def set_centre_frequency_Hz(self, freq_Hz):
        if self.send_command("FREQ:CENT {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False

    def get_centre_frequency_Hz(self):
        return int(float(self.send_query("FREQ:CENT?").strip()))
    
    def set_span_Hz(self, freq_Hz):
        if self.send_command("FREQ:SPAN {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_span_Hz(self):
        return int(float(self.send_query("FREQ:SPAN?").strip()))
    
    def set_resolution_BW_Hz(self, freq_Hz):
        if self.send_command("BAND:RES {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_resolution_BW_Hz(self):
        return int(float(self.send_query("BAND:RES?").strip()))
    
    def set_reference_level_dBm(self, level_dBm):
        if self.send_command("DISP:WIND:TRAC:Y:RLEV {:.2f} DBM".format(level_dBm)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_reference_level_dBm(self):
        return float(self.send_query("DISP:WIND:TRAC:Y:RLEV?").strip())
    
    def set_dB_per_division(self, division_dB):
        if self.send_command("DISP:WIND:TRAC:Y:PDIV {:.2f} DB".format(division_dB)):
            return self.wait_command_complete()
        else:
            return False

    def get_dB_per_division(self):
        return float(self.send_query("DISP:WIND:TRAC:Y:PDIV?").strip())
    
    def set_continuous_sweep(self, continuous):
        if self.send_command("INIT:CONT ON" if continuous else "INIT:CONT OFF"):
            return self.wait_command_complete()
        else:
            return False
    
    def get_peak_Hz_dBm(self):
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("CALC:MARK1:X?").strip()))
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            return freq_Hz, ampl_dBm
        else:
            return 0, -999.0

    def get_peak_amplitude_dBm(self):
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            return ampl_dBm
        else:
            return -999.0

    def get_peak_frequency_Hz(self):
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("CALC:MARK1:X?").strip()))
            return freq_Hz
        else:
            return 0

    last_freq_Hz = 0
    def get_next_peak_Hz_dBm(self):
        # Perform the next peak search
        if self.marker_find_next_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("CALC:MARK1:X?").strip()))
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            valid = freq_Hz != self.last_freq_Hz
            # Remember the last marker frequency
            self.last_freq_Hz = freq_Hz
            return freq_Hz, ampl_dBm, valid
        else:
            return 0, -999.0, False

    def set_attenuation_mode(self, auto):
            if self.send_command("POW:ATT:AUTO ON" if auto else "POW:ATT:AUTO OFF"):
                return self.wait_command_complete()
            else:
                return False

    def set_attenuation_dB(self, atten_dB):
        if self.send_command("POW:ATT {:.2f} DB".format(atten_dB)):
            return self.wait_command_complete()
        else:
            return False

    def set_video_average_mode(self, enabled):
        if self.send_command("AVER ON" if enabled else "AVER OFF"):
            return self.wait_command_complete()
        else:
            return False

    def set_video_average_sweeps(self, sweeps):
        # Number of sweeps must be between 1 and 10000
        if sweeps >= 1 and sweeps <= 10000:
            if self.send_command("AVER:COUN {:.0f}".format(sweeps)):
                return self.wait_command_complete()
            else:
                return False
        else:
                return False

    def set_marker_noise_mode(self, enabled):
        if self.send_command("CALC:MARK:FUNC NOIS" if enabled else "CALC:MARK:FUNC OFF"):           
            return self.wait_command_complete()
        else:
            return False

    def get_amplitude_dBm(self, freq_Hz):
        # Set the marker frequency first
        if self.send_command("CALC:MARK1:X {:.0f} HZ".format(freq_Hz)) and self.wait_command_complete():
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            return ampl_dBm
        else:
            return -999.0

    def set_peak_excursion_dB(self, excursion_dB):
        if self.send_command("CALC:MARK:PEAK:EXC {:.2f} DB".format(excursion_dB)):
            return self.wait_command_complete()
        else:
            return False
    
    def set_peak_threshold_dBm(self, threshold_dBm):
        if self.send_command("CALC:MARK:PEAK:THR {:.2f} DBM".format(threshold_dBm)):
            return self.wait_command_complete()
        else:
            return False

    def set_max_hold_mode(self, enabled):
        if self.send_command("TRAC1:TYPE MAXH" if enabled else "TRAC1:TYPE WRIT"):
            return self.wait_command_complete()
        else:
            return False
        
    def marker_find_peak(self):        
        # Trigger a sweep
        if self.send_command("INIT:IMM") and self.wait_command_complete():
            # Set marker 1 to peak
            if self.send_command("CALC:MARK1:MAX") and self.wait_command_complete():
                return True
            else:
                return False
        else:
            return False
    
    def marker_find_next_peak(self):
        # Set marker 1 to next peak
        if self.send_command("CALC:MARK1:MAX:NEXT") and self.wait_command_complete():
            return True
        else:
            return False

    def wait_command_complete(self):
        resp = self.send_query("*OPC?").strip()
        return bool(resp == "1" or resp == "+1")

    def send_command(self, cmd):
        if self.debug:
            print("send_command: {}".format(cmd))
        try:
            self.sa.write(cmd)
            return True
        except:
            print("ERROR - could not send command")
            return False

    def send_query(self, query):
        if self.debug:
            print("send_query: {}".format(query))
        try:
            return self.sa.query(query).strip()
        except:
            print("ERROR - could not send query")
        return False


if __name__ == "__main__":
    sa = SpectrumAnalyserN90XXB(debug=False)
    print("SpectrumAnalyserN90XXB Test:")
    if sa.find_and_initialise():
        print("Found and initialised: {}".format(sa.details()))
    else:
        print("ERROR: could not find & configure spectrum analyser")
        exit()

    print("Set centre frequency to 1 GHz: ", end="", flush=True)
    if sa.set_centre_frequency_Hz(1e9):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get centre frequency: {} Hz".format(sa.get_centre_frequency_Hz()))

    print("Set span to 10 MHz: ", end="", flush=True)
    if sa.set_span_Hz(10e6):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get span: {} Hz".format(sa.get_span_Hz()))

    print("Set resolution bandwidth to 10 kHz: ", end="", flush=True)
    if sa.set_resolution_BW_Hz(10e3):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get resolution bandwidth: {} Hz".format(sa.get_resolution_BW_Hz()))

    print("Set reference level to 10.0 dBm: ", end="", flush=True)
    if sa.set_reference_level_dBm(10.0):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get reference level: {} dBm".format(sa.get_reference_level_dBm()))

    print("Set dB per division to 20.0 dB: ", end="", flush=True)
    if sa.set_dB_per_division(20.0):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get dB per division: {} dB".format(sa.get_dB_per_division()))

    print("Set continous sweep (on): ", end="", flush=True)
    if sa.set_continuous_sweep(True):
        print("OK")
    else:
        print("ERROR")
        exit()
    
    print("Set peak excursion to 1 dB: ", end="", flush=True)
    if sa.set_peak_excursion_dB(1.0):
        print("OK")
    else:
        print("ERROR")
        exit()

    print("Set peak threshold to -90 dBm: ", end="", flush=True)
    if sa.set_peak_threshold_dBm(-90.0):
        print("OK")
    else:
        print("ERROR")
        exit()

    print("Get peak: {0[0]} Hz, {0[1]} dBm".format(sa.get_peak_Hz_dBm()))

    print("Get peak amplitude: {} dBm".format(sa.get_peak_amplitude_dBm()))

    print("Get peak frequency: {} Hz".format(sa.get_peak_frequency_Hz()))

    print("Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
    print("Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
    print("Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
        
    print("Get amplitude at 1 GHz: {} dBm".format(sa.get_amplitude_dBm(1e9)))

    print("Set attenuation to 10 dB: ", end="", flush=True)
    if sa.set_attenuation_dB(10.0):
        print("OK")
    else:
        print("ERROR")
        exit()

    print("Set video average mode (on): ", end="", flush=True)
    if sa.set_video_average_mode(True):
        print("OK")
    else:
        print("ERROR")
        exit()

    print("Set video averaging to 10 sweeps: ", end="", flush=True)
    if sa.set_video_average_sweeps(10):
        print("OK")
    else:
        print("ERROR")
        exit()

    print("Set marker noise mode (on): ", end="", flush=True)
    if sa.set_marker_noise_mode(True):
        print("OK")
    else:
        print("ERROR")
        exit()    

    print("Set max hold mode (on): ", end="", flush=True)
    if sa.set_max_hold_mode(True):
        print("OK")
    else:
        print("ERROR")
        exit()