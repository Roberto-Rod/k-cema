#!/usr/bin/env python3
"""
Test script for KT-000-0140-00 battery signals, call script to execute test
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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

# stdlib imports -------------------------------------------------------
import argparse
import logging
import time

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from csm_zero_micro_test_intf import CsmTamperDevices, CsmTamperChannels, CsmTamperChannelStatus, CsmGpiSignals, \
    CsmGpoSignals, CsmZeroiseMircoTestInterface

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def disable_all_anti_tamper_channels(csm_micro_interface):
    """
    Disable all of the anti-tamper device channels
    :param csm_micro_interface: CSM Zeroise Micro test interface :type: CsmZeroiseMircoTestInterface
    :return: True if anti-tamper device channels disabled, else False
    """
    success = True
    for device in CsmTamperDevices:
        # Set all the TEBx bits to '0'
        for channel in CsmTamperChannels:
            success = csm_micro_interface.set_anti_tamper_channel_enable(device, channel, False) and success
        # Read the Flags registers to make sure nIRQ signals are cleared, Flags register is shared so just check
        # channel 0
        success = csm_micro_interface.get_tamper_channel_status(device, CsmTamperChannels.CHANNEL_0)

    return success


def rtc_test(csm_micro_interface):
    """
    Get 2x RTC readings 1-second apart and check that the values are not the same
    :param csm_micro_interface: CSM Zeroise Micro test interface :type: CsmZeroiseMircoTestInterface
    :return: True if test passes, else False
    """
    test_pass = True
    at_rtc_1, pcd_rtc_1 = csm_micro_interface.get_rtc()
    log.debug(at_rtc_1)
    log.debug(pcd_rtc_1)

    time.sleep(1)

    at_rtc_2, pcd_rtc_2 = csm_micro_interface.get_rtc()
    log.debug(at_rtc_2)
    log.debug(pcd_rtc_2)

    if at_rtc_1 == "" or at_rtc_2 == "" or at_rtc_1 == at_rtc_2:
        test_pass &= False

    if pcd_rtc_1 == "" or pcd_rtc_2 == "" or pcd_rtc_1 == pcd_rtc_2:
        test_pass &= False

    log.info("{} - Anti-Tamper RTC Test".format("PASS" if test_pass else "FAIL"))
    return test_pass


def case_switch_test(csm_micro_interface):
    """
    Test steps:
        - Ask user to hold down case switch
        - Arm sensor and check GPI and register status
        - Ask user to release case switch
        - Check GPI signal and registers for tamper detection
        - Disable sensor and check register status
    disable case switch
    :param csm_micro_interface: CSM Zeroise Micro test interface :type: CsmZeroiseMircoTestInterface
    :return: True if test passes, else False
    """
    test_pass = True
    input("Press and HOLD down the board under test case switch, S1 <Enter>")
    # Arm the tamper sensor
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                                   CsmTamperChannels.CHANNEL_0, True) and test_pass

    # Check the IRQ_TAMPER signal is NOT asserted
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_TAMPER)
    if not cmd_success or asserted:
        test_pass &= False

    # Check that the tamper channel status is ARMED_READY
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.ARMED_READY:
        test_pass &= False

    # Trigger the tamper sensor
    input("RELEASE the board under test case switch, S1 <Enter>")

    # Check that the IRQ_TAMPER signal has been asserted
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_TAMPER)
    if not cmd_success or not asserted:
        test_pass &= False

    # Check that the tamper channel status is TAMPERED
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.TAMPERED:
        test_pass &= False

    # Disable the tamper channel and check its status is reported correctly
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                                   CsmTamperChannels.CHANNEL_0, False) and test_pass

    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.DISABLED:
        test_pass &= False

    # Determine test success
    log.info("{} - Case Tamper Switch (S1) Test".format("PASS" if test_pass else "FAIL"))
    return test_pass


def light_sensor_test(csm_micro_interface):
    """
    Test steps:
        - Ask user to cover light sensor
        - Arm sensor and check GPI and register status
        - Ask user to power-down the board under test
        - Check powered-down by sending a command that will fail
        - Ask user to uncover light sensor
        - Check tamper status by reading registers, in battery mode IRQ is pulsed so this can't be read
        - De-assert ZER_PWR_HOLD to turn off zeroise micro, full command response not received so command fails
        - Ask user to power-on board under test
        - Disable the sensor and check register status
    :param csm_micro_interface: CSM Zeroise Micro test interface :type: CsmZeroiseMircoTestInterface
    :return: True if test passes, else False
    """
    test_pass = True
    input("COVER the board under test light sensor, Q14 <Enter>")
    # Arm the tamper sensor
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                                   CsmTamperChannels.CHANNEL_1, True) and test_pass
    # Check the IRQ_TAMPER signal is NOT asserted
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_TAMPER)
    if not cmd_success or asserted:
        test_pass &= False
    # Check that the tamper channel status is ARMED_READY
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                        CsmTamperChannels.CHANNEL_1)
    if not cmd_success or status != CsmTamperChannelStatus.ARMED_READY:
        test_pass &= False

    # Power-down the board under test
    input("Press and hold the Keypad Power Button for >3 seconds to power-down the +12V DC-DC converter <Enter>")

    # Try to check the IRQ_TAMPER signal status - command WILL FAIL as the Zeroise Micro powered-down
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_TAMPER)
    if cmd_success:
        test_pass &= False

    input("UNCOVER the board under test light sensor, Q14 <Enter>")
    time.sleep(2)

    # Check that the tamper channel status is TAMPERED
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                        CsmTamperChannels.CHANNEL_1)
    if not cmd_success or status != CsmTamperChannelStatus.TAMPERED:
        test_pass &= False
    # De-assert the ZER_PWR_HOLD signal, command WILL FAIL as full response won't be received
    if csm_micro_interface.set_gpo_signal(CsmGpoSignals.ZER_PWR_HOLD, False):
        test_pass &= False

    # Power on the board under test
    input("Press the Keypad Power Button to enable the +12V DC-DC converter <Enter>")

    # Disable the tamper channel and check its status is reported correctly
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                                   CsmTamperChannels.CHANNEL_1, False) and test_pass

    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                        CsmTamperChannels.CHANNEL_1)
    if not cmd_success or status != CsmTamperChannelStatus.DISABLED:
        test_pass &= False

    log.info("{} - Light Sensor (Q14) Test".format("PASS" if test_pass else "FAIL"))
    return test_pass


def power_cable_detect_test(csm_micro_interface):
    """
    Test steps:
        - Ask USER to make power cable detect loop back
        - Arm sensor and check GPI and register status
        - Ask USER to break power cable detect loop back
        - Check GPI and register status for tamper detected
        - Ask USER to make power cable detect loop back
        - Arm sensor and check register status
        - Ask USER to break power cable detect loopback and power down the board under test
        - Check the SoM PGOOD_3V3_SUP signal is low
        - Ask the USER to power on the board under test
        - Check the SoM PGOOD_3V3_SUP signal is high
        - Disable sensor and check register status
    :param csm_micro_interface: CSM Zeroise Micro test interface :type: CsmZeroiseMircoTestInterface
    :return: True if test passes, else False
    """
    test_pass = True

    # Arm the tamper sensor
    input("MAKE the Power Cable Detection loop back (K-CEMA CSM Master Test Cable, S1) <Enter>")
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                   CsmTamperChannels.CHANNEL_0, True) and test_pass

    # Check the IRQ_CABLE_UNPLUG signal is NOT asserted
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_CABLE_UNPLUG)
    if not cmd_success or asserted:
        log.debug("0")
        test_pass &= False

    # Check that the tamper channel status is ARMED_READY
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.ARMED_READY:
        log.debug("1")
        test_pass &= False

    # Trigger the tamper sensor
    input("BREAK the Power Cable Detection loop back (K-CEMA CSM Master Test Cable, S1) <Enter>")

    # Check that the IRQ_CABLE_UNPLUG signal has been asserted
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_CABLE_UNPLUG)
    if not cmd_success or not asserted:
        test_pass &= False

    # Check that the tamper channel status is TAMPERED
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.TAMPERED:
        test_pass &= False

    # Arm the tamper sensor
    input("MAKE the Power Cable Detection loop back (K-CEMA CSM Master Test Cable, S1) <Enter>")
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                   CsmTamperChannels.CHANNEL_0, True) and test_pass

    # Check that the tamper channel status is ARMED_READY
    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.ARMED_READY:
        log.debug("1")
        test_pass &= False

    # Trigger the tamper sensor
    input("BREAK the Power Cable Detection loop back (K-CEMA CSM Master Test Cable, S1) <Enter>")

    # Check that the IRQ_CABLE_UNPLUG signal has been asserted
    cmd_success, asserted = csm_micro_interface.get_gpi_signal_asserted(CsmGpiSignals.IRQ_CABLE_UNPLUG)
    if not cmd_success or not asserted:
        test_pass &= False

    # Power-down the unit
    input("Press and hold the Keypad Power Button for >3 seconds to power-down the +12V DC-DC converter <Enter>")

    # Check that the PGOOD_3V3_SUP signal is NOT asserted
    cmd_success, asserted = csm_micro_interface.get_pgood_3v3_sup_asserted()
    if not cmd_success or asserted:
        test_pass &= False

    # Power on the board under test
    input("Press the Keypad Power Button to enable the +12V DC-DC converter <Enter>")

    # Check that the PGOOD_3V3_SUP signal is asserted
    cmd_success, asserted = csm_micro_interface.get_pgood_3v3_sup_asserted()
    if not cmd_success or not asserted:
        test_pass &= False

    # Disable the tamper channel and check its status is reported correctly
    test_pass = csm_micro_interface.set_anti_tamper_channel_enable(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                   CsmTamperChannels.CHANNEL_0, False) and test_pass

    cmd_success, status = csm_micro_interface.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                        CsmTamperChannels.CHANNEL_0)
    if not cmd_success or status != CsmTamperChannelStatus.DISABLED:
        test_pass &= False

    log.info("{} - Power Cable Detection Test".format("PASS" if test_pass else "FAIL"))
    return test_pass


def run_test(com_port):
    """
    Run the test
    :param com_port: name of serial port for CSM Zeroise Micro test interface :type string
    :return: True if
    """
    czm = CsmZeroiseMircoTestInterface(com_port)
    test_pass = True

    test_pass = disable_all_anti_tamper_channels(czm) and test_pass
    test_pass = rtc_test(czm) and test_pass
    test_pass = case_switch_test(czm) and test_pass
    test_pass = light_sensor_test(czm) and test_pass
    test_pass = power_cable_detect_test(czm) and test_pass

    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0140-00 CSM Battery Signal Production Test")
    parser.add_argument("-m", "--csm_micro_port", required=True, dest="csm_micro_port", action="store",
                        help="Name of CSM Zeroise Microcontroller COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    if run_test(args.csm_micro_port):
        log.info("PASS - Overall Test Result")
    else:
        log.info("FAIL - Overall Test Result")
