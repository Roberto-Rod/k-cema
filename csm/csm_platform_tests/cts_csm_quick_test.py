#!/usr/bin/env python3
"""
This file contains utility classes and methods for an SSH client.  It makes
use of the fabric library Connection class for maintaining the SSH connection.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
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

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from cts_serial_msg_intf import *
import exp_power_disable
from gbe_switch import SerialGbeSwitch 

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
def on_off_test():
    """
    Test the CTS Power Enable signal is working.
    :return: True test passes, else False
    """
    input("Observe the Bench Power Supply Current, <Enter> to continue...")
    exp_power_disable.expansion_slot_power_disable(1, True)
    answer = input("Has the Bench Power Supply Current DECREASED by ~100 mA? (Y/N) <Enter> ")
    ret_val = (answer.upper() == "Y")
    
    exp_power_disable.expansion_slot_power_disable(1, False)
    answer = input("Has the Bench Power Supply Current INCREASED by ~100 mA? (Y/N) <Enter> ")
    ret_val = (answer.upper() == "Y") and ret_val
        
    log.info("{} - On/off Test".format("PASS" if ret_val else "FAIL"))    
    return ret_val
    
    
def ethernet_test():
    """
    Do a quick ping test to check that the Ethernet interface is working.
    :return: True test passes, else False
    """
    with SerialGbeSwitch("/dev/ttyEthSw") as gs:
        # This method does a ping as part of the discovery process
        time.sleep(10.0)
        ret_val = (len(gs.find_lwip_autoip_addresses()) == 1)

    log.info("{} - Ethernet Test".format("PASS" if ret_val else "FAIL"))
    return ret_val
    
    
def set_assy_config_info(uart, serial_no, rev_no, batch_no):
    """
    Set the assembly configuration information.
    :return: True if information set successfully, else False
    """
    with CtsSerialMsgInterface(uart) as c:
        ret_val = c.send_set_unit_info("KT-900-0057-00", rev_no, serial_no, batch_no)
        
        result, msg = c.get_command(CtsMsgId.GET_UNIT_INFO, CtsMsgPayloadLen.GET_UNIT_INFO)
        if result:
            payload_version, status, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no = \
                c.unpack_get_unit_info_response(msg)
            log.info("Assembly Config Info:\n\tStatus:\t\t{}\n\tPart No:\t{}\n\tRev No:\t\t{}\n\tSerial No:\t{}\n\tBatch No:\t{}"
                     "".format(status, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no))
        
    log.info("{} - Set Assembly Configuration Information".format("PASS" if ret_val else "FAIL"))
    return ret_val    


def tx_test(uart):
    """
    Test the tx paths, one tone per path.
    :return: True if test passes, else False
    """
    test_freq = [410000, 1100000, 1950000, 4200000]
    ret_val = True
    
    with CtsSerialMsgInterface(uart) as c:
        input("Connect the CTS Antenna Port to a Spectrum Analyser, <Enter> to continue...")
        
        for freq in test_freq:
            input("Set Spectrum Analyser Centre Frequency {} MHz, Span 1 MHz, Ref Level +20dBm.\n"
                  "Tone will be output for 10-seconds, check level is +9 to 13 dBm (allowing for cable loss).\n"
                  "<Enter> to continue...".format(freq / 1000))
            test_pass = c.send_start_scan(2, freq, 10000, 0, 0, check_resp_nok=True)
            time.sleep(3.0)
            answer = input("Was tone output as expected? (Y/N) <Enter> ")
            test_pass = (answer.upper() == "Y") and test_pass
            
            log.info("{} - Tx {} MHz Test".format("PASS" if test_pass else "FAIL", freq / 1000)) 
            ret_val = test_pass and ret_val        
        
    return ret_val


def rf_detector_calibration(uart):
    """
    Calibrate the RF detector, tests the rx paths.
    Slope and offset indices:
        0 - 20 to 500 MHz
        1 - 500 to 800 MHz
        2 - 800 to 2000 MHz
        3 - 2000 to 2600 MHz
        4 - 2600 to 3000 MHz
        5 - 3000 to 4400 MHz
        6 - 4400 to 4670 MHz
        7 - 4670 to 6000 MHz
    :return: True if calibration successful, else False
    """
    cal_freq = [250000, 650000, 1400000, 2300000, 2800000, 3700000, 4535000, 5335000]
    ret_val = True
    
    with CtsSerialMsgInterface(uart) as c:
        input("Connect the CTS Antenna Port to a Signal Generator, <Enter> to continue...")
        
        rf_cal_power_0_dbm1 = 100    # +10.0 dBm
        scan_mode = 1
        scan_dwell_time_ms = 50
        scan_tx_atten_0_db5 = 0
        scan_rx_atten_0_db5 = 63
        slope_0dp1_points = []
        offset_mv_points = []   
        
        for freq in cal_freq:
            input("Set Signal Generator Frequency {} MHz, Amplitude +10.0 dBm (allowing for cable loss).\n"
                  "<Enter> to continue...".format(freq / 1000))
            test_pass = c.send_start_scan(scan_mode, freq, scan_dwell_time_ms,
                                          scan_tx_atten_0_db5, scan_rx_atten_0_db5, check_resp_nok=True)
            time.sleep(scan_dwell_time_ms / 1000.0)
            result, msg = c.get_command(CtsMsgId.GET_SCAN_STATUS_MSG_ID, CtsMsgPayloadLen.GET_SCAN_STATUS)
            
            test_pass = result and test_pass
            if result:
                payload_version, status, rf_detector_power_0dbm1, rf_detector_voltage_mv_p10dbm, remaining_dwell_time_ms = \
                    c.unpack_get_scan_status_response(msg)
                test_pass = (rf_detector_voltage_mv_p10dbm > 800) and test_pass
            
            input("Set Signal Generator Frequency {} MHz, Amplitude -10.0 dBm (allowing for cable loss).\n"
                  "<Enter> to continue...".format(freq / 1000))
            test_pass = c.send_start_scan(scan_mode, freq, scan_dwell_time_ms,
                                          scan_tx_atten_0_db5, scan_rx_atten_0_db5, check_resp_nok=True) and test_pass
            time.sleep(scan_dwell_time_ms / 1000.0)
            result, msg = c.get_command(CtsMsgId.GET_SCAN_STATUS_MSG_ID, CtsMsgPayloadLen.GET_SCAN_STATUS)
            
            test_pass = result and test_pass
            if result:
                payload_version, status, rf_detector_power_0dbm1, rf_detector_voltage_mv_n10dbm, remaining_dwell_time_ms = \
                    c.unpack_get_scan_status_response(msg)
                             
            ret_val = test_pass and ret_val            
            if test_pass:
                offset_mv_points.append(rf_detector_voltage_mv_p10dbm)
                slope_0dp1 = int((rf_detector_voltage_mv_p10dbm - rf_detector_voltage_mv_n10dbm) / 2)
                slope_0dp1_points.append(slope_0dp1)
                log.info("PASS - RF Detector Measurement {} MHz: {} - {}"
                         "".format(freq / 1000, rf_detector_voltage_mv_p10dbm, slope_0dp1))
            else:
                log.info("FAIL - RF Detector Measurement Failure!")
                break
        
        # Only do this if measurements were successful
        if ret_val:
            ret_val = c.send_set_rf_cal_table(rf_cal_power_0_dbm1,
                                              slope_0dp1_points, 
                                              offset_mv_points, 
                                              check_resp_nok=True)
            with open("/run/media/mmcblk1p2/cts_rf_detector_cal.txt", "w") as f:
                f.write("RF Calibration Power (0.1 dBm): {}\n".format(rf_cal_power_0_dbm1))
                f.write("Offset (mV), Slope (0.1 d.p.)\n")
                for i in range(0, len(cal_freq)):
                    f.write("{}, {}\n".format(offset_mv_points[i], slope_0dp1_points[i]))
            
            log.info("{} - Set RF Detector Calibration Table".format("PASS" if ret_val else "FAIL"))
                                              
    return ret_val


def main(kw_args):
    """
    Execute tets procedure
    :param kw_args: command line parameters
    :return: N/A
    """
    ret_val = rf_detector_calibration(vars(kw_args).get("uart", ""))
    ret_val = tx_test(vars(kw_args).get("uart", "")) and ret_val
    ret_val = on_off_test() and ret_val
    ret_val = ethernet_test() and ret_val
    ret_val = set_assy_config_info(vars(kw_args).get("uart", ""),
                                   vars(kw_args).get("rev_no", ""),
                                   vars(kw_args).get("serial_no", ""), 
                                   vars(kw_args).get("batch_no", "")) and ret_val
                                   
    log.info("{} - Overall Test Result".format("PASS" if ret_val else "FAIL"))
    
    
# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="CTS CSM Quick Test")
    parser.add_argument("-b", "--batch_no", help="CTS Assembly Batch No.")
    parser.add_argument("-r", "--rev_no", help="CTS Assembly Rev No.")
    parser.add_argument("-s", "--serial_no", help="CTS Assembly Serial No.")
    parser.add_argument("-u", "--uart", help="Serial UART")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args)
