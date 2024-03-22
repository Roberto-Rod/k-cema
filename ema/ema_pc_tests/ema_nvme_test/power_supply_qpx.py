#!/usr/bin/env python3
import pyvisa
import math

from time import *


class PowerSupplyQPX:
    def __init__(self, reset_device=True, debug=False):
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.psu = None
        self.reset_device = reset_device
        self.debug = debug

    def __del__(self):
        if self.psu:
            self.psu.close()

    def find_and_initialise(self):
        self.resource = None
        resources = self.rm.list_resources()
        for res in resources:
            # This instrument does not fully support VXI-11, we need to use the COM port interface
            # find COM ports, open and query to look for device ID
            if res.startswith("ASRL"):
                self.resource = res
                if self.initialise_device():
                    print("Found and initialised QPX Power Supply: {}".format(res))
                    return True
                else:
                    self.resource = None
        print("ERROR: did not find a QPX Power Supply")
        return False

    def initialise_device(self):
        try:
            self.psu = self.rm.open_resource(self.resource)
        except:
            if self.psu:
                self.psu.close()
                print("Could not open resource: {}".format(self.resource))
            else:
                print("Resource busy: {}".format(self.resource))
            return False
        details = self.details()
        try:
            model = details.split(",")[1].strip()
            if model.startswith("QPX"):
                if self.reset_device:
                    return self.send_command("*RST")
                else:
                    return True
        except:
            pass
        self.psu.close()
        return False

    def details(self):
        return self.send_query("*IDN?")

    def send_command(self, cmd):
        if self.debug:
            print("send_command: {}".format(cmd))
        try:
            self.psu.write(cmd)
            return True
        except:
            print("ERROR - could not send command")
            return False

    def send_query(self, query):
        if self.debug:
            print("send_query: {}".format(query))
        try:
            return self.psu.query(query).strip()
        except:
            print("ERROR - could not send query")
            return False

    def set_enabled(self, enabled):
        if enabled:
            return self.send_command("OP1 1")
        else:
            return self.send_command("OP1 0")

    def dc_is_enabled(self):
        response = self.send_query("OP1?")
        return response == "1"

    def set_voltage(self, voltage):
        return self.send_command("V1 {}".format(voltage))

    def get_voltage(self):
        response = self.send_query("V1?")
        return float(response.split(" ")[1])

    def get_voltage_out(self):
        response = self.send_query("V1O?")
        return float(response.replace("V", ""))

    def set_current(self, voltage):
        return self.send_command("I1 {}".format(voltage))

    def get_current(self):
        response = self.send_query("I1?")
        return float(response.split(" ")[1])

    def get_current_out(self):
        response = self.send_query("I1O?")
        return float(response.replace("A", ""))

    def get_average_current_out(self, nr_readings=16, delay_s=0):
        readings = []
        for i in range(0, nr_readings):
            sleep(delay_s)
            readings.append(self.get_current_out())
        return round(sum(readings) / len(readings), 4)

    def get_power_out(self):
        return round(self.get_voltage_out() * self.get_current_out(), 4)

    def get_average_power_out(self, nr_readings=16, delay_s=0.1):
        # Use average current and an instantaneous voltage measurement as voltage
        # is stabilised by the PSU whilst current varies
        return round(self.get_voltage_out() * self.get_average_current_out(nr_readings, delay_s), 4)

    def set_ovp(self, voltage):
        return self.send_command("OVP1 {}".format(voltage))

    def get_ovp(self):
        response = self.send_query("OVP1?")
        return float(response.split(" ")[1])

    def set_ocp(self, voltage):
        return self.send_command("OCP1 {}".format(voltage))

    def get_ocp(self):
        response = self.send_query("OCP1?")
        return float(response.split(" ")[1])

    def set_sense_remote(self):
        return self.send_command("SENSE1 1")

    def set_sense_local(self):
        return self.send_command("SENSE1 0")

if __name__ == "__main__":
    psu = PowerSupplyQPX(reset_device=False)
    print("PowerSupplyQPX Test:")
    if psu.find_and_initialise():
        sleep(2)
        psu.set_voltage(24)
        psu.set_current(15)
        psu.set_ovp(45.5)
        psu.set_ocp(30.0)
        psu.set_sense_remote()
        psu.set_enabled(True)
        sleep(2)
        print("Details:           {}".format(psu.details()))
        print("Enabled:           {}".format(psu.dc_is_enabled()))
        print("Voltage Setting:   {} V".format(psu.get_voltage()))
        print("Voltage Out:       {} V".format(psu.get_voltage_out()))
        print("Current Setting:   {} A".format(psu.get_current()))
        print("Current Out:       {} A".format(psu.get_current_out()))
        print("Power Out:         {} W".format(psu.get_power_out()))
        print("Average Power Out: {} W".format(psu.get_average_power_out()))
        print("OVP Setting:       {} V".format(psu.get_ovp()))
        print("OCP Setting:       {} V".format(psu.get_ocp()))

        while True:
            print("Average Current:   {} A".format(psu.get_average_current_out(nr_readings=5000)))
