#!/usr/bin/env python3
"""
Install a firmware file on the CTS Digital Board using the CTS Test Jig and s
Segger J-Link programmer
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
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
import pyvisa

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
class VisaTestEquipment:
    """" Base class for a piece of VISA compatible test equipment. """
    # Concrete class implementations should override parameters with appropriate values
    MANUFACTURER = ""
    MODEL = ""

    def __init__(self, resource_name):
        """
        Class constructor
        :param resource_name: VISA resource name for the piece of TE :type String
        """
        self.resource_manager = pyvisa.ResourceManager()
        self.resource_name = resource_name
        self.visa_te = None
        self.manufacturer = ""
        self.model = ""

    def __del__(self):
        if self.visa_te is not None:
            self.visa_te.close()

    def __enter__(self):
        return self

    def __exit__(self):
        if self.visa_te is not None:
            self.visa_te.close()

    def find_and_initialise(self):
        """
        Looks for resource name specified during object creation in available resources and initialises device if it is
        found.
        Concrete class implementations must define the parameter SUPPORTED_MODELS which is a List of Dictionaries, e.g.
        [{"manufacturer": "HP", "model "abc"}, {"manufacturer": "HP", "model "abc"}, ... ]
        :return: True if the resource is found and initialised, else False
        """
        for resource in self.resource_manager.list_resources():
            if resource == self.resource_name:
                device_list = [{"manufacturer": self.MANUFACTURER, "model": self.MODEL}]
                if self.initialise_device(device_list):
                    log.debug("Found and initialised Test Equipment: {} - {}"
                              "".format(self.resource_name, self.ieee4882_idn_query()))
                    return True
        log.debug("ERROR: did not find and initialise Test Equipment!")
        return False

    def initialise_device(self, model_string_list):
        """
        Initialises the device, only successful if the resource is in the list of supported models.
        :param model_string_list: list of models supported by the concrete class implementation :type List of Strings
        :return: True if the resource is found and initialised, else False
        """
        ret_val = False
        try:
            self.visa_te = self.resource_manager.open_resource(self.resource_name)
            idn_dict = self.ieee4882_idn_query()
            for model in model_string_list:
                if idn_dict.get("manufacturer", "") == model.get("manufacturer", "") and \
                      idn_dict.get("model", "") == model.get("model", ""):
                    self.manufacturer = idn_dict.get("manufacturer")
                    self.model = idn_dict.get("model")
                    ret_val = self.ieee4882_reset()
                    ret_val = self.ieee4882_clear_status() and ret_val
                    ret_val = self.ieee4882_wait_cmd_complete() and ret_val
                    ret_val = self.device_specific_initialisation() and ret_val
                    break

        except Exception as ex:
            log.debug("Could not open resource: {} - {}".format(self.resource_name, ex))

        if not ret_val and self.visa_te is not None:
            self.visa_te.close()

        return ret_val

    def device_specific_initialisation(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: True if successful, else False
        """
        raise NotImplementedError

    def ieee4882_idn_query(self):
        """
        Queries the connected resource's IEEE488.2 formatted identification data.
        :return: Dictionary representing the IEEE288.2 identification data, keys "manufacturer", "model", "serial_no",
        "revision", empty dictionary if the query fails.
        """
        idn_dict = {}
        # A valid IEEE488.2 identification string has four comma separated values:
        # "manufacturer", "model", "serial_no", "revision"
        idn_strings = self.send_query("*IDN?").split(',')
        if len(idn_strings) == 4:
            idn_dict["manufacturer"] = idn_strings[0].lstrip()
            idn_dict["model"] = idn_strings[1].lstrip()
            idn_dict["serial_no"] = idn_strings[2].lstrip()
            idn_dict["revision"] = idn_strings[3].lstrip()

        return idn_dict

    def ieee4882_opt_query(self):
        """
        Queries the connected resource's IEEE488.2 option string.
        :return: Option string, empty string if the query fails :type String
        """
        return self.send_query("*OPT?")

    def ieee4882_reset(self):
        return self.send_command("*RST")

    def ieee4882_clear_status(self):
        return self.send_command("*CLS")

    def ieee4882_wait_cmd_complete(self):
        resp = self.send_query("*OPC?").strip()
        return bool(resp == "1" or resp == "+1")

    def send_command(self, cmd):
        log.debug("send_command: {}".format(cmd))
        try:
            self.visa_te.write(cmd)
            return True
        except Exception as ex:
            log.critical("ERROR - send_command - {}".format(ex))
            return False

    def send_query(self, query, delay=None):
        log.debug("send_query: {}".format(query, delay))
        try:
            return self.visa_te.query(query, delay=delay).strip()
        except Exception as ex:
            log.critical("ERROR - send_query - {}".format(ex))
        return ""


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """ List the available PyVISA resources. """
    print("Available PyVISA resources:")
    resource_manager = pyvisa.ResourceManager()
    for i, resource in enumerate(resource_manager.list_resources()):
        print("{} - {}".format(i, resource))
        v = resource_manager.open_resource(resource)
        idn_dict = {}
        # A valid IEEE488.2 identification string has four comma separated values:
        # "manufacturer", "model", "serial_no", "revision"
        try:
            print(v.query("*IDN?").strip())
        except:
            pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run-time procedure """
    main()
