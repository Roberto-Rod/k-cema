import socket
import time
import zeroconf as zeroconfig

unit_type_str = "KFD-"
type_str = "_kfd._tcp.local."

timeout = 10
count = timeout * 10

ret_val = []

def on_change(zeroconf, service_type, name, state_change):
    if state_change is zeroconfig.ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            address = "{}".format(socket.inet_ntoa(info.addresses[0]))
            server = str(info.server)
            if unit_type_str in server:
                ret_val.append([server.rstrip("."), address])

zeroconf = zeroconfig.Zeroconf()
browser = zeroconfig.ServiceBrowser(zeroconf, type_str, handlers=[on_change])

while count > 0:
    time.sleep(0.1)
    count = count - 1

zeroconf.close()
print(ret_val)
