#!/usr/bin/env python3
from ssh import SSH


class ReconfigureSlotOrder:
    RECONFIGURE_SLOT_ORDER_CMD = "python3 /tmp/test/generate_run_file.py"
    RECONFIGURE_SLOT_ORDER_SUCCESS_STR = "OK: Generate Run File"

    def __init__(self, text, csms):
        self.text = text
        self.csms = csms

    def reconfigure(self):
        all_ok = True
        for csm in self.csms:
            s = SSH(csm[1])
            self.text.insert("Reconfiguring slot order ({})...".format(csm[0].rstrip(".local")))
            ret_str = str(s.send_command(self.RECONFIGURE_SLOT_ORDER_CMD).stderr).strip()

            if self.RECONFIGURE_SLOT_ORDER_SUCCESS_STR in ret_str:
                self.text.insert("Successfully reconfigured slot order({})...".format(csm[0].rstrip(".local")))
            else:
                self.text.insert("Failed to reconfigure slot order({})...".format(csm[0].rstrip(".local")))
                all_ok = False

        return all_ok
