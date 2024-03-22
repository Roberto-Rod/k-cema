#!/usr/bin/env python3
from find_service import *
import socket
import select
import json


class SignalGenerator:
    def __init__(self, timeout=10):
        self.address = "0.0.0.0"
        self.port = 0
        self.timeout = timeout
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.found = False
        self.description = "<not found>"

    def __del__(self):
        self.sock.close()

    def find(self, ip_addr=None):
        # Allow 2 minutes to find service so that operator has a chance to start the service
        # if it isn't already running
        location = FindService.find_sgs(False, ip_addr, 120)
        self.address = location[0]
        self.port = location[1]
        if self.address == "0.0.0.0":
            return False
        else:
            return True

    def connect(self):
        self.found = False
        self.sock.connect((self.address, self.port))
        #self.sock.setblocking(0)
        resp = self.send_commmand("query signal generator available")
        if "status" in resp.keys() and resp["status"] == "ok":
            if "signal generator available" in resp.keys() and\
               (resp["signal generator available"] == "true" or resp["signal generator available"]):
                self.found = True                
            if "description" in resp.keys():
                self.description = resp["description"]
        return self.found
    
    def set_frequency_Hz(self, freq_Hz):
        ok = False
        if self.found:
            resp = self.send_commmand("set frequency", {"frequency": freq_Hz})
            if "status" in resp.keys() and resp["status"] == "ok":
                ok = True
        return ok
    
    def get_frequency_Hz(self):
        if self.found:
            resp = self.send_commmand("get frequency")
            if "status" in resp.keys() and resp["status"] == "ok":
                if "Hz" in resp.keys():
                    freq_Hz = float(resp["Hz"])
        return freq_Hz
    
    def set_output_power_dBm(self, power_dBm):
        ok = False
        if self.found:
            resp = self.send_commmand("set output power", {"output power": power_dBm})
            if "status" in resp.keys() and resp["status"] == "ok":
                ok = True
        return ok
    
    def get_output_power_dBm(self):
        if self.found:
            resp = self.send_commmand("get output power")
            if "status" in resp.keys() and resp["status"] == "ok":
                if "dBm" in resp.keys():
                    power_dBm = float(resp["dBm"])
        return power_dBm
    
    def set_output_enable(self, enable_state):
        ok = False
        if self.found:
            resp = self.send_commmand("set output enable", {"enable state": enable_state})
            if "status" in resp.keys() and resp["status"] == "ok":
                ok = True
        return ok
    
    def get_output_enable(self):
        if self.found:
            resp = self.send_commmand("get output enable")
            if "status" in resp.keys() and resp["status"] == "ok":
                if "output enabled" in resp.keys():
                    enable_state = float(resp["output enabled"])
        return enable_state

    def send_commmand(self, cmd, params = None):
        ret_val = {}
        msg = {"command": cmd}
        if params != None:
            msg.update(params)        
        self.sock.sendall(json.dumps(msg).encode("utf-8"))
        ready = select.select([self.sock], [], [], self.timeout)        
        if ready[0]:
            resp = self.sock.recv(1024).decode("utf-8")
            ret_val = json.loads(resp)
        return ret_val


if __name__ == "__main__":
    print("SignalGenerator tests:")
    
    sg = SignalGenerator()
    if sg.find():
        print("Signal Generator Service found at {}:{}".format(sg.address,str(sg.port)))
        if sg.connect():
            print("Found signal generator: {}".format(sg.description))
            
            print("Setting frequency to 10 MHz")
            input("Press Enter to continue...")
            if sg.set_frequency_Hz(10e6):
                print("Get frequency: {} Hz".format(sg.get_frequency_Hz()))
            else:
                print("Error: failed to set frequency")
                        
            print("Setting output power to -50 dBm")
            input("Press Enter to continue...")
            if sg.set_output_power_dBm(-50.0):
                print("Get output power: {} dBm".format(sg.get_output_power_dBm()))
            else:
                print("Error: failed to set output power")
            
            print("Setting output enable state to 'on'")
            input("Press Enter to continue...")
            if sg.set_output_enable(True):
                print("Get output enable state: {}".format(sg.get_output_enable()))
            else:
                print("Error: failed to set output enable state")
            
            print("Setting frequency to 20 MHz")
            input("Press Enter to continue...")
            if sg.set_frequency_Hz(20e6):
                print("Get frequency: {} Hz".format(sg.get_frequency_Hz()))
            else:
                print("Error: failed to set frequency")
                        
            print("Setting output power to -60 dBm")
            input("Press Enter to continue...")
            if sg.set_output_power_dBm(-60.0):
                print("Get output power: {} dBm".format(sg.get_output_power_dBm()))
            else:
                print("Error: failed to set output power")
            
            print("Setting output enable state to 'off'")
            input("Press Enter to continue...")
            if sg.set_output_enable(False):
                print("Get output enable state: {}".format(sg.get_output_enable()))
            else:
                print("Error: failed to set output enable state")
        else:
            print("Error: failed to connect to signal generator")
    else:
        print("Error: failed to find Signal Generator Service")