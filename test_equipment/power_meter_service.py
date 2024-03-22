#!/usr/bin/env python3
"""
NRP Power Meter Service Class
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
import logging
import ifaddr
import socket
import sys
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

class PowerMeterService:
    """
    Power Meter Service Class: Instantiates a power meter visa test equipment class (model agnostic) and find IP address adapters
    """
    def __init__(self):
        """
        Class constructor
        :param None: 
        """
        self.pm = VisaTestEquipment("Power Meter")
        self.ip = None
        self.ips = []
        self.is_thread_running = False
        self.port = 7001
        self.select_ip()

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)
    
    def __del__(self):
        print("PMS object deleted!!!")
        self.stopped = True

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
        service_name = "Power Meter Service {}".format(self.ip).replace(".", "-")
        registration_name = "%s.%s" % (service_name, service_type)
        properties = {'version:': '1.0'}
        info = ServiceInfo(type_ = service_type, name = registration_name, addresses = [socket.inet_aton(self.ip)], port = self.port, properties = properties)
        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        atexit.register(lambda: zeroconf.close())


class PMSServer(threading.Thread):
    def __init__(self, sck, addr, pms, accept):
        threading.Thread.__init__(self)
        self.sck = sck
        self.addr = addr
        self.pms = pms
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
                # Decode the command, poll power meter and set response parameters
                try:
                    cmd = json.loads(data)
                    status = "fail"
                    params = {}
                    if "command" in cmd.keys():
                        if cmd["command"] == "query power meter available":
                            status = "ok"
                            if pms.pm.resource:
                                params["power meter available"] = True
                                params["description"] = pms.pm.visa_te.pm.details()
                            else:
                                params["power meter available"] = False
                        elif cmd["command"] == "zero power meter":
                            if pms.pm.visa_te.pm.zero():
                                status = "ok"
                        elif cmd["command"] == "set cable offset":
                            if "offset" in cmd.keys():
                                if pms.pm.visa_te.pm.set_offset(float(cmd["offset"])):
                                    status = "ok"
                        elif cmd["command"] == "set average count":
                            if "count" in cmd.keys():
                                if pms.pm.visa_te.pm.set_average_count(int(cmd["count"])):
                                    status = "ok"
                        elif cmd["command"] == "get reading":
                            ok = True
                            if "frequency" in cmd.keys():
                                if not pms.pm.visa_te.pm.set_frequency_Hz(float(cmd["frequency"])):
                                    ok = False
                            if ok:
                                params["dBm"] = pms.pm.visa_te.pm.get_reading_dBm()
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
        log.info("Sending: '{}'".format(str(resp, "utf-8")))
        self.sck.sendall(resp)


class PMSAccept(threading.Thread):
    def __init__(self, host, port, pms, pm):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.pms = pms
        self.pm = pm
        self.stopped = False

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)
        try:
            self.s.bind((self.host, self.port))
            self.s.listen(1)
            self.pm.binding_success = True
            while not self.stopped:
                try:
                    (sck, addr) = self.s.accept()
                    PMSServer(sck, addr, pms, self).start()
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        time.sleep(0.1)
                        continue
                    else:
                        log.info("ERROR - Exception: {}".format(e))
                        self.stopped = True
            self.s.close()
        except:
            log.info("ERROR - Error trying to listen to {}:{}".format(self.host, self.port))
            self.pm.binding_success = False

    def quit(self):
        self.stopped = True

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------



# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("INFO - Starting Power Meter Service...")
    pms = PowerMeterService()
    [is_device_initalized, model] = pms.pm.device_specific_initialisation()
    if is_device_initalized:
        if pms.ips:
            n = 1
            sel = 1
            for ip in pms.ips:
                print("{}) {}".format(n, ip))
                n += 1
            try:
                if sel <= 1 or sel > len(pms.ips):
                    sel = 1
                    pms.ip = pms.ips[sel - 1]
                else:
                    sel = int(input())
            except:
                sel = 1
            log.info("INFO - Selecting network interface with IP address {}".format(pms.ip))
            log.info("INFO - Starting TCP/IP listener on port {}".format(pms.port))
            thread = PMSAccept(pms.ip, pms.port, pms, pms.pm)
            thread.start()
            log.info("INFO - Registering service for power meter {}".format(model))
            pms.register_service()
            if pms.pm.binding_success:
                log.info("INFO - Registering power meter service successfull")
                log.info("INFO - Power meter service is running...")
                input("<press Enter to quit>\n")  
                thread.quit()
            else:
                thread.quit()
        else:
            log.info("ERROR - no candidate network interface found")
    else:
        log.info("ERROR: could not find power meter")
    log.info("INFO - Stopping Power Meter Service...")
    exit()

