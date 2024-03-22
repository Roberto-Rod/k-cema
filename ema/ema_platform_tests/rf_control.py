#!/usr/bin/env python3
from devmem import *
from band import *


class RFControl:
    REG_RF_CONTROL = 0x40080580
    REG_TX_CONTROL = 0x40015000

    RF_CONTROL_STEP_ATT_MASK = 0x01000000
    RF_CONTROL_DBLR_ATT_MASK = 0x00FF0000
    RF_CONTROL_SRC_ATT_MASK = 0x00003000
    RF_CONTROL_TX_PATH_MASK = 0x000000F0
    RF_CONTROL_TX_PATH_EHB_MASK = 0x00000070
    RF_CONTROL_XCVR_PATH_MASK = 0x00000080
    REG_TX_ATT_OR_MASK = 0x00000800
    REG_TX_ATT_VAL_MASK = 0x000003F0

    # RF path register values:
    # 0:  (400-1500 MHz, x1)  [Mercury MB path 0]
    # 1:  (1480-1880 MHz, x2) [Mercury MB path 1]
    # 2:  (1850-2250 MHz, x2) [Mercury MB path 2]
    # 3:  (2250-2500 MHz, x2) [Mercury MB path 3]
    # 4:  (2500-2700 MHz, x2) [Mercury MB path 4]
    # 5:  (2700-3000 MHz, x2) [Mercury MB path 5]
    # 9:  (2400-3400 MHz, x4) [Mercury HB path 1]
    # 10: (3400-4600 MHz, x4) [Mercury HB path 2]
    # 11: (4600-6000 MHz, x6) [Mercury HB path 3]

    @staticmethod
    def set_doubler_att(att_dB):
        # Doubler attenuator is set in 0.25 dB steps
        # Range 0.00 dB to 63.75 dB
        att_quarter_dB = int(round(att_dB * 4, 0))
        DevMem.rmw(RFControl.REG_RF_CONTROL, att_quarter_dB, RFControl.RF_CONTROL_DBLR_ATT_MASK)

    @staticmethod
    def get_doubler_att():
        att_quarter_dB = (DevMem.read(RFControl.REG_RF_CONTROL) & RFControl.RF_CONTROL_DBLR_ATT_MASK) >> 16
        return att_quarter_dB / 4

    @staticmethod
    def en_doubler_att_20_dB(en):
        if (en):
            DevMem.set(RFControl.REG_RF_CONTROL, RFControl.RF_CONTROL_STEP_ATT_MASK)
        else:
            DevMem.clear(RFControl.REG_RF_CONTROL, RFControl.RF_CONTROL_STEP_ATT_MASK)

    @staticmethod
    def set_source_att(att_dB):
        # Source attenuator:
        #   value | attenuation
        #     0x0 | 30 dB
        #     0x1 | 20 dB
        #     0x2 | 10 dB
        #     0x3 | 0 dB

        # Find closest available value, default to 30 dB if a bigger number is requested...
        val = 0
        if att_dB < 5:
            val = 3
        elif att_dB < 15:
            val = 2
        elif att_dB < 25:
            val = 1

        DevMem.rmw(RFControl.REG_RF_CONTROL, val, RFControl.RF_CONTROL_SRC_ATT_MASK)

    @staticmethod
    def enable_tx_att_override():
        DevMem.set(RFControl.REG_TX_CONTROL, RFControl.REG_TX_ATT_OR_MASK)

    @staticmethod
    def disable_tx_att_override():
        DevMem.clear(RFControl.REG_TX_CONTROL, RFControl.REG_TX_ATT_OR_MASK)

    @staticmethod
    def set_tx_att(att_dB):
        val = att_dB * 2
        if 0 < val < 64:
            DevMem.rmw(RFControl.REG_TX_CONTROL, val, RFControl.REG_TX_ATT_VAL_MASK)

    @staticmethod
    def convert_tx_path(path, band, ehb=False):
        if band == Band.HIGH or band == Band.EXT_HIGH:
            if ehb:
                return path + 1
            else:
                # HB paths: MB 1, MB 2, MB 3, HB 1, HB 2, HB 3
                # Logical:     0,    1,    2,    3,    4,    5
                # Reg val:     1,    2,    3,    9,   10,   11
                if path <= 2:
                    path += 1
                else:
                    path += 6
        return path

    @staticmethod
    def set_tx_path(path, band, ehb=False):
        path = RFControl.convert_tx_path(path, band, ehb)
        if ehb:
            mask = RFControl.RF_CONTROL_TX_PATH_EHB_MASK
        else:
            mask = RFControl.RF_CONTROL_TX_PATH_MASK
        DevMem.rmw(RFControl.REG_RF_CONTROL, path, mask)

    @staticmethod
    def set_xcvr_path(path):
        if path == 0:
            DevMem.clear(RFControl.REG_RF_CONTROL, RFControl.RF_CONTROL_XCVR_PATH_MASK)
        else:
            DevMem.set(RFControl.REG_RF_CONTROL, RFControl.RF_CONTROL_XCVR_PATH_MASK)

    @staticmethod
    def get_multiplier(path, band, ehb=False):
        if ehb:
            path = RFControl.convert_tx_path(path, band, ehb)
            if path == 0:
                return 1
            elif path <= 3:
                return 2
            elif path <= 6:
                return 4
            else:
                return 8
        else:
            if band == Band.LOW:
                return 1
            elif band == Band.MID:
                if path == 0:
                    return 1
                else:
                    return 2
            elif band == Band.HIGH:
                if path <= 2:
                    return 2
                elif path == 5:
                    return 6
                else:
                    return 4
            else:
                return 0


if __name__ == "__main__":
    print("RF Control tests:")
    print("Set Tx path to 0")
    RFControl.set_tx_path(0)
    print("Set source attenuation to 0 dB")
    RFControl.set_source_att(0)
    print("Set doubler attenuation to 0 dB")
    RFControl.set_doubler_att(0)
    print("Disable doubler 20 dB step attenuator")
    RFControl.en_doubler_att_20_dB(False)
