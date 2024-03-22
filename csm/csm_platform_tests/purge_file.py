#!/usr/bin/python3
"""
This module is used to purge files from disk
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-f/--file_name Name of file to purge including full path
-d/--dir_name Name of directory to purge
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
import os
import os.path

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
BLK_SIZE = 512
FILE_EXCLUSION_LIST = ["system.bin", "image.ub"]

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
def purge_file(fn):
    """
    Purges a file from disk, overwrites file size with zeroes, on a Flash drive
    clearing file contents down to zero should not lead to file block reallocation
    but this is not guaranteed
    :param fn: name of file to be purged :type string
    :return: True if file purged, else False, raises ValueError exception if fn is not a string
    """
    if not isinstance(fn, str):
        raise ValueError("Value must be a string!")

    try:
        # If the file is not writable change its mode
        if not os.access(fn, os.W_OK):
            os.chmod(fn, 0o777)

        with open(fn, "wb") as f:
            # Overwrite the file contents with zeroes
            bytes_to_write = os.stat(fn).st_size
            zeroes = bytearray(BLK_SIZE)

            while bytes_to_write > 0:
                if bytes_to_write > BLK_SIZE:
                    bytes_written = f.write(zeroes)
                else:
                    zeroes = bytearray(bytes_to_write)
                    bytes_written = f.write(zeroes)

                bytes_to_write -= bytes_written

        # And finally remove the file from the filesystem
        os.remove(fn)

        if not os.access(fn, os.W_OK):
            log.info("OK: File purged: {}".format(fn))
            ret_val = True
        else:
            log.info("*** FAIL: File NOT purged: {}".format(fn))
            ret_val = False

    except Exception as err:
        log.critical("*** FAIL: {} ***".format(err))
        ret_val = False

    return ret_val


def purge_directory(dn):
    """
    Purges all the files in a directory, filenames in FILE_EXCLUSION_LIST will not be purged
    :param dn: name of directory to be purged :type string
    :return: True if directory purged, else False, raises ValueError exception if dn is not a string
    """
    if not isinstance(dn, str):
        raise ValueError("Value must be a string!")

    ret_val = True

    try:
        if os.path.isdir(dn):
            file_list = [f for f in os.listdir(dn) if os.path.isfile(os.path.join(dn, f))]
            log.debug(file_list)
            for f in file_list:
                if f not in FILE_EXCLUSION_LIST:
                    ret_val = purge_file(os.path.join(dn, f)) and ret_val

            if ret_val:
                log.info("OK: Directory purged: {}".format(dn))
            else:
                log.info("*** FAIL: Directory NOT purged: {}".format(dn))

        else:
            log.critical("*** FAIL: not a directory: {} ***".format(dn))
            ret_val = False

    except Exception as err:
        log.critical("*** FAIL: {} ***".format(err))
        ret_val = False

    return ret_val


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="Purge file from disk")
    parser.add_argument("-f", "--file_name", dest="file_name", action="store", default="",
                        help="Name of file to purge including full path")
    parser.add_argument("-d", "--dir_name", dest="dir_name", action="store", default="",
                        help="Name of directory to purge")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    if args.file_name != "":
        purge_file(args.file_name)

    if args.dir_name != "":
        purge_directory(args.dir_name)
