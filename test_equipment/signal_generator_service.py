#!/usr/bin/env python3
"""
NRP Power Supply Service Class
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
import atexit
import threading
import json
import errno
import time
import logging

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class SignalGeneratorService:
    def __init__(self):
        self.sg = VisaTestEquipment("Signal Generator")
        self.ip = None
        self.port = 7003
        self.ips = []
        self.is_thread_running = False
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
            log.info("No suitable adapters found")
        elif len(self.ips) == 1:
            self.ip = self.ips[0]
        else:
            # log.info("List IP address of adapters to use:")
            n = 1
            for ip in self.ips:
                # log.info("{}) {}".format(n, ip))
                n += 1

    def register_service(self):
        service_type = "_kpms._tcp.local."
        service_name = "Signal Generator Service {}".format(self.ip).replace(".", "-")
        registration_name = "%s.%s" % (service_name, service_type)
        properties = {'version:': '1.0'}
        info = ServiceInfo(type_=service_type, name=registration_name, addresses=[socket.inet_aton(self.ip)],
                           port=self.port, properties=properties)
        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        atexit.register(lambda: zeroconf.close())


class SGSServer(threading.Thread):
    def __init__(self, sck, addr, pms, accept):
        threading.Thread.__init__(self)
        self.sck = sck
        self.addr = addr
        self.pms = pms
        self.accept = accept

    def run(self):
        log.info("{} connected".format(repr(self.addr)))
        self.sck.setblocking(False)
        while not self.accept.stopped:
            try:
                data = self.sck.recv(1024).decode("utf=8")
                if not data:
                    break
                log.info("Received: '{}'".format(str(data)))
                # Decode the command, read/write signal generator and set response parameters
                try:
                    cmd = json.loads(data)
                    status = "fail"
                    params = {}
                    if "command" in cmd.keys():
                        if cmd["command"] == "query signal generator available":
                            status = "ok"
                            if sgs.sg.resource:
                                params["signal generator available"] = True
                                params["description"] = sgs.sg.visa_te.sg.details()
                            else:
                                params["signal generator available"] = False
                        elif cmd["command"] == "set frequency":
                            if "frequency" in cmd.keys():
                                if sgs.sg.visa_te.sg.set_frequency_Hz(float(cmd["frequency"])):
                                    status = "ok"
                        elif cmd["command"] == "get frequency":
                            ok = True
                            if ok:
                                params["Hz"] = sgs.sg.visa_te.sg.get_frequency_Hz()
                                status = "ok"
                        elif cmd["command"] == "set output power":
                            if "output power" in cmd.keys():
                                if sgs.sg.visa_te.sg.set_output_power_dBm(float(cmd["output power"])):
                                    status = "ok"
                        elif cmd["command"] == "get output power":
                            ok = True
                            if ok:
                                params["dBm"] = sgs.sg.visa_te.sg.get_output_power_dBm()
                                status = "ok"
                        elif cmd["command"] == "set output enable":
                            if "enable state" in cmd.keys():
                                if cmd["enable state"] == "true" or cmd["enable state"] == True:
                                    if sgs.sg.visa_te.sg.set_output_enable(True):
                                        status = "ok"
                                elif cmd["enable state"] == "false" or cmd["enable state"] == False:
                                    if sgs.sg.visa_te.sg.set_output_enable(False):
                                        status = "ok"
                        elif cmd["command"] == "get output enable":
                            ok = True
                            if ok:
                                params["output enabled"] = sgs.sg.visa_te.sg.get_output_enable()
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
        log.info("{} disconnected".format(repr(self.addr)))

    def send_response(self, status, params = None):
        msg = {"status": status}
        if params:
            msg.update(params)
        resp = json.dumps(msg).encode("utf-8")
        log.info("Sending: '{}'".format(str(resp, "utf-8")))
        self.sck.sendall(resp)


class SGSAccept(threading.Thread):
    def __init__(self, host, port, sgs, sg):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.sgs = sgs
        self.sg = sg
        self.stopped = False

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)
        try:
            self.s.bind((self.host, self.port))
            self.s.listen(1)
            self.sg.binding_success = True
            while not self.stopped:
                try:
                    (sck, addr) = self.s.accept()
                    SGSServer(sck, addr, sgs, self).start()
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
            self.sg.binding_success = False
            log.info(e)

    def quit(self):
        self.stopped = True

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    log.info("Starting Signal Generator Service Test...")
    sgs = SignalGeneratorService()
    [is_device_initalized, model] = sgs.sg.device_specific_initialisation()
    if is_device_initalized:
        if sgs.ips:
            n = 1
            sel = 1
            for ip in sgs.ips:
                print("{}) {}".format(n, ip))
                n += 1
            try:
                if sel <= 1 or sel > len(sgs.ips):
                    sel = 1
                    sgs.ip = sgs.ips[sel - 1]
                else:
                    sel = int(input())
            except:
                sel = 1
            log.info("Selecting network interface with IP address {}".format(sgs.ip))
            log.info("Starting TCP/IP listener on port {}".format(sgs.port))
            thread = SGSAccept(sgs.ip, sgs.port, sgs, sgs.sg)
            thread.start()
            log.info("Registering service for signal generator {}".format(model))
            sgs.register_service()
            if sgs.sg.binding_success:
                log.info("Registering signal generator service successfull.")
                log.info("Signal generator service is running...")
                input("<press Enter to quit>\n")
                thread.quit()
            else:
                thread.quit()
        else:
            log.info("ERROR - no candidate network interface found")
    else:
        log.info("ERROR: could not find signal generator")
    log.info("Stopping Signal Generator Service...")
    exit()
