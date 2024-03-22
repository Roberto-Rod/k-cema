#!/usr/bin/env python3
from enum import Enum


class Band(Enum):
    UNKNOWN = 0
    LOW = 1
    MID_HIGH = 2
    MID = 3
    HIGH = 4
    EXT_HIGH = 5


def get_band_opt(argv, ntm_digital=False, quiet=False):
    band = Band.LOW
    if len(argv) >= 2:
        if argv[1] == "LB":
            pass
        elif argv[1] == "MB":
            if ntm_digital:
                band = Band.MID_HIGH
            else:
                band = Band.MID
        elif argv[1] == "HB":
            if ntm_digital:
                band = Band.MID_HIGH
            else:
                band = Band.HIGH
    if not quiet:
        print("\nUsing: {}".format(band))
    return band
