#!/usr/bin/env python3
import socket
import argparse
import time

import zeroconf as zeroconfig


class FindService:
    def find(service_name, type="kpms", return_service=False, timeout=10, stop_on_finding=1):
        ret_val = []
        type_ = "_{}._tcp.local.".format(type)
        count = timeout * 10
        found = 0

        def on_change(zeroconf, service_type, name, state_change):
            nonlocal ret_val
            nonlocal count
            nonlocal found
            nonlocal stop_on_finding
            if state_change is zeroconfig.ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    address = "{}".format(socket.inet_ntoa(info.addresses[0]))
                    server = str(info.server)
                    if service_name in server:
                        if return_service:
                            ret_val.append([server.rstrip("."), address])
                        else:
                            ret_val.append([address, info.port])
                        found += 1
                        if found == stop_on_finding:
                            count = 0

        zeroconf = zeroconfig.Zeroconf()
        browser = zeroconfig.ServiceBrowser(zeroconf, type_, handlers=[on_change])

        while count > 0:
            time.sleep(0.1)
            count = count - 1

        zeroconf.close()
        return ret_val

    def find_pms(return_service=False, timeout=10):
        return FindService.find("Power Meter Service", "kpms", return_service, timeout=timeout)

    def find_sgs(return_service=False, timeout=10):
        return FindService.find("Signal Generator Service", "kpms", return_service, timeout=timeout)

    def find_csm(return_service=False, timeout=10):
        return FindService.find("CSM-", "ssh", return_service, timeout=timeout)

    def find_ema(return_service=False, timeout=10):
        return FindService.find("EMA-", "ssh", return_service, timeout=timeout, stop_on_finding=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find zeroconf service")
    parser.add_argument("-n", "--name", help="Display service name (no IP address or port)", action="store_true")
    parser.add_argument("-p", "--pms", help="Find Power Meter Service", action="store_true")
    parser.add_argument("-s", "--sgs", help="Find Signal Generator Service", action="store_true")
    parser.add_argument("-c", "--csm", help="Find CSM", action="store_true")
    parser.add_argument("-e", "--ema", help="Find EMA", action="store_true")
    args = parser.parse_args()

    if args.pms:
        details = FindService.find_pms(args.name)
    elif args.sgs:
        details = FindService.find_sgs(args.name)
    elif args.csm:
        details = FindService.find_csm(args.name)
    elif args.ema:
        details = FindService.find_ema(args.name)
    else:
        details = None

    for item in details:
        if isinstance(item, list):
            print("{}:{}".format(item[0], item[1]))
        else:
            print(item)
