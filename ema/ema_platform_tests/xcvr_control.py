#!/usr/bin/env python3
import os
import subprocess
import socket
from time import sleep
from enum import IntEnum

from devmem import *


class JESD204BSource(IntEnum):
    NVME = 1
    Tone = 2
    DC = 3


class XcvrControl:
    REG_XCVR_CONTROL = 0x40015000
    REG_XCVR_CLK_CONTROL = 0x40015008
    REG_JESD204B_MUX = 0x4001C000
    REG_TEST_TONE_AMP = 0x4001D000
    REG_TEST_DC_AMP = 0x4001D008

    XCVR_CONTROL_RESET_MASK = 0x00000001
    XCVR_CONTROL_TX_EN_MASK = 0x00000002
    XCVR_CONTROL_LD_MASK = 0x80000000

    XCVR_CLK_CONTROL_STATUS0_MASK = 0x00000004
    XCVR_CLK_CONTROL_SYSREF_MASK = 0x00000002
    XCVR_CLK_CONTROL_RESET_MASK = 0x00000001

    JESD204B_MUX_UPDATE_OFFS = 0x00
    JESD204B_MUX_UPDATE_VAL = 0x02
    JESD204B_MUX_SOURCE_OFFS = 0x40
    JESD204B_MUX_SOURCE_NVME = 0x00
    JESD204B_MUX_SOURCE_TONE = 0x01
    JESD204B_MUX_SOURCE_DC = 0x02

    def __init__(self):
        os.popen("killall xcvrtool").read()
        self.sock = socket.socket()
        self.port = 7000
        self.sock.settimeout(10)
        try:
            subprocess.Popen(["./xcvrtool"])
            sleep(1)
        except FileNotFoundError as e:
            print("ERROR: {}".format(e))

    def __del__(self):
        self.sock.close()
        os.popen("killall xcvrtool").read()

    def connect(self):
        try:
            self.sock.connect(('127.0.0.1', self.port))
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
        MAX_XCVR_TUNE_ATTEMPTS = 10
        ok = True

        tuned = False
        attempts = 0
        while ok and not tuned and attempts < MAX_XCVR_TUNE_ATTEMPTS:
            self.sock.send("set frequency {}".format(freq_MHz).encode("utf-8"))
            resp = self.sock.recv(1024)
            if len(resp) == 0:
                print("ERROR: server hung up")
                ok = False
            else:
                resp = resp.decode("utf-8").strip()
                if resp == "OK: PLL set":
                    tuned = True
            attempts += 1

        return ok and tuned

    def set_synth(self, freq_MHz):
        MAX_SYNTH_TUNE_ATTEMPTS = 10
        ok = True
        locked = False
        attempts = 0
        while ok and not locked and attempts < MAX_SYNTH_TUNE_ATTEMPTS:
            self.sock.send("set synth {}".format(freq_MHz).encode("utf-8"))
            resp = self.sock.recv(1024)
            if len(resp) == 0:
                print("ERROR: server hung up")
                ok = False
            resp = resp.decode("utf-8").strip()
            if resp == "OK: synth set":
                sleep(0.5)
                print("Check synth lock detect: ", end="", flush=True)
                locked = self.is_synth_locked()
                print("{}".format("Locked" if locked else "Not Locked"))
            attempts += 1
        ok = ok and locked
        return ok

    def enable_tx_mode(self):
        MAX_TX_MODE_TIMEOUTS = 3
        timeouts = 0
        self.sock.send("tx mode".encode("utf-8"))
        while True:
            try:
                resp = self.sock.recv(1024)
                if len(resp) == 0:
                    print("ERROR: server hung up")
                    return False
                else:
                    resp = resp.decode("utf-8").strip()
                    print(resp)
                    if resp == "OK: Tx mode enabled":
                        return True
                    if resp == "ERROR: Failed to enable Tx mode":
                        return False
            except Exception as e:
                timeouts += 1
                if timeouts == MAX_TX_MODE_TIMEOUTS:
                    print("ERROR: timeout waiting for Tx mode")
                    return False

    def set_tx_att(self, tx_att_mdB):
        MAX_TX_ATT_ATTEMPTS = 3
        attempts = 0
        while attempts < MAX_TX_ATT_ATTEMPTS:
            self.sock.send("set tx att {}".format(tx_att_mdB).encode("utf-8"))
            resp = self.sock.recv(1024)
            if len(resp) == 0:
                print("ERROR: server hung up")
                ok = False
            resp = resp.decode("utf-8").strip()
            if resp == "OK: Tx attenuation set":
                return True
            if resp == "ERROR: Failed to set Tx attenuation":
                return False
            attempts += 1
        return False

    def set_tx_path(self, path):
        MAX_TX_ATT_ATTEMPTS = 3
        attempts = 0
        while attempts < MAX_TX_ATT_ATTEMPTS:
            self.sock.send("set tx path {}".format(path).encode("utf-8"))
            resp = self.sock.recv(1024)
            if len(resp) == 0:
                print("ERROR: server hung up")
                ok = False
            resp = resp.decode("utf-8").strip()
            if resp == "OK: Tx path set":
                return True
            if resp == "ERROR: Failed to set Tx path":
                return False
            attempts += 1
        return False

    def is_synth_locked(self):
        return (DevMem.read(self.REG_XCVR_CONTROL) & self.XCVR_CONTROL_LD_MASK) != 0

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

    def reset(self, rst=True):
        if rst:
            return DevMem.clear(self.REG_XCVR_CLK_CONTROL, self.XCVR_CLK_CONTROL_RESET_MASK) and\
                   DevMem.clear(self.REG_XCVR_CONTROL, self.XCVR_CONTROL_RESET_MASK)
        else:
            return DevMem.set(self.REG_XCVR_CLK_CONTROL, self.XCVR_CLK_CONTROL_RESET_MASK) and \
                   DevMem.set(self.REG_XCVR_CONTROL, self.XCVR_CONTROL_RESET_MASK)

    def tx_en(self, en=True):
        if en:
            return DevMem.set(self.REG_XCVR_CONTROL, self.XCVR_CONTROL_TX_EN_MASK)
        else:
            return DevMem.clear(self.REG_XCVR_CONTROL, self.XCVR_CONTROL_TX_EN_MASK)

    def sysref_ext_request(self, enable=True):
        if enable:
            return DevMem.set(self.REG_XCVR_CLK_CONTROL, self.XCVR_CLK_CONTROL_SYSREF_MASK)
        else:
            return DevMem.clear(self.REG_XCVR_CLK_CONTROL, self.XCVR_CLK_CONTROL_SYSREF_MASK)

    def jesd204b_stream_select(self, source):
        # Find the mux value for the requested source
        mux_value = None
        if source == JESD204BSource.NVME:
            mux_value = self.JESD204B_MUX_SOURCE_NVME
        elif source == JESD204BSource.Tone:
            mux_value = self.JESD204B_MUX_SOURCE_TONE
        elif source == JESD204BSource.DC:
            mux_value = self.JESD204B_MUX_SOURCE_DC
        if mux_value is not None:
            DevMem.write(self.REG_JESD204B_MUX + self.JESD204B_MUX_SOURCE_OFFS, int(mux_value))
            # Transfer the new AXI-S switch settings
            DevMem.write(self.REG_JESD204B_MUX + self.JESD204B_MUX_UPDATE_OFFS, self.JESD204B_MUX_UPDATE_VAL)
            return True
        return False

    def set_test_tone_amplitude(self, amplitude):
        reg_val = int(amplitude) & 0x00FFFFFF
        DevMem.write(self.REG_TEST_TONE_AMP, reg_val)
        return True

    def set_test_dc_amplitude(self, amplitude):
        DevMem.write(self.REG_TEST_DC_AMP, int(amplitude) << 16)
        return True


if __name__ == "__main__":
    xcvr = XcvrControl()
    if xcvr.initialise():
        print("Transceiver initialised")
    else:
        exit

    if xcvr.set_frequency(1200):
        print("Transceiver tuned to 1200 MHz")
    else:
        exit

    print("Power: {}".format(xcvr.read_power()))
