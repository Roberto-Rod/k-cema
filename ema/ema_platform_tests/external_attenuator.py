#!/usr/bin/env python3
from band import *
from enum import Enum

class Path(Enum):
    TX = 0,
    RX = 1

class ExternalAttenuator:
    ATT_POINTS = [
    #    Path,      Band,     Start Freq.,   Att.
    #                              (MHz)    (dB)
        #[Path.TX,   Band.LOW,          20,  30.40],
        #[Path.TX,   Band.LOW,         520,  30.40],
        #[Path.TX,   Band.MID,         400,  30.40],
        #[Path.TX,   Band.MID,        2700,  30.40],
        #[Path.TX,   Band.HIGH,       1800,  30.08],
        #[Path.TX,   Band.HIGH,       6000,  30.97],
        #[Path.RX,   Band.LOW,          20,  29.70],
        #[Path.RX,   Band.LOW,         520,  30.50],
        #[Path.RX,   Band.MID,         400,  29.77 + 0.53],
        #[Path.RX,   Band.MID,        2700,  30.13 + 2.65],
        #[Path.RX,   Band.HIGH,       1800,  30.08],
        #[Path.RX,   Band.HIGH,       6000,  30.97],
        [Path.TX,   Band.LOW,          20,  40],
        [Path.TX,   Band.LOW,         520,  40],
        [Path.TX,   Band.MID,         400,  40],
        [Path.TX,   Band.MID,        2700,  40],
        [Path.TX,   Band.HIGH,       1800,  40],
        [Path.TX,   Band.HIGH,       6000,  40.3],
        [Path.TX,   Band.EXT_HIGH,   5700,  40.5],
        [Path.TX,   Band.EXT_HIGH,   8000,  40.7],
        [Path.RX,   Band.LOW,          20,  29.8],
        [Path.RX,   Band.LOW,         520,  30.4],
        [Path.RX,   Band.MID,         400,  30.3],
        [Path.RX,   Band.MID,        2700,  31.6],
        [Path.RX,   Band.HIGH,       1800,  31.4],
        [Path.RX,   Band.HIGH,       6000,  33.0],
        [Path.RX,   Band.EXT_HIGH,   5700,  32.6],
        [Path.RX,   Band.EXT_HIGH,   8000,  37.5]
    ]

    # 4 GHz att. K2:
    #ATT_POINTS = [
    #    Band,     Start Freq.,   Att.
    #                    (MHz)    (dB)
    #    [Band.LOW,          20,  30.40],
    #    [Band.LOW,         520,  30.40],
    #    [Band.MID,         400,  30.40],
    #    [Band.MID,        2700,  30.40],
    #]

    # 6 GHz att. K2
    #ATT_POINTS = [
    #    Band,     Start Freq.,   Att.
    #                    (MHz)    (dB)
    #    [Band.LOW,          20,  29.64],
    #    [Band.LOW,         520,  29.85],
    #    [Band.MID,         400,  29.77],
    #    [Band.MID,        2700,  30.13],
    #    [Band.HIGH,       1800,  30.08],
    #    [Band.HIGH,       6000,  30.97]
    #]

    # 4 GHz att. RH
    #ATT_POINTS = [
    #    Band,     Start Freq.,   Att.
    #                    (MHz)    (dB)
    #    [Band.LOW,          20,  30.07],
    #    [Band.LOW,         520,  30.18],
    #    [Band.MID,         400,  30.17],
    #    [Band.MID,        2700,  29.75],
    #    [Band.HIGH,       1800,  30.08],
    #    [Band.HIGH,       6000,  30.97]
    #]

    # 6 GHz att. RH
    #ATT_POINTS = [
    #    Band,     Start Freq.,   Att.
    #                    (MHz)    (dB)
    #    [Band.LOW,          20,  29.64],
    #    [Band.LOW,         520,  29.85],
    #    [Band.MID,         400,  29.77],
    #    [Band.MID,        2700,  30.13],
    #    [Band.HIGH,       1800,  30.08],
    #    [Band.HIGH,       6000,  30.97]
    #]

    def get_att(band, freq_MHz, path=Path.TX, verbose=False):
        n = 0
        for point in ExternalAttenuator.ATT_POINTS:
            if point[0] == path and point[1] == band:
                if n == 0:
                    freq1 = float(point[2])
                    att1 = float(point[3])
                    freq2 = freq1
                    att2 = att1
                else:
                    if float(point[2]) >= float(freq_MHz):
                        freq2 = float(point[2])
                        att2 = float(point[3])
                        break
                    freq1 = float(point[2])
                    att1 = float(point[3])
                n += 1

        # If there was no data then return 0
        if n == 0:
            att_dB = 0

        # If we did not find a point within the table then use the att value from the last point
        elif freq2 <= freq1:
            att_dB = att1
        else:
            r = (float(freq_MHz) - freq1) / (freq2 - freq1)
            att_dB = round((r * (att2 - att1)) + att1, 2)

        if verbose:
            print("Band: {}, Freq: {} MHz, Att.: {:.2f} dB".format(band, freq_MHz, att_dB))

        return att_dB


if __name__ == "__main__":
    print("ExternalAttenuator Tests")
    ExternalAttenuator.get_att(Band.LOW, 20, True)
    ExternalAttenuator.get_att(Band.LOW, 270, True)
    ExternalAttenuator.get_att(Band.LOW, 520, True)
    ExternalAttenuator.get_att(Band.MID, 400, True)
    ExternalAttenuator.get_att(Band.MID, 1550, True)
    ExternalAttenuator.get_att(Band.MID, 2700, True)
    ExternalAttenuator.get_att(Band.HIGH, 1800, True)
    ExternalAttenuator.get_att(Band.HIGH, 3900, True)
    ExternalAttenuator.get_att(Band.HIGH, 6000, True)
    ExternalAttenuator.get_att(Band.HIGH, 6100, True)
