#!/usr/bin/env python3
from find_service import *
import socket
import select
import json


class PowerMeter:
    def __init__(self, timeout=10):
        self.address = "0.0.0.0"
        self.port = 0
        self.timeout = timeout
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.found = False
        self.description = "<not found>"
        self.frequency_Hz = 100e6

    def __del__(self):
        self.sock.close()

    def find(self, ip_addr=None):
        # Allow 2 minutes to find service so that operator has a chance to start the service
        # if it isn't already running
        location = FindService.find_pms(False, ip_addr, 120)
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
        resp = self.send_commmand("query power meter available")
        if "status" in resp.keys() and resp["status"] == "ok":
            if "power meter available" in resp.keys() and\
               (resp["power meter available"] == "true" or resp["power meter available"]):
                self.found = True
            if "description" in resp.keys():
                self.description = resp["description"]

        return self.found

    def zero(self):
        ok = False
        if self.found:
            resp = self.send_commmand("zero power meter")
            if "status" in resp.keys() and resp["status"] == "ok":
                ok = True
        return ok

    def set_offset(self, offset):
        ok = False
        if self.found:
            resp = self.send_commmand("set cable offset", {"offset": offset})
            if "status" in resp.keys() and resp["status"] == "ok":
                ok = True
        return ok
        
    def set_average_count(self, count):
        ok = False
        if self.found:
            resp = self.send_commmand("set average count", {"count": count})
            if "status" in resp.keys() and resp["status"] == "ok":
                ok = True
        return ok

    def get_reading_dBm(self):
        reading = -100.0
        if self.found:
            for attempt in range(1, 11):
                resp = self.send_commmand("get reading", {"frequency": self.frequency_Hz})
                if "status" in resp.keys() and resp["status"] == "ok":
                    if "dBm" in resp.keys():
                        reading = resp["dBm"]
                if reading > -100:
                    break
        return reading

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
    print("PowerMeter tests:")

    pm = PowerMeter()
    if pm.find():
        print("Power Meter Service found at {}:{}".format(pm.address,str(pm.port)))
        if pm.connect():
            print("Found power meter: {}".format(pm.description))

            print("Terminate power meter and disable RF source")
            input("Press Enter to continue...")

            # Zero power meter
            print("Zero power meter: ", end = "", flush = True)
            if pm.zero():
                print("OK")
            else:
                print("FAIL")

            # Set offset to 0.0 dB
            print("Enable RF source")
            input("Press Enter to continue...")
            print("Set offset to 0.0 dB: ", end = "", flush = True)
            if pm.set_offset(0):
                print("OK")
            else:
                print("FAIL")

            # Get readings, calibrating power meter to 20 MHz, 100 MHz, 8000 MHz
            print("Get reading @ 20 MHz: ", end = "", flush = True)
            pm.frequency_Hz = 20e6
            print(pm.get_reading_dBm())
            print("Get reading @ 100 MHz: ", end = "", flush = True)
            pm.frequency_Hz = 100e6
            print(pm.get_reading_dBm())
            print("Get reading @ 8000 MHz: ", end = "", flush = True)
            pm.frequency_Hz = 8000e6
            print(pm.get_reading_dBm())

            # Set offset to 30.5 dB
            print("Set offset to 30.5 dB: ", end = "", flush = True)
            if pm.set_offset(30.5):
                print("OK")
            else:
                print("FAIL")

            # Get reading, calibrating power meter to 100 MHz
            print("Get reading @ 100 MHz: ", end = "", flush = True)
            pm.frequency_Hz = 100e6
            print(pm.get_reading_dBm())
        else:
            print("Error: failed to connect to power meter")
    else:
        print("Error: failed to find Power Meter Service")
