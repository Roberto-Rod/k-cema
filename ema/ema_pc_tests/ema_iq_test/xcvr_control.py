#!/usr/bin/env python3
import os
import subprocess
import socket
from time import sleep


class XcvrControl:
    def __init__(self, host):
        os.popen("killall xcvrtool").read()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = 7000
        self.sock.settimeout(10)

    def __del__(self):
        self.sock.close()

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            return True
        except ConnectionRefusedError as e:
            print("ERROR: {}".format(e))
        return False

    def initialise(self):
        timeouts = 0
        self.sock.send("initialise".encode("utf-8"))
        while True:
            try:
                resp = self.sock.recv(1024)
                if len(resp) == 0:
                    print("ERROR: server hung up")
                    return False
                else:
                    resp = resp.decode("utf-8").strip()
                    print(resp)
                    if resp == "OK: Transceiver initialised":
                        return True
                    if resp == "ERROR: Failed to initialise transceiver":
                        return False
            except Exception as e:
                timeouts += 1
                if timeouts == 12:
                    print("ERROR: timeout waiting for transceiver initialisation")
                    return False

    def set_frequency(self, freq_MHz):
        self.sock.send("set frequency {}".format(freq_MHz).encode("utf-8"))
        resp = self.sock.recv(1024)
        if len(resp) == 0:
            print("ERROR: server hung up")
            return False
        resp = resp.decode("utf-8").strip()
        if resp == "OK: PLL set":
            return True
        return False

    def read_power(self):
        self.sock.send("read power".encode("utf-8"))
        resp = self.sock.recv(1024)
        if len(resp) == 0:
            print("ERROR: server hung up")
        else:
            try:
                reported_power = float(resp.decode("utf-8"))
                # 0.0 is reported when there is no input power
                if reported_power != 0.0:
                    return reported_power
            except (ValueError, TypeError) as e:
                print("ERROR: {}".format(e))
        return -100.0
