import logging
import os
from cts_serial_msg_intf import *
from PyCRC.CRCCCITT import CRCCCITT

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

COM_PORT = "COM39"
WAIT_FOR_RESP_MSGS = True
ERASE_LINE = "\033[2K"
CURSOR_HOME = "\033[100D"

fmt = "%(asctime)s: %(message)s"
# Set logging level DEBUG to see detailed information
logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

FW_FILE = r"C:\workspace\k-cema\PcbTest\cts_pcb_production_test_files\cts_micro_operational_fw\KT-056-0265-00_v0-0-3-0.bin"
FW_FILE_SIZE = os.path.getsize(FW_FILE)
FW_FILE_CRC16 = CRCCCITT(version="FFFF").calculate(open(FW_FILE, mode="rb").read())
DATA_CHUNK_SIZE_BYTES = 240
print("File: {}\nFile Size (bytes): {}\nFile CRC-16: x{:4x}".format(FW_FILE, FW_FILE_SIZE, FW_FILE_CRC16))

with CtsSerialMsgInterface(COM_PORT, response_timeout=7.0) as c:
# with CtsSerialTcpMsgInterface("169.254.139.24", 32, response_timeout=7.0) as c:
    print("CTS Ping: {}".format(c.send_ping()))
    print("Start File Upload: {}".format(c.send_start_file_upload(FW_FILE_SIZE, FW_FILE_CRC16, check_for_resp=WAIT_FOR_RESP_MSGS)))

    with open(FW_FILE, mode="rb") as f:
        file_transfer_success = True
        chunk_no = 1
        total_chunks = int(FW_FILE_SIZE / DATA_CHUNK_SIZE_BYTES)
        chunk = bytearray(f.read(DATA_CHUNK_SIZE_BYTES))
        while chunk:
            if c.send_file_data(chunk, check_for_resp=WAIT_FOR_RESP_MSGS):
                print("Data transfer: {} %".format(int((chunk_no / total_chunks) * 100)))
                # print("{}{}Data transfer: {} %".format(ERASE_LINE, CURSOR_HOME, int((chunk_no / total_chunks) * 100)),
                #      end="", flush=True)
                # print("{}\t- Send File Data: True ({}-bytes)".format(chunk_no, len(chunk)))
                chunk_no += 1
                chunk = bytearray(f.read(DATA_CHUNK_SIZE_BYTES))
            else:
                print("Send File Data: False")
                file_transfer_success = False
                break

    if file_transfer_success:
        cmd_success, resp = c.verify_file_crc(FW_FILE_CRC16)

        if cmd_success:
            payload_version, test_msg_type, test_msg_version, file_type, crc_valid, file_crc = \
                c.unpack_verify_file_crc_response(resp)
            print("Verify File CRC: valid {}; expected x{:4x}; returned x{:4x}"
                  "".format(crc_valid, FW_FILE_CRC16, file_crc))
            print("Relaunch - {}".format(c.send_relaunch()))

        else:
            print("Verify File Crc: Command Failed")
