#!/usr/bin/env python3
"""
Test CSAC and set it to 1PPS auto-sync mode
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import logging
import time
from enum import Enum

# Third-party imports -----------------------------------------------
import serial

# Our own imports ---------------------------------------------------
from dev_mem import DevMem

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class CsacTest:
    """
    Class which tests and configures the CSM CSAC
    """
    class Mode(Enum):
        ANALOG_TUNING = 0x0001
        PPS_PHASE_MEAS = 0x0004
        PPS_AUTO_SYNC = 0x0008
        DISCIPLINE = 0x0010
        ULTRA_LOW_POWER_MODE = 0x0020
        REQUIRE_CHECKSUM = 0x0040

    _RX_TX_TIMEOUT = 3.0
    # _SERIAL_PORT = "/dev/ttyCSAC"
    _SERIAL_PORT = "/dev/ttyUL5"
    _BAUD_RATE = 57600

    _CSM_SYNC_ADDRESS = 0x4000D004
    _CSM_CSAC_CLOCK_PRESENT_MASK = 0x4
    _CSM_1PPS_PRESENT_MASK = 0x2

    _MODE_ARGUMENT = {
        Mode.ANALOG_TUNING: "A",
        Mode.PPS_PHASE_MEAS: "M",
        Mode.PPS_AUTO_SYNC: "S",
        Mode.DISCIPLINE: "D",
        Mode.ULTRA_LOW_POWER_MODE: "U",
        Mode.REQUIRE_CHECKSUM: "C"
    }

    def __init__(self):
        """
        Class constructor
        :param None
        :return: None
        """
        self._serial_device = None
        try:
            self._serial_device = serial.Serial(port=self._SERIAL_PORT, timeout=self._RX_TX_TIMEOUT,
                                                baudrate=self._BAUD_RATE, bytesize=8, stopbits=serial.STOPBITS_ONE)
        except serial.serialutil.SerialException as e:
            log.error(e)

    def send_command(self, command):
        command = command.strip() + "\r\n"
        self._serial_device.write(bytes(command, "utf-8"))
        resp = self._serial_device.readline().decode("utf-8").strip()
        # Commands have been seen to fail intermittently if they are sent too close to each other
        # delay here to stop another command being sent immediately after the response has been received
        time.sleep(0.25)
        return resp

    def send_mode_command(self, command):
        resp = self.send_command(command)
        if resp:
            try:
                status = int(resp, 16)
                return status
            except ValueError:
                # Response didn't decode properly (probably doesn't look like hex)
                log.error("Error decoding response: '{}'".format(resp))
        return None

    def get_status(self):
        self._serial_device.write(b"\r\n")
        time.sleep(0.25)
        resp = self.send_command("!6")
        log.info(resp)
        headings = resp.split(",")
        resp = self.send_command("!^")
        log.info(resp)
        values = resp.split(",")
        return dict(zip(headings, values))

    def read_mode(self):
        value = self.send_mode_command("!M?")
        if value is not None:
            for mode in self.Mode:
                if (value & mode.value) != 0:
                    enabled = "Enabled"
                else:
                    enabled = "Disabled"
                log.info("{}: {}".format(mode, enabled))
            return True
        return False

    def disable_all_modes(self):
        for mode in self.Mode:
            if not self.disable_mode(mode):
                return False
        return True

    def disable_mode(self, mode):
        command = "!M{}".format(self._MODE_ARGUMENT[mode].lower())
        if self.send_mode_command(command) is None:
            log.info("Failed to disable: {}".format(mode))
            return False
        else:
            log.info("Disabled {}".format(mode))
            return True

    def enable_mode(self, mode):
        command = "!M{}".format(self._MODE_ARGUMENT[mode].upper())
        value = self.send_mode_command(command)
        if value is None:
            log.info("Failed to enable: {}".format(mode))
            return False
        else:
            if value & mode.value:
                log.info("Enabled {}".format(mode))
                return True

    def disable_checksum(self):
        # Treat this as a special command including the checksum itself so that we can unlock the device
        # if it is requiring command checksums
        command = "!Mc*2E\r\n"
        if self.send_mode_command(command) is None:
            log.info("Failed to disable command checksum")
            return False
        else:
            log.info("Disabled command checksum")
            return True

    def get_pps_phase(self):
        status = self.get_status()
        if "Phase" in status.keys():
            phase = status["Phase"]
            try:
                return int(phase)
            except ValueError:
                return phase
        return None

    def test_1pps_in(self):
        timeout = time.time() + 60  # 1 minute from now
        log.info("Waiting for 1PPS...")
        while True:
            if time.time() > timeout:
                log.error("Timed out waiting for 1PPS")
                return False
            phase = self.get_pps_phase()
            if isinstance(phase, int):
                # Log the detected phase. Note that this is arbitrary if the CSAC has not been set to PPS sync
                # since power-up. This will be 0 or close to 0 if the CSAC has been set to PPS sync.
                log.info("1PPS in detected (phase {})".format(phase))
                return True

    def test_1pps_out(self):
        reg = DevMem.read(self._CSM_SYNC_ADDRESS)
        if (reg & self._CSM_1PPS_PRESENT_MASK) == 0:
            log.info("1PPS out not detected at SoC")
            return False
        else:
            log.info("1PPS out detected at SoC")
            return True

    def test_10mhz_out(self):
        reg = DevMem.read(self._CSM_SYNC_ADDRESS)
        if (reg & self._CSM_CSAC_CLOCK_PRESENT_MASK) == 0:
            log.info("10 MHz out not detected at SoC")
            return False
        else:
            log.info("10 MHz out detected at SoC")
            return True

    def run_test(self):
        """
        Run the CSAC test routine
        :return: True if the test passes, else False
        """
        if self._serial_device is None or not self._serial_device.isOpen():
            log.error("Could not open serial port {}".format(self._SERIAL_PORT))
            return False

        log.info("Serial port {} opened".format(self._SERIAL_PORT))

        ok = True
        ok &= self.test_10mhz_out()
        ok &= self.test_1pps_out()
        ok &= self.disable_checksum()
        ok &= self.disable_all_modes()
        # Don't carry on if the test has failed up to here, avoid waiting for 1PPS input
        if ok:
            # Set the CSAC to PPS phase measurement mode to test the 1PPS input
            ok &= self.enable_mode(self.Mode.PPS_PHASE_MEAS)
            ok &= self.test_1pps_in()
            # Set the CSAC to PPS auto-sync mode as we want to field it in this mode
            ok &= self.enable_mode(self.Mode.PPS_AUTO_SYNC)

        return ok


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """
    Enable logging, run test and report the overall test result
    :return: None
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    csac = CsacTest()

    if csac.run_test():
        log.info("Overall Test Result:\t PASS")
    else:
        log.info("Overall Test Result:\t FAIL")

    return None


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    main()
