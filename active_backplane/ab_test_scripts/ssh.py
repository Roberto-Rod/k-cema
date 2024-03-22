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
import logging

# Third-party imports -----------------------------------------------
from fabric import Connection, runners

# Our own imports ---------------------------------------------------

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
class SSH:
    """
    Utility class provides a wrappper to a fabric library Connection instance
    used to maintain an SSH client connection.
    """
    def __init__(self, address, username, password):
        """ Class constructor """
        self.client = Connection(host=address, user=username, port=22,
                                 connect_kwargs={"password": password})
        self.client.run("")

    def __del__(self):
        """" Class destructor - close the client connection """
        self.client.close()

    def __enter__(self):
        """ Context manager - entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the client connection"""
        self.client.close()

    def close(self):
        """" Close the connection """
        self.client.close()

    def send_command(self, command):
        """
        Execute a shell command on the remote end of this connection.
        :param command: Command to execute
        :return: A runners.Result object
        """
        if self.client.is_connected:
            output = self.client.run(command, warn=True, hide=True)
        else:
            raise RuntimeError("ERROR: could not execute command - connection is closed")

        return output

    def send_file(self, local, remote):
        """
        Upload a file from the local filesystem to the current connection.
        :param local: Local path of file to upload, or a file-like object.
        If a string is given**, it should be a path to a local (regular) file (not a directory).
        :param str remote: Remote path to which the local file will be written.
        :return: A runners.Result object
        """
        if self.client.is_connected:
            output = self.client.put(local, remote)
        else:
            raise RuntimeError("ERROR: could not execute command - connection is closed")

        return output

    def get_file(self, remote, local):
        """
        Copy a file from client connection's host to the local filesystem.
        :param str remote: Remote file to download.
        :param local: Local path to store downloaded file in, or a file-like object.
        :return: A runners.Result object
        """
        if self.client.is_connected:
            output = self.client.get(remote, local)
        else:
            raise RuntimeError("ERROR: could not execute command - connection is closed")

        return output

    def is_connected(self):
        """ Check if the client is connected """
        return self.client.is_connected

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
