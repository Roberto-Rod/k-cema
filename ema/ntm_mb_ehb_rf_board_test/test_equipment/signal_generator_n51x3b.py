import pyvisa

#   Currently supported models:
#       N5173B
#       N5183B

class SignalGeneratorN51X3B:
    def __init__(self, debug = False):
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sg = None
        self.debug = debug
    
    def __del__(self):
        if self.sg:
            self.sg.close()
        
    def find_and_initialise(self):
        self.resource = None
        for res in self.rm.list_resources():
            if res:
                self.resource = res
                if self.initialise_device():
                    print("Found and initialised N5173B/83B Signal Generator: {}".format(res))
                    return True
                else:
                    self.resource = None
        print("ERROR: did not find an N5173B/83B Signal Generator")
        return False
            
    def initialise_device(self):
        try:
            self.sg = self.rm.open_resource(self.resource)    
            if "N5173B" in self.details() or "N5183B" in self.details():
                if self.send_command("*RST") and self.wait_command_complete():
                    ok = True
                else:
                    ok = False
                    self.sg.close()
            else:
                ok = False
                self.sg.close()                                 
        except:
            if self.sg:
                self.sg.close()
                print("Could not open resource: {}".format(self.resource))
            else:
                print("Resource busy: {}".format(self.resource))
            ok = False
        return ok     
        
    def details(self):
        return self.send_query("*IDN?")
    
    def resource_name(self):
        return self.resource
    
    def set_frequency_Hz(self, freq_Hz):
        if self.send_command("FREQ {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_frequency_Hz(self):
        return int(float(self.send_query("FREQ?").strip()))
        
    def set_output_power_dBm(self, power_dBm):
        if self.send_command("POW:AMPL {:.2f} DBM".format(power_dBm)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_output_power_dBm(self):
        return float(self.send_query("POW:AMPL?").strip())
    
    def set_output_enable(self, enable_state):
        if self.send_command("OUTP:STAT ON" if enable_state else "OUTP:STAT OFF"):
            return self.wait_command_complete()
        else:
            return False
    
    def get_output_enable(self):
        resp = self.send_query("OUTP:STAT?").strip()
        return bool(resp == "1" or resp == "+1")
    
    def wait_command_complete(self):
        resp = self.send_query("*OPC?").strip()
        return bool(resp == "1" or resp == "+1")

    def send_command(self, cmd):
        if self.debug:
            print("send_command: {}".format(cmd))
        try:            
            self.sg.write(cmd)
            return True
        except:
            print("ERROR - could not send command")
            return False
    
    def send_query(self, query):
        if self.debug:
            print("send_query: {}".format(query))
        try:
            return self.sg.query(query).strip()
        except:
            print("ERROR - could not send query")
        return False


if __name__ == "__main__":
    sg = SignalGeneratorN51X3B()
    print("SignalGeneratorN51X3B Test:")
    if sg.find_and_initialise():
        print("Found and initialised: {}".format(sg.details()))        
    else:
        print("ERROR: could not find & configure signal generator")
        exit()
        
    print("Set frequency to 10 MHz: ", end="", flush=True)
    if sg.set_frequency_Hz(10e6):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get frequency: {} Hz".format(sg.get_frequency_Hz()))
    
    print("Set output power to -10.0 dBm: ", end="", flush=True)
    if sg.set_output_power_dBm(-10.0):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get output power: {} dBm".format(sg.get_output_power_dBm()))
    
    print("Set output enable state to 'on': ", end="", flush=True)
    if sg.set_output_enable(True):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get output enable state: {}".format(sg.get_output_enable()))
    
    print("Set frequency to 20 MHz: ", end="", flush=True)
    if sg.set_frequency_Hz(20e6):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get frequency: {} Hz".format(sg.get_frequency_Hz()))
    
    print("Set output power to -20.0 dBm: ", end="", flush=True)
    if sg.set_output_power_dBm(-20.0):
        print("OK")
    else:
        print("ERROR")
        exit()
        
    print("Get output power: {} dBm".format(sg.get_output_power_dBm()))
    
    print("Set output enable state to 'off': ", end="", flush=True)
    if sg.set_output_enable(False):
        print("OK")
    else:
        print("ERROR")
        exit()
    
    print("Get output enable state: {}".format(sg.get_output_enable()))