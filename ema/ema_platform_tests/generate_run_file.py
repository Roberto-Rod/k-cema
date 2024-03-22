#!/usr/bin/python3

##############################################################################
# This script is intended to generate a run.sh file
##############################################################################

import argparse
import os

parser = argparse.ArgumentParser(description="Generate an EMA run.sh file")
parser.add_argument('-o', '--output_file', default='/run/media/mmcblk0p2/run.sh',
                    help="Output file. Default is /run/media/mmcblk0p2/run.sh")


# ------------------------------------------------------------
def write_file(output_file):
    try:
        f = open(output_file, "w")

        f.write("LIB_ROOT=/usr/local/lib\n")
        f.write("export FILE_ROOT=/run/media/mmcblk0p2\n")
        f.write("export LD_LIBRARY_PATH=${LIB_ROOT}/Boost:${LIB_ROOT}/OpenSSL:${LIB_ROOT}/OpenDDS\n")
        f.write("${FILE_ROOT}/drmd\n")
        f.write("${FILE_ROOT}/KCemaEMAApp -DCPSConfigFile ${FILE_ROOT}/rtps.ini\n")

        f.close()

        # Finally change the file permissions to 755
        os.chmod(output_file, 0o755)

    except OSError:
        print("Unable to open file: " + output_file)


# ------------------------------------------------------------
if __name__ == '__main__':
    args = parser.parse_args()
    output_file = args.output_file
    write_file(output_file)
