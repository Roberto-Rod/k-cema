#!/usr/bin/env python3
import os
import ipaddress
import re


class IPTools:
    def __init__(self):
        pass

    def get_ipv4_from_mac(self, mac, verbose=False):
        number_of_attempts = 5
        for i in range(number_of_attempts):
            # Ping the IPv6 link-local address so that we get the device in the ARP cache
            ipv6 = self.get_ipv6_from_mac(mac, "fe80::/64")
            ret = os.popen("ping {} -6 -n 1".format(ipv6)).read()
            if verbose:
                print(ret)
            arp = os.popen("arp -a").read().splitlines()
            for a in arp:
                a = a.lower().replace("-", ":")
                if mac.lower() in a:
                    return a.lstrip().split()[0]
        return "0.0.0.0"

    @staticmethod
    def get_ipv6_from_mac(mac, prefix=None):
        '''
        Convert a MAC address to a EUI64 address
        or, with prefix provided, a full IPv6 address
        '''
        # http://tools.ietf.org/html/rfc4291#section-2.5.1
        eui64 = re.sub(r'[.:-]', '', mac).lower()
        eui64 = eui64[0:6] + 'fffe' + eui64[6:]
        eui64 = hex(int(eui64[0:2], 16) ^ 2)[2:].zfill(2) + eui64[2:]

        if prefix is None:
            return ':'.join(re.findall(r'.{4}', eui64))
        else:
            try:
                net = ipaddress.ip_network(prefix, strict=False)
                euil = int('0x{0}'.format(eui64), 16)
                return str(net[euil])
            except:  # pylint: disable=bare-except
                return


if __name__ == "__main__":
    t = IPTools()
    mac = "80:1F:12:D0:B7:EC"
    print("Using MAC Address: {}".format(mac))
    print("IPv6: {}".format(t.get_ipv6_from_mac(mac, "fe80::/64")))
    print("IPv4: {}".format(t.get_ipv4_from_mac(mac, True)))
