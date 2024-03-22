#!/usr/bin/env python3
"""
Module for simulating the Battery Box unit
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-s --serial_port Simulator serial port
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
from threading import Event, Thread

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from bb_serial_msg_intf import BbSerialMsgInterface, BbMsgId, BbStaticBatteryParameters, \
    BbDynamicBatteryParameters, BbBatteryStatus, BbSoftwareVersionInfo

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
class BbSimulator:
    """
    Class for simulating a battery box serial interface
    """

    def __init__(self):
        """ Class constructor """
        self._serial_port = None
        self._baud_rate = 115200
        self._thread = None
        self._event = Event()

    def __del__(self):
        """ Class constructor """
        self.stop()

    def start(self, serial_port, baud_rate=115200):
        """
        Starts the Battery Box simulator running
        :param serial_port: serial port to attach to :type string
        :param baud_rate: baud rate of serial link :type integer
        :return: True if started, else False :type: Boolean
        """
        log.debug("Starting Battery Box Simulator...")

        try:
            self._serial_port = serial_port
            self._baud_rate = baud_rate
            self._thread = Thread(target=self.__thread_run)
            self._thread.start()

        except Exception as ex:
            self._event.set()
            log.info("Failed to start Battery Box Simulator: {}".format(ex))

        if not self._event.is_set():
            return True
        else:
            return False

    def stop(self):
        """
        Stop the MessageHandler from running
        :return: NA
        """
        if not self._event.is_set():
            self._event.set()

    def __thread_run(self):
        """
        Battery Box Simulator thread
        :return: NA
        """
        bsp = BbStaticBatteryParameters()
        bsp.payload_version = 0x01
        bsp.battery_1a_serial_no = 7684
        bsp.battery_1a_design_capacity = 9300
        bsp.battery_1b_serial_no = 7684
        bsp.battery_1b_design_capacity = 9300
        bsp.battery_2a_serial_no = 1186
        bsp.battery_2a_design_capacity = 9300
        bsp.battery_2b_serial_no = 1186
        bsp.battery_2b_design_capacity = 9300

        bdp = BbDynamicBatteryParameters()
        bdp.payload_version = 0
        bdp.battery_1a_voltage = 1
        bdp.battery_1a_current = 5
        bdp.battery_1a_state_of_charge = 9
        bdp.battery_1a_temperature = 13
        bdp.battery_1a_status = BbBatteryStatus()
        bdp.battery_1a_status.error_code = 7
        bdp.battery_1a_status.initialised = True
        bdp.battery_1a_status.discharging = True
        bdp.battery_1a_remaining_energy = 17
        bdp.battery_1b_voltage = 2
        bdp.battery_1b_current = 6
        bdp.battery_1b_state_of_charge = 10
        bdp.battery_1b_temperature = 14
        bdp.battery_1b_status = BbBatteryStatus()
        bdp.battery_1b_status.error_code = 7
        bdp.battery_1b_status.initialised = True
        bdp.battery_1b_status.discharging = True
        bdp.battery_1b_remaining_energy = 18
        bdp.battery_2a_voltage = 3
        bdp.battery_2a_current = 7
        bdp.battery_2a_state_of_charge = 11
        bdp.battery_2a_temperature = 15
        bdp.battery_2a_status = BbBatteryStatus()
        bdp.battery_2a_status.error_code = 7
        bdp.battery_2a_status.initialised = True
        bdp.battery_2a_remaining_energy = 19
        bdp.battery_2a_status.discharging = True
        bdp.battery_2b_voltage = 4
        bdp.battery_2b_current = 8
        bdp.battery_2b_state_of_charge = 12
        bdp.battery_2b_temperature = 16
        bdp.battery_2b_status = BbBatteryStatus()
        bdp.battery_2b_status.error_code = 7
        bdp.battery_2b_status.initialised = True
        bdp.battery_2b_status.discharging = True
        bdp.battery_2b_remaining_energy = 20

        sw_info = BbSoftwareVersionInfo()
        sw_info.payload_version = 0
        sw_info.sw_major = 1
        sw_info.sw_minor = 2
        sw_info.sw_patch = 3
        sw_info.sw_build = 4567

        with BbSerialMsgInterface(self._serial_port, self._baud_rate) as bsmh:
            while not self._event.is_set():
                rx_msg = bsmh.smh.get_from_rx_queue()
                if rx_msg is not None:
                    log.debug("Rx Msg: {}".format(rx_msg))
                    msg_header = bsmh.smh.unpack_message_header(rx_msg)

                    if msg_header.msg_id == BbMsgId.GET_STATIC_BATTERY_PARAMETERS.value:
                        bsmh.send_static_battery_parameters(bsp, msg_header.seq_no)
                        log.info("Received and handled Get Static Battery Parameters message")
                    elif msg_header.msg_id == BbMsgId.GET_DYNAMIC_BATTERY_PARAMETERS.value:
                        bsmh.send_dynamic_battery_parameters(bdp, msg_header.seq_no)
                        log.info("Received and handled Get Dynamic Battery Parameters message")
                    elif msg_header.msg_id == BbMsgId.GET_SOFTWARE_VERSION_NUMBER.value:
                        bsmh.send_software_version(sw_info, msg_header.seq_no)
                        log.info("Received and handled Get Software Version message")
                    elif msg_header.msg_id == BbMsgId.PING.value:
                        log.info("Received and handled Ping message")
                    else:
                        # Unhandled message, ignore it
                        log.info("Unhandled message: {}".format(msg_header.msg_id))


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def run(serial_port, baud_rate):
    """
    Run the battery simulation
    :param serial_port:
    :param baud_rate:
    :return: N/A
    """
    bb_sim = BbSimulator()
    bb_sim.start(serial_port, baud_rate)
    input("Press <Enter>  to exit...\n")
    bb_sim.stop()


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure
    """
    parser = argparse.ArgumentParser(description="NEO Battery Box Simulator")
    parser.add_argument("-s", "--serial_port", help="Simulator serial port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    run(args.serial_port, 115200)
