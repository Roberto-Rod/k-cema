class KCEMAModule:
    def __init__(self, ip_address, hostname, software_version, state, health):
        self.ip_address = ip_address
        self.hostname = hostname
        self.software_version = software_version
        self.state = state
        self.health = health


class KCEMACSM(KCEMAModule):
    def __init__(self, ip_address="<enter ip>", hostname="", software_version="", state="", health="",
                 system_name="", location="", system_group=""):
        KCEMAModule.__init__(self, ip_address, hostname, software_version, state, health)
        self.system_name = system_name
        self.system_group = system_group
        self.location = location


class KCEMAEMA(KCEMAModule):
    def __init__(self, ip_address="", hostname="", software_version="", state="", health="", band=""):
        KCEMAModule.__init__(self, ip_address, hostname, software_version, state, health)
        self.band = band


class KCEMASystem:
    def __init__(self, csm_ip_address="", ema_ip_addresses=[]):
        self.csm = KCEMACSM(ip_address=csm_ip_address)
        self.emas = []
        for ema_ip in ema_ip_addresses:
            self.emas.append(KCEMAEMA(ip_address=ema_ip))
        self.poll_status = ""
        self.selected = False

    def get_ip_addresses(self):
        ema_ip_addresses = []
        for ema in self.emas:
            ema_ip_addresses.append(ema.ip_address)
        data = {
            "csm_ip_address": self.csm.ip_address,
            "ema_ip_addresses": ema_ip_addresses
        }
        return data
