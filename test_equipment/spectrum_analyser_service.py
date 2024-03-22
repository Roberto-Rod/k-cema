#!/usr/bin/env python3
"""
Spectrum Analyser Service Class
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
import sys, io
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

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class SpectrumAnalyserService:
    def __init__(self):
        self.sa = VisaTestEquipment("Spectrum Analyser")
        self.ip = None
        self.ips = []
        self.is_thread_running = False
        self.port = 7002
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
        service_name = "Spectrum Analyser Service {}".format(self.ip).replace(".", "-")
        registration_name = "%s.%s" % (service_name, service_type)
        properties = {'version:': '1.0'}
        info = ServiceInfo(type_=service_type, name=registration_name, addresses=[socket.inet_aton(self.ip)], port=self.port, properties=properties)
        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        atexit.register(lambda: zeroconf.close())


class SASServer(threading.Thread):
    def __init__(self, sck, addr, sas, accept):
        threading.Thread.__init__(self)
        self.sck = sck
        self.addr = addr
        self.sas = sas
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
                # Decode the command, read/write spectrum analyser and set response parameters
                try:
                    cmd = json.loads(data)
                    status = "fail"
                    params = {}
                    if "command" in cmd.keys():
                        if cmd["command"] == "query spectrum analyser available":
                            status = "ok"
                            if sas.sa.resource:
                                params["spectrum analyser available"] = True
                                params["description"] = sas.sa.visa_te.sa.details()
                            else:
                                params["spectrum analyser available"] = False
                        elif cmd["command"] == "set centre frequency":
                            if "frequency" in cmd.keys():
                                if sas.sa.visa_te.sa.set_centre_frequency_Hz(float(cmd["frequency"])):
                                    status = "ok"
                        elif cmd["command"] == "get centre frequency":
                            ok = True
                            if ok:
                                params["Hz"] = sas.sa.visa_te.sa.get_centre_frequency_Hz()
                                status = "ok"
                        elif cmd["command"] == "set span Hz":
                            if "set span" in cmd.keys():
                                if sas.sa.visa_te.sa.set_span_Hz(float(cmd["set span"])):
                                    status = "ok"
                        elif cmd["command"] == "get span Hz":
                            ok = True
                            if ok:
                                params["Hz"] = sas.sa.visa_te.sa.get_span_Hz()
                                status = "ok"
                        elif cmd["command"] == "set resolution bandwidth":
                            if "set resolution BW" in cmd.keys():
                                if sas.sa.visa_te.sa.set_resolution_BW_Hz(float(cmd["resolution"])):
                                    status = "ok"
                        elif cmd["command"] == "set reference level":
                            if "set reference" in cmd.keys():
                                if sas.sa.visa_te.sa.set_reference_level_dBm(float(cmd["reference"])):
                                    status = "ok"
                        elif cmd["command"] == "get reference level":
                            ok = True
                            if ok:
                                params["dBm"] = sas.sa.visa_te.sa.get_reference_level_dBm()
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


class SASAccept(threading.Thread):
    def __init__(self, host, port, sas, sa):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.sas = sas
        self.sa = sa
        self.stopped = False

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)
        try:
            self.s.bind((self.host, self.port))
            self.s.listen(1)
            self.sa.binding_success = True
            while not self.stopped:
                try:
                    (sck, addr) = self.s.accept()
                    SASServer(sck, addr, sas, self).start()
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        time.sleep(0.1)
                        continue
                    else:
                        log.info("ERROR - Exception: {}".format(e))
                        self.stopped = True
            self.s.close()
        except Exception as e:
            log.info("ERROR - Error trying to listen to {}:{}".format(self.host, self.port))
            self.sa.binding_success = False
            log.info(e)

    def quit(self):
        self.stopped = True

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    """ This module is NOT intended to be executed stand-alone """
    log.info("Starting spectrum analyser Service Test...")
    sas = SpectrumAnalyserService()
    [is_device_initalized, model] = sas.sa.device_specific_initialisation()
    if is_device_initalized:
        if sas.ips:
            n = 1
            sel = 1
            for ip in sas.ips:
                print("{}) {}".format(n, ip))
                n += 1
            try:
                if sel <= 1 or sel > len(sas.ips):
                    sel = 1
                    sas.ip = sas.ips[sel - 1]
                else:
                    sel = int(input())
            except:
                sel = 1
            log.info("INFO - Selecting network interface with IP address {}".format(sas.ip))
            log.info("INFO - Starting TCP/IP listener on port {}".format(sas.port))
            thread = SASAccept(sas.ip, sas.port, sas, sas.sa)
            thread.start()
            log.info("INFO - Registering service for spectrum analyser {}".format(model))
            sas.register_service()
            if sas.sa.binding_success:
                log.info("INFO - Registering spectrum analyser service successfull")
                log.info("INFO - Spectrum analyser service is running...")
                input("<press Enter to quit>\n")  
                thread.quit()
            else:
                thread.quit()
        else:
            log.info("ERROR - no candidate network interface found")
    else:
        log.info("ERROR: could not find spectrum analyser")
    log.info("INFO - Stopping Spectrum Analyser Service...")
    exit()

