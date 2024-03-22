#!/usr/bin/env python3
"""
Procedural test script for KT-000-0143-00 EMA PCM PCB Production Test
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-e/--ema_com_port name of EMA Test Interface board COM port
-n/--ntm_com_port name of EMA PCM NTM Test Interface board COM port 
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
import time
from datetime import datetime

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from ema_test_intf_board import EmaTestInterfaceBoard
from pcm_ntm_test_intf_board import PcmNtmTestInterfaceBoard
from test import Test
from hardware_config_serial import HardwareConfigSerial

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
def pause_seconds(seconds, newline=False):
    """
    Utility function pauses for specified number of seconds, prints "." to terminal to
    provide feedback that the script is not hung
    :param seconds:
    :param newline:
    :return:
    """
    for i in range(seconds):
        print(".", end="", flush=True)
        time.sleep(1)
    if newline:
        print("")


def power_fail_test(ntm_interface):
    test_pass = True

    input("Set the Bench Power Supply voltage to +10.0 ± 0.1 V then press <Enter> ")
    cmd_success, asserted = ntm_interface.get_power_fail_asserted()
    if cmd_success and asserted:
        test_pass &= True
    else:
        test_pass &= False

    input("Set the Bench Power Supply voltage to +28.0 ± 0.1 V then press <Enter> ")
    cmd_success, asserted = ntm_interface.get_power_fail_asserted()
    if cmd_success and not asserted:
        test_pass &= True
    else:
        test_pass &= False

    log_str = " - Power Fail Test"
    if test_pass:
        log_str = "PASS" + log_str
    else:
        log_str = "FAIL" + log_str
    log.info(log_str)

    return test_pass


def rdac_adjust_test(ntm_interface):
    test_pass = True
    test_values = {"15 V": [15000, 1014], "32 V": [32000, 70], "28 V": [28000, 202]}

    # Set RDAC for required DC-DC output voltage allow to settle then test
    for test_voltage, values in test_values.items():
        if not ntm_interface.set_rdac(values[1]):
            test_pass &= False
            break
        pause_seconds(10, newline=True)
        rail_3v4_stby, rail_28v = ntm_interface.get_analog_op()

        log_str = " - DC-DC {} nominal [{} mV]".format(test_voltage, rail_28v)
        test_pass = Test.nom(rail_28v, nominal=values[0], allowed_error_percent=5) and test_pass

        if test_pass:
            log_str = "PASS" + log_str
        else:
            log_str = "FAIL" + log_str

        log.info(log_str)

    # Use the last +3V4_STBY reading to check the output rail
    if test_pass:
        log_str = " - +3V4_STBY Rail [{} mV]".format(rail_3v4_stby)
        test_pass = Test.nom(rail_3v4_stby, nominal=3400, allowed_error_percent=5) and test_pass

        if test_pass:
            log_str = "PASS" + log_str
        else:
            log_str = "FAIL" + log_str

        log.info(log_str)

    return test_pass


def rdac_set_50tp(ntm_interface):
    log_str = " - Set 50TP for +28V output"

    # Set the RDAC for 28 V then write it to 50TP memory
    if ntm_interface.set_rdac(202):
        if ntm_interface.set_50tp():
            log_str = "PASS" + log_str
            test_pass = True
        else:
            log_str = "FAIL" + log_str
            test_pass = False
    else:
        log_str = "FAIL" + log_str
        test_pass = False

    log.info(log_str)
    return test_pass


def ema_uart_echo_test(ema_interface):
    """
    Perform a UART echo test, test routine is:
    - Enable EMA Test Interface Board UART echo function
    - Perform echo test
    - Disable EMA Test Interface Board UART echo function
    :param ema_interface: :type: EmaTestInterfaceBoard
    :return: True if test passed, else False
    """
    test_result = False

    if ema_interface.set_uart_echo(True):
        test_result_str = " - EMA UART Echo Test"

        if ema_interface.uart_echo_test():
            test_result_str = "PASS" + test_result_str
            test_result = True
        else:
            test_result_str = "FAIL" + test_result_str
            test_result = False

        ema_interface.set_uart_echo(False)

        log.info(test_result_str)
    else:
        log.critical("*** Failed to Enable EMA Interface UART Echo! ***")

    return test_result


def pps_test(ema_interface, ntm_interface):
    """
    Peform a 1PPS pass through test:
    - Enabl
    :param ema_interface: :type: EmaTestInterfaceBoard
    :param ntm_interface: :type: PcmNtmTestInterfaceBoard
    :return: True if test passed, else False
    """
    test_result_str = " - 1PPS Test"
    test_result = True

    if ema_interface.set_pps(True):
        pause_seconds(3)
        test_result = ntm_interface.get_pps_detected() and test_result
        log.debug(test_result)
    else:
        log.critical("*** Failed to Enable EMA Interface 1PPS! ***")

    if ema_interface.set_pps(False):
        pause_seconds(3, newline=True)
        test_result = (not ntm_interface.get_pps_detected()) and test_result
        log.debug(test_result)
    else:
        log.critical("*** Failed to Disable EMA Interface 1PPS! ***")

    if test_result:
        test_result_str = "PASS" + test_result_str
    else:
        test_result_str = "FAIL" + test_result_str

    log.info(test_result_str)
    return test_result


def rf_mute_test(ema_interface, ntm_interface):
    """

    :param ema_interface: :type: EmaTestInterfaceBoard
    :param ntm_interface: :type: PcmNtmTestInterfaceBoard
    :return:
    """
    test_result_str = " - RF Mute Test"
    test_result = True

    if ema_interface.set_rf_mute(True):
        test_result = ntm_interface.get_rf_mute_asserted() and test_result
        log.debug(test_result)
    else:
        log.critical("*** Failed to Assert RF Mute Signal! ***")

    if ema_interface.set_rf_mute(False):
        test_result = (not ntm_interface.get_rf_mute_asserted()) and test_result
        log.debug(test_result)
    else:
        log.critical("*** Failed to De-assert RF Mute Signal! ***")

    if test_result:
        test_result_str = "PASS" + test_result_str
    else:
        test_result_str = "FAIL" + test_result_str

    log.info(test_result_str)
    return test_result


def fan_controller_temperature_test(ntm_interface):
    """

    :param ntm_interface: :type: PcmNtmTestInterfaceBoard
    :return:
    """
    temperature = ntm_interface.get_fan_controller_temp()
    test_result = 20 <= temperature <= 40

    test_result_str = " - Fan Controller Temperature Test [{} deg C]".format(temperature)

    if test_result:
        test_result_str = "PASS" + test_result_str
    else:
        test_result_str = "FAIL" + test_result_str

    log.info(test_result_str)
    return test_result


def fan_speed_test(ema_interface, ntm_interface):
    """

    :param ema_interface: :type: EmaTestInterfaceBoard
    :param ntm_interface: :type: PcmNtmTestInterfaceBoard
    :return:
    """
    test_result = True

    if not ema_interface.set_power_off(True):
        log.critical("*** Set Power Off Failed! ***")
    pause_seconds(1)
    if not ema_interface.set_power_off(False):
        log.critical("*** Set Power Off Failed! ***")
    pause_seconds(5)
    test_result = ntm_interface.get_fan_alert_asserted() and test_result

    if not ema_interface.set_power_off(True):
        log.critical("*** Set Power Off Failed! ***")
    pause_seconds(1)
    if not ema_interface.set_power_off(False):
        log.critical("*** Set Power Off Failed! ***")
    pause_seconds(1)
    ntm_interface.fan_controller_init()
    test_result = (not ntm_interface.get_fan_alert_asserted()) and test_result

    ntm_interface.fan_controller_push_temperature(50)
    pause_seconds(20)
    fan1_spd, fan2_spd = ntm_interface.get_fan_speeds()
    test_result = (9700 <= fan1_spd <= 10700) and test_result
    test_result = (9700 <= fan2_spd <= 10700) and test_result

    ntm_interface.fan_controller_push_temperature(72)
    pause_seconds(30, newline=True)
    fan1_spd, fan2_spd = ntm_interface.get_fan_speeds()
    test_result = (17300 <= fan1_spd <= 19100) and test_result
    test_result = (17300 <= fan2_spd <= 19100) and test_result

    ntm_interface.fan_controller_push_temperature(20)

    test_result_str = " - Fan Speed Test"
    if test_result:
        test_result_str = "PASS" + test_result_str
    else:
        test_result_str = "FAIL" + test_result_str
    log.info(test_result_str)

    return test_result


def set_and_get_hci(hci_interface, serial_no, rev_no, batch_no):
    test_pass = True

    test_pass = hci_interface.reset_hci() and test_pass
    test_pass = hci_interface.set_assembly_part_no("KT-000-0143-00") and test_pass
    test_pass = hci_interface.set_assembly_serial_no(serial_no) and test_pass
    test_pass = hci_interface.set_assembly_revision_no(rev_no) and test_pass
    test_pass = hci_interface.set_assembly_build_batch_no(batch_no) and test_pass

    if test_pass:
        log.info("PASS - Set HCI")
    else:
        log.info("FAIL - Set HCI")

    cmd_success, hci_data = hci_interface.get_hci()
    if cmd_success:
        log.info(hci_data.decode("UTF-8").replace("\r", ""))
        test_pass &= True
    else:
        log.info("Failed to read Hardware Configuration Information!")
        test_pass &= False

    return True


def main(ema_com_port, ntm_com_port, serial_no, rev_no, batch_no):
    """
    Executes tests and determines overall test script result
    :param ema_com_port: name of EMA Test Interface Board COM port :type: string
    :param ntm_com_port: name of PCM NTM Test Interface Board COM port :type: string
    :return: None
    """
    # Create test interface objects
    ema_interface = EmaTestInterfaceBoard(ema_com_port)
    ntm_interface = PcmNtmTestInterfaceBoard(ntm_com_port)
    hci_interface = HardwareConfigSerial(ntm_com_port)

    overall_pass = True

    log.info("KT-000-0143-00 EMA PCM PCB Test Script")
    overall_pass - fan_speed_test(ema_interface, ntm_interface) and overall_pass
    overall_pass = fan_controller_temperature_test(ntm_interface) and overall_pass
    overall_pass = ema_uart_echo_test(ema_interface) and overall_pass
    overall_pass = rf_mute_test(ema_interface, ntm_interface) and overall_pass
    overall_pass = pps_test(ema_interface, ntm_interface) and overall_pass
    overall_pass = rdac_adjust_test(ntm_interface) and overall_pass
    overall_pass = rdac_set_50tp(ntm_interface) and overall_pass
    overall_pass = power_fail_test(ntm_interface) and overall_pass
    overall_pass = set_and_get_hci(hci_interface, serial_no, rev_no, batch_no) and overall_pass

    if overall_pass:
        log.info("PASS - Overall Test Result")
    else:
        log.info("FAIL - Overall Test Result")

    log.info(datetime.now().strftime("%d/%m/%Y"))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0143-00 EMA PCM PCB Production Test Script")
    parser.add_argument("-e", "--ema_com_port", required=True, dest="ema_com_port", action="store",
                            help="Name of EMA Test Interface board COM port")
    parser.add_argument("-n", "--ntm_com_port", required=True, dest="ntm_com_port", action="store",
                            help="Name of EMA PCM NTM Test Interface board COM port")
    parser.add_argument("-s", "--serial_no", required=True, dest="serial_no", action="store",
                        help="Serial number of board under test, max length 15 characters")
    parser.add_argument("-r", "--rev_no", required=True, dest="rev_no", action="store",
                        help="Revision number of board under test, max length 15 characters")
    parser.add_argument("-b", "--batch_no", required=True, dest="batch_no", action="store",
                        help="Batch number of board under test, max length 15 characters")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    log_file_name = "KT-000-0143-00_{}_{}_{}.txt".format(args.serial_no, args.batch_no,
                                                         datetime.now().strftime("%Y%m%d%H%M%S"))
    logging.basicConfig(filename=log_file_name, filemode='w', format=fmt, level=logging.INFO, datefmt="%H:%M:%S")
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger().addHandler(console)

    main(args.ema_com_port, args.ntm_com_port, args.serial_no, args.rev_no, args.batch_no)
