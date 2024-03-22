#!/usr/bin/env python3.7

#-------------------------------------------------------------
# Script takes a file of NMEA messages and sends them on a specified serial port.
#
# Run it like:
#     c:\Python37\python sendgps.py -p "COM26" -f "putty.log"
#-------------------------------------------------------------

import argparse, serial, time, datetime, sys

parser = argparse.ArgumentParser(description="Send NMEA Strings to a serial port.")
parser.add_argument('-p', '-p1', '--port', default='COM54', help="the serial port to use for unit tests. Default COM54")
parser.add_argument('-f', '--filename', default='gps_sample_data.log', help="file of NMEA messages to send, default gps_sample_data.log")

# ------------------------------------------------------------

# Runs the test using the serial port
def run_test(serial_port, filename):
    print('Starting')

    ser = None

    try:
        ser = serial.Serial(serial_port, 9600, timeout = 1.0, xonxoff = False, rtscts = False, dsrdtr = False)
        if ser.isOpen():
            print('Serial Port Opened')

            # open the input file and read it in
            with open(filename) as f:
                content = f.readlines()

            content = [x.strip() for x in content]

            count = 0
            for line in content:
                checksum_present = False
                if not line.startswith('$'):
                    pass
                else:
                    checksum = 0
                    for char in line:
                        if char not in ['$', '*']:
                            checksum = checksum ^ ord(char)
                        if char is '*':
                            checksum_present = True
                            break
                    if checksum_present == True:
                      line = '%s\r\n' % (line) 
                    else:
                      line = '%s*%02X\r\n' % (line, checksum)
                    print(count, line.strip())
                    count = count + 1
                    if line.startswith('$GPZDA') or line.startswith('$GNZDA'):
                        delay = 1
                    else:
                        delay = 0
                    ser.write(bytearray(line, 'ascii'))
                    time.sleep(delay)
            ser.close()

        else :
            print('Failed to open the serial port on test')

    except Exception as e:
        if ser:
            ser.close()
        traceback.print_exc()
        print('failed to load and start : %s' % (e))

    if ser:
        ser.close()
    print('Finished')

# ------------------------------------------------------------

if __name__ == '__main__':
    args = parser.parse_args()
    serial_port = args.port
    filename = args.filename
    print('serial port is %s, filename %s' % (serial_port, filename))
    run_test(serial_port, filename)
