#!/usr/bin/env python3
"""
Utility module to create test script tgz zip archive.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
"-v", "--version", default="x-y-z", help="Test Script Archive Version"
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
import os
import shutil
import tarfile

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SW_PART_NO_STR = "KT-956-0258-00"

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

def main(version):
    """
    Generate platform test script archive.
    :param version: version number to append to output filename :type: string
    :return: N/A
    """
    working_folder_name = "test"
    tgz_filename = "{}_v{}.tgz".format(SW_PART_NO_STR, version)

    # Add files to working folder ready for archiving
    if os.path.isdir(working_folder_name):
        shutil.rmtree(working_folder_name)

    os.mkdir(working_folder_name)
    for fn in os.listdir("."):
        # Ignore PyCharm project folder, Python cach folders and previous archive folder
        if ".idea" not in os.path.realpath(fn) and "__pycache__" not in os.path.realpath(fn) and \
                "{}_v".format(SW_PART_NO_STR) not in fn:
            if os.path.isdir(fn) and fn != "test":
                shutil.copytree(fn, r"{}\{}".format(working_folder_name, fn))
            elif not os.path.isdir(fn):
                shutil.copy(fn, working_folder_name)

    # Create test script archive file
    if os.path.exists(tgz_filename):
        os.remove(tgz_filename)

    tgz = tarfile.open(tgz_filename, "w:gz")
    tgz.add(working_folder_name)
    tgz.close()

    # Delete the working folder and tar file
    if os.path.isdir(working_folder_name):
        shutil.rmtree(working_folder_name)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="Generate Test Script Archive Tool")
    parser.add_argument("-v", "--version", default="x-y-z", help="Test Script Archive Version")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args.version)
