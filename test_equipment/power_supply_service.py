#!/usr/bin/env python3
"""
Power Supply Service Class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
None

"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# Our own imports -------------------------------------------------------------
from visa_test_equipment import VisaTestEquipment

# stdlib imports --------------------------------------------------------------
from zeroconf import ServiceInfo, Zeroconf
from _ast import Try

import ifaddr
import socket
import sys
import logging
import atexit
import threading
import json
import errno
import time

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class PowerSupplyService:
    def __init__(self):
        self.psu = VisaTestEquipment("Power Supply")
        self.ip = None
        self.ips = []
        self.is_thread_running = False
        self.port = 7004
        self.select_ip()

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def select_ip(self):
        self.ip = None
        adapters = ifaddr.get_adapters()
        for adapter in adapters:
            name = adapter.nice_name
            # Ignore adapters which contain these terms...
            ignore = (name.find("Bluetooth") >= 0) or (name.find("Software Loopback") >= 0) or (name.find("Virtual") >= 0) or (name.find("VPN") >= 0)
            if not ignore:
                for ip in adapter.ips:
                    # Ignore IPv6 as these typically come back with ip.network_prefix >= 64
                    if ip.network_prefix <= 24:
                        # Accept link-local only for now
                        if ip.ip.startswith("192.168"):
                            self.ips.append(ip.ip)
        if len(self.ips) == 0:
            log.info("ERROR - No suitable adapters found")
        elif len(self.ips) == 1:
            self.ip = self.ips[0]
        else:
            # log.info("INFO - List IP address of adapters to use:")
            n = 1
            for ip in self.ips:
                # log.info("{}) {}".format(n, ip))
                n += 1  

    def register_service(self):
        service_type = "_kpms._tcp.local."
        service_name = "power supply Service {}".format(self.ip).replace(".", "-")
        registration_name = "%s.%s" % (service_name, service_type)
        properties = {'version:': '1.0'}
        info = ServiceInfo(type_=service_type, name=registration_name, addresses=[socket.inet_aton(self.ip)], port=self.port, properties=properties)
        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        atexit.register(lambda: zeroconf.close())


class PSUSServer(threading.Thread):
    def __init__(self, sck, addr, psus, accept):
        threading.Thread.__init__(self)
        self.sck = sck
        self.addr = addr
        self.psus = psus
        self.accept = accept

    def run(self):
        log.info("INFO - {} connected".format(repr(self.addr)))
        self.sck.setblocking(False)
        while not self.accept.stopped:
            try:
                data = self.sck.recv(1024).decode("utf=8")
                if not data:
                    break
                log.info("INFO - Received: '{}'".format(str(data)))
                # Decode the command, read/write power supply and set response parameters
                try:
                    cmd = json.loads(data)
                    status = "fail"
                    params = {}
                    if "command" in cmd.keys():
                        if cmd["command"] == "query power supply available":
                            status = "ok"
                            if psus.psu.resource:
                                params["power supply available"] = True
                                params["description"] = psus.psu.visa_te.psu.details()
                            else:
                                params["power supply available"] = False
                        elif cmd["command"] == "set enable":
                            if "enable state" in cmd.keys():
                                if cmd["enable state"] == "true" or cmd["enable state"] == True:
                                    if psus.psu.visa_te.psu.set_enabled(True):
                                        status = "ok"
                                elif cmd["enable state"] == "false" or cmd["enable state"] == False:
                                    if psus.psu.visa_te.psu.set_enabled(False):
                                        status = "ok"
                        elif cmd["command"] == "set DC voltage":
                            if "set voltage" in cmd.keys():
                                psus.psu.visa_te.psu.set_voltage(int(cmd["set voltage"]))
                                status = "ok"
                        elif cmd["command"] == "get DC voltage":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_voltage()
                                status = "ok"
                        elif cmd["command"] == "set DC current":
                            if "set current" in cmd.keys():
                                psus.psu.visa_te.psu.set_current(float(cmd["set current"]))
                                status = "ok"
                        elif cmd["command"] == "get DC current":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_current()
                                status = "ok"
                        elif cmd["command"] == "set DC voltage out":
                            if "set voltage out" in cmd.keys():
                                psus.psu.visa_te.psu.set_voltage(int(cmd["set voltage out"]))
                                status = "ok"
                        elif cmd["command"] == "get DC voltage out":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_voltage_out()
                                status = "ok"
                        elif cmd["command"] == "set DC current out":
                            if "set current out" in cmd.keys():
                                psus.psu.visa_te.psu.set_current(float(cmd["set current out"]))
                                status = "ok"
                        elif cmd["command"] == "get DC current":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_current_out()
                                status = "ok"
                        elif cmd["command"] == "get average current":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_average_current_out()
                                status = "ok"
                        elif cmd["command"] == "get power out":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_power_out()
                                status = "ok"
                        elif cmd["command"] == "get average power out":
                            ok = True
                            if ok:
                                params["V"] = psus.psu.visa_te.psu.get_average_power_out()
                                status = "ok"
                        elif cmd["command"] == "set over voltage protection":
                            if "set ovp" in cmd.keys():
                                psus.psu.visa_te.psu.set_ovp(int(cmd["set ovp"]))
                                status = "ok"
                        elif cmd["command"] == "set over current protection":
                            if "set ocp" in cmd.keys():
                                psus.psu.visa_te.psu.set_ocp(int(cmd["set ocp"]))
                                status = "ok"
                    # Send the response
                    self.send_response(status, params)
                except Exception as e:
                    log.info("ERROR: {}".format(e))
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time.sleep(0.1)
                    continue
                else:
                    # a "real" error occurred, e.g. other side disconnected
                    break
        self.sck.close()
        log.info("INFO - {} disconnected".format(repr(self.addr)))

    def send_response(self, status, params = None):
        msg = {"status": status}
        if params:
            msg.update(params)
        resp = json.dumps(msg).encode("utf-8")
        log.info("INFO - Sending: '{}'".format(str(resp, "utf-8")))
        self.sck.sendall(resp)


class PSUSAccept(threading.Thread):
    def __init__(self, host, port, psus, psu):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.psus = psus
        self.psu = psu
        self.stopped = False

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)
        try:
            self.s.bind((self.host, self.port))
            self.s.listen(1)
            self.psu.binding_success = True
            while not self.stopped:
                try:
                    (sck, addr) = self.s.accept()
                    PSUSServer(sck, addr, psus, self).start()
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        time.sleep(0.1)
                        continue
                    else:
                        log.info("Exception: {}".format(e))
                        self.stopped = True
            self.s.close()
        except Exception as e:
            log.info("ERROR - Error trying to listen to {}:{}".format(self.host, self.port))
            self.psu.binding_success = False
            log.info(e)

    def quit(self):
        self.stopped = True

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

    
# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------    
if __name__ == "__main__":
    """ This module is NOT intended to be executed stand-alone """
    log.info("INFO - Starting power supply Service Test...")
    psus = PowerSupplyService()
    [is_device_initalized, model] = psus.psu.device_specific_initialisation()
    if is_device_initalized:
        if psus.ips:
            n = 1
            sel = 1
            for ip in psus.ips:
                print("{}) {}".format(n, ip))
                n += 1
            try:
                if sel <= 1 or sel > len(psus.ips):
                    sel = 1
                    psus.ip = psus.ips[sel - 1]
                else:
                    sel = int(input())
            except:
                sel = 1
            log.info("INFO - Selecting network interface with IP address {}".format(psus.ip))
            log.info("INFO - Starting TCP/IP listener on port {}".format(psus.port))
            thread = PSUSAccept(psus.ip, psus.port, psus, psus.psu)
            thread.start()
            log.info("INFO - Registering service for power supply {}".format(model))
            psus.register_service()
            if psus.psu.binding_success:
                log.info("INFO - Registering power supply service successfull")
                log.info("INFO - Power supply service is running...")
                input("<press Enter to quit>\n")  
                thread.quit()
            else:
                thread.quit()
        else:
            log.info("ERROR - no candidate network interface found")
    else:
        log.info("ERROR - could not find power supply")
    log.info("INFO - Stopping Power Supply Service...")
    exit()


