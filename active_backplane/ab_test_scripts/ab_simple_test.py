#!/usr/bin/env python3
"""
Simple script file to test the functionality of th AbSerialMsgInterface class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Kirintec
#
# -----------------------------------------------------------------------------
from ab_serial_msg_intf import AbSerialMsgInterface, AbMsgId, AbMsgPayloadLen
import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

NO_TESTS = 10
COM_PORT = "COM4"
BAUD_RATE = 115200

if __name__ == "__main__":
    fmt = "%(asctime)s: %(message)s"
    # Set logging level DEBUG to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    # absi = AbSerialMsgInterface()
    # log.info("Started Active Backplane: {}".format(absi.start(COM_PORT, BAUD_RATE)))

    pass_count = 0
    fail_count = 0

    for i in range(0, NO_TESTS):
        with AbSerialMsgInterface(COM_PORT, BAUD_RATE) as absi:
            result = absi.send_ping()
            log.info("{} Ping {}".format(result, i))

            result, msg = absi.get_command(AbMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                           AbMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)
            if result:
                payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                    absi.unpack_get_software_version_number_response(msg)
                log.info("{} Sw Ver: V{}.{}.{}:{}".format(result, sw_major, sw_minor, sw_patch, sw_build))
                pass_count += 1
            else:
                log.info("{} Sw Ver: none".format(result))
                fail_count += 1

            result, msg = absi.get_command(AbMsgId.GET_HARDWARE_INFO,
                                           AbMsgPayloadLen.GET_HARDWARE_INFO)
            if result:
                payload_version, assy_part_no, assy_rev_no, assy_serial_no, \
                    assy_build_date_batch_no, bare_pcb_rev, mod_level = \
                    absi.unpack_get_hardware_info_response(msg)
                log.info("{} Hw Info: Assy PN-{}; Assy Rev-{}: Assy SN-{}; Assy BD BN-{}; PCB Rev-{}; Mod Lev-{}".format(
                    result, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no, bare_pcb_rev, mod_level))
                pass_count += 1
            else:
                log.info("{} Tw Info: none".format(result))
                fail_count += 1

            result, msg = absi.get_command(AbMsgId.GET_UNIT_INFO,
                                           AbMsgPayloadLen.GET_UNIT_INFO)
            if result:
                payload_version, status, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no = \
                    absi.unpack_get_unit_info_response(msg)
                log.info("{} Unit Info: Assy PN-{}; Assy Rev-{}: Assy SN-{}; Assy BD BN-{}; Status-{}".format(
                    result, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no, status))
                pass_count += 1
            else:
                log.info("{} Unit Info: none".format(result))
                fail_count += 1

            result, msg = absi.get_command(AbMsgId.GET_BIT_INFO,
                                           AbMsgPayloadLen.GET_BIT_INFO)
            if result:
                payload_version, flags, voltage_1v0_mv, voltage_2v5_mv, \
                    ambient_temp_deg, eth_sw_temp_deg, eth_phy_temp_deg, micro_temp_deg = \
                    absi.unpack_get_bit_info_response(msg)
                log.info("{} BIT Info: Flags x{}; +1V0: {} mV; +2V5: {} mV; Amb Temp: {} dC; Eth Sw Temp: {} dC; "
                         "Eth Phy Temp: {} dC;  Uc Temp: {} dC".format(
                            result, format(flags, '02x'), voltage_1v0_mv, voltage_2v5_mv, ambient_temp_deg,
                            eth_sw_temp_deg, eth_phy_temp_deg, micro_temp_deg))
                pass_count += 1
            else:
                log.info("{} BIT Info: none".format(result))
                fail_count += 1

            result, slot_no = absi.get_slot_no("DC-A6-32-AD-11-AE")

            if result:
                log.info("{} Slot No: {}".format(result, slot_no))
                pass_count += 1
            else:
                log.info("{} Get Slot No: none".format(result))
                fail_count += 1

    log.info("Pass Count: {}".format(pass_count))
    log.info("Fail Count: {}".format(fail_count))
    # absi.stop()
