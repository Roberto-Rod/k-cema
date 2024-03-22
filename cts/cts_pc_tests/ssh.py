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
from fabric import Connection
import fabric.transfer as ft
from scp import SCPClient

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
    CONNECTION_RETRIES = 2
    COMMAND_TIMEOUT_S = 15
    COMMAND_RETRIES = 3
    FILE_SEND_RETRIES = 3
    PASSWORDS = ["gbL^58TJc", "root"]

    def __init__(self, address, username, password_dict=None):
        """ Class constructor """
        self.client = None
        self.address = address
        self.username = username
        if password_dict is not None:
            self.password_dict = password_dict
        else:
            self.password_dict = {}
        self.connect()

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

    def connect(self):
        """
        Connect to the host
        :return: N/A, raises an exception if the connection fails
        """
        # Build a list of passwords to try
        passwords = []
        if self.address in self.password_dict.keys():
            # Try the existing password if it is in the dictionary
            passwords.append(self.password_dict[self.address])
        passwords.extend(self.PASSWORDS)

        for i, password in enumerate(passwords):
            for attempt in range(0, self.CONNECTION_RETRIES):
                try:
                    self.client = Connection(host=self.address, user=self.username, port=22,
                                             connect_kwargs={"password": password})
                    self.client.create_session()
                    # If connection is successful break out of loop
                    log.info("Connected to {}".format(self.address))
                    self.password_dict[self.address] = password
                    break
                except Exception as ex:
                    self.client.close()
                    log.info("ERROR: SSH connection attempt {} to {} with password {} failed - {}".format(attempt,
                                                                                                          self.address,
                                                                                                          i, ex))
            if self.client.is_connected:
                break
        # If the connection failed, this call will blow up and raise a suitable error
        self.client.run("")

    def send_command(self, command, timeout=COMMAND_TIMEOUT_S, retries=COMMAND_RETRIES):
        """
        Execute a shell command on the remote end of this connection.
        :param command: Command to execute
        :param timeout: number of seconds to wait for the command to complete :type Float
        :param retries: number of times to retry the command
        :return: A runners.Result object, raises RuntimeError exception if the command fails
        """
        reconnect = False
        for i in range(retries):
            if reconnect:
                self.client.close()
                del self.client
                self.connect()

            if self.client.is_connected:
                try:
                    return self.client.run(command, warn=True, hide=True, timeout=timeout)
                except Exception as ex:
                    log.info("WARNING: command timed out, reconnecting... - {}".format(ex))
                    reconnect = True
            else:
                reconnect = True

        raise RuntimeError("ERROR: could not execute command - unable to open SSH connection")

    def send_file(self, local, remote, protocol="SFTP"):
        """
        Upload a file from the local filesystem to the current connection.
        :param local: Local path of file to upload, or a file-like object.
        If a string is given**, it should be a path to a local (regular) file (not a directory).
        :param remote: Remote path to which the local file will be written. :type String
        :param protocol: file transfer protocol to use, "SFTP" or "SCP". :type String
        :return: A runners.Result object, raises a RuntimeError exception if the send file fails
        """
        if protocol not in ["SFTP", "SCP"]:
            raise ValueError("Protocol must be one of : {}".format(protocol))

        reconnect = False
        for i in range(self.FILE_SEND_RETRIES):
            if reconnect:
                self.client.close()
                del self.client
                self.connect()

            if self.client.is_connected:
                try:
                    if protocol == "SCP":
                        with SCPClient(self.client.client.get_transport()) as scp_client:
                            scp_client.put(local, remote)
                            # No exception raised so assume success, create and return a Fabric Transfer Result object
                            # to mimic the standard Fabric SFTP transfer
                            return ft.Result(
                                orig_remote=remote,
                                remote=remote,
                                orig_local=local,
                                local=local,
                                connection=self.client,
                            )
                    elif protocol == "SFTP":
                        return self.client.put(local, remote)
                    else:
                        # Return an  empty Result object to indicate the error
                        return ft.Result(
                            orig_remote="",
                            remote="",
                            orig_local="",
                            local="",
                            connection=self.client,
                        )

                except Exception as ex:
                    log.info("WARNING: send file timed out, reconnecting... - {}".format(ex))
                    reconnect = True
            else:
                reconnect = True

        raise RuntimeError("ERROR: could not send file - unable to open SSH connection")

    def get_file(self, remote, local, protocol="SFTP"):
        """
        Copy a file from client connection's host to the local filesystem.
        :param str remote: Remote file to download.
        :param local: Local path to store downloaded file in, or a file-like object.
        :param protocol: file transfer protocol to use, "SFTP" or "SCP". :type String
        :return: A runners.Result object, raises a RuntimeError exception if the send file fails
        """
        if protocol not in ["SFTP", "SCP"]:
            raise ValueError("Protocol must be one of : {}".format(protocol))

        reconnect = False
        for i in range(self.FILE_SEND_RETRIES):
            if reconnect:
                self.client.close()
                del self.client
                self.connect()

            if self.client.is_connected:
                try:
                    if protocol == "SCP":
                        with SCPClient(self.client.client.get_transport()) as scp_client:
                            scp_client.get(remote, local)
                            # No exception raised so assume success, create and return a Fabric Transfer Result object
                            # to mimic the standard Fabric SFTP transfer
                            return ft.Result(
                                orig_remote=remote,
                                remote=remote,
                                orig_local=local,
                                local=local,
                                connection=self.client
                            )
                    elif protocol == "SFTP":
                        # By default Fabric uses SFTP file transfer protocol
                        return self.client.get(remote, local)
                    else:
                        # Return an  empty Result object to indicate the error
                        return ft.Result(
                            orig_remote="",
                            remote="",
                            orig_local="",
                            local="",
                            connection=self.client
                        )
                except Exception as ex:
                    log.info("WARNING: get file timed out, reconnecting... - {}".format(ex))
                    reconnect = True
            else:
                reconnect = True

        raise RuntimeError("ERROR: could not get file - unable to open SSH connection")

    def is_connected(self):
        """
        Check if the client is connected
        :return True if connected, else False
        """
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
