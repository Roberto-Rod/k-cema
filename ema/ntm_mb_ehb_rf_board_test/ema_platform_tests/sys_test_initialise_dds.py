#!/usr/bin/env python3
from dds import *
from serial_number import *


# Class provided to initialise the DDS e.g. to stop it outputting a tone
class SysTestInitialiseDDS:
    def init(self, sweep_mode=False):
        serial = SerialNumber.get_serial(Module.EMA)
        print("Initialising EMA-{} DDS...".format(serial))

        # Initialise DDS
        d = DDS()
        d.initialise(sweep_mode)

        # If we got this far then everything worked
        return True


if __name__ == "__main__":
    o = SysTestInitialiseDDS()
    ok = o.init()
    if ok:
        print("OK")
    else:
        print("Error")
