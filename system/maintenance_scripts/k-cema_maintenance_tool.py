from tkinter import filedialog
from tkinter import ttk
from update_software import *
from test_tamper import *
from text_update import *
from getmac import get_mac_address
import datetime
import json
import os
import re
import sys
from reconfigure_slot_order import ReconfigureSlotOrder
from tempfile import TemporaryDirectory
import shutil
import zipfile
import cffi  # Although not used directly in this script, adding this import fixes an error with py2exe packaging

password_dict = {}


class App:
    VERSION_MAJOR = 1
    VERSION_MINOR = 5
    VERSION_PATCH = 8

    MIN_NR_CSM = 1
    MIN_NR_EMA = 1

    MIN_EMA_BOOT_PARTITION_SIZE = 16384000

    CSM_REFRESH_HW_CONFIG_CMD = "cd /tmp/test/; export PATH=${PATH}:/usr/sbin; python3 hardware_unit_config.py -r"
    EMA_REFRESH_HW_CONFIG_CMD = "cd /tmp/test/; export PATH=${PATH}:/usr/sbin; python3 hardware_unit_config.py -r"
    EMA_GET_BOOT_PARTITION_SIZE_CMD = "/usr/sbin/mtdinfo /dev/mtd0"
    REBOOT_CMD = "/sbin/reboot"

    LOG_FILE_NAMES = ["k-cema-{}.log", "k-cema-{}.1.log", "k-cema-{}.2.log",
                      "k-cema-{}-critical.log", "k-cema-{}-critical.1.log", "k-cema-{}-critical.2.log",
                      "GPS.csv", "GPS.1.csv", "GPS.2.csv"]

    def __init__(self, master):
        self.emas = []
        self.csms = []
        master.geometry("1200x600")
        master.iconbitmap("kirintec_logo.ico")
        fm = Frame(master)
        self.buttons = {"dsc": Button(fm, text='Discover Modules', width=20, command=self.discover_modules),
                        "zer": Button(fm, text='Zeroise Software & Fill', width=20, command=self.zeroise_software_and_fill, state=DISABLED),
                        "upd": Button(fm, text='Update Software', width=20, command=self.update_software, state=DISABLED),
                        "cbs": Button(fm, text='Check Boot Size', width=20, command=self.check_bootloader_size, state=DISABLED),
                        "log": Button(fm, text='Recover Log Files', width=20, command=self.recover_logs, state=DISABLED),
                        "rbt": Button(fm, text='Reboot', width=20, command=self.reboot_system, state=DISABLED),
                        "ips": Button(fm, text='Set IP Address/Mode', width=20, command=self.ip_dialog, state=DISABLED),
                        "sys": Button(fm, text='Set System Settings', width=20, command=self.system_settings, state=DISABLED),
                        "scr": Button(fm, text='Install Test Scripts', width=20, command=self.install_scripts, state=DISABLED),
                        "ubl": Button(fm, text='Update Bootloader', width=20, command=self.update_bootloader, state=DISABLED),
                        "rso": Button(fm, text='Reconfigure Slot Order', width=20, command=self.reconfigure_slot_order, state=DISABLED)}
        for key in self.buttons:
            self.buttons[key].pack(side=TOP, expand=NO, padx=10, pady=5)
        text = Text(master)
        text.insert(INSERT, self.get_part_number() + "\n")
        text.insert(INSERT, self.get_title() + "\n")
        fm.pack(fill=BOTH, expand=NO, side=LEFT)
        text.pack(fill=BOTH, expand=YES, side=RIGHT, padx=5, pady=5)
        self.text = TextUpdate(text, master)

    def update_availability(self):
        global password_dict
        if len(self.csms) >= self.MIN_NR_CSM and len(self.emas) >= self.MIN_NR_EMA:
            ema_connections_ok = True
            csm_connections_ok = True
            for csm in self.csms:
                s = SSH(csm[1], password_dict)
                try:
                    # Send any command (use "hostname") to test the CSM connection
                    s.send_command("hostname").stdout.splitlines()
                except AttributeError:
                    csm_connections_ok = False
            for ema in self.emas:
                s = SSH(ema[1], password_dict)
                try:
                    # Send any command (use "hostname") to test the EMA connection
                    s.send_command("hostname").stdout.splitlines()
                except AttributeError:
                    ema_connections_ok = False

            if ema_connections_ok and csm_connections_ok:
                if len(self.emas) > 0:
                    self.text.insert("OK")
                self.buttons["scr"]["state"] = NORMAL
                self.buttons["upd"]["state"] = NORMAL
                self.buttons["zer"]["state"] = NORMAL
                self.buttons["log"]["state"] = NORMAL
                self.buttons["rbt"]["state"] = NORMAL
                self.buttons["ips"]["state"] = NORMAL
                self.buttons["sys"]["state"] = NORMAL
                self.buttons["cbs"]["state"] = NORMAL
            else:
                self.text.insert("One or More Connections Lost")
        self.text.insert("CSM Count: {}, EMA Count: {}".format(len(self.csms), len(self.emas)))

    def discover_modules(self):
        self.clear_ui_state()
        self.text.insert("\nDiscover Modules...")
        self.emas = []
        self.csms = []
        # Get the CSM hostnames
        try:
            self.csms = FindService.find_csm(True, 4)
            for host in self.csms:
                self.text.insert("Found {} ({})".format(host[0].rstrip(".local"), host[1]))
        except Exception as e:
            self.text.insert("ERROR: could not get CSM hostname ({})".format(e))
        # Get the EMA hostnames
        try:
            self.emas = FindService.find_ema(True, 4)
            for host in self.emas:
                self.text.insert("Found {} ({})".format(host[0].rstrip(".local"), host[1]))
        except Exception as e:
            self.text.insert("ERROR: could not get EMA hostname ({})".format(e))
        self.update_availability()

    def update_bootloader(self):
        # Ensure tamper is not triggered on any of the modules
        t = TestTamper(self.text, self.csms, self.emas)
        if t.run_test():
            self.update_software(bootloader=True)

    def check_bootloader_size(self):
        global password_dict
        ok = True
        for ema in self.emas:
            self.text.insert("Checking boot partition size ({})...".format(ema[0].rstrip(".local")))
            s = SSH(ema[1], password_dict)
            # Get the mtdinfo and split the fields to find the size which appears in a line of the form:
            # Amount of eraseblocks: 250 (16384000 bytes, 15.6 MiB)
            resp = None
            try:
                resp = s.send_command(self.EMA_GET_BOOT_PARTITION_SIZE_CMD).stdout.splitlines()
            except AttributeError:
                resp = None
            if resp is None:
                ok = False
                self.text.insert("WARNING - lost connection to {}".format(ema.rstrip(".local")))
            else:
                nr_bytes = 0
                for line in resp:
                    fields = line.split(":")
                    if len(fields) == 2:
                        if fields[0] == "Amount of eraseblocks":
                            vals = fields[1].strip().replace("(", " ").split()
                            nr_bytes = vals[1]
                if int(nr_bytes) >= self.MIN_EMA_BOOT_PARTITION_SIZE:
                    self.text.insert("    OK")
                else:
                    self.text.insert("    WARNING - Boot Partition Undersized")
                    ok = False
        return ok

    def install_scripts(self):
        if self.update_software(scripts=True):
            self.buttons["ubl"]["state"] = NORMAL
            self.buttons["rso"]["state"] = NORMAL

    def update_software(self, bootloader=False, scripts=False):
        ret_val = False
        file = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if file is not None and file != "":
            if bootloader:
                self.text.insert("\nRefreshing hardware config info...")
                if not self.refresh_hw_config():
                    self.text.insert("\nFailed to update hardware config info, aborting bootloader update")
                    return
                self.text.insert("\nUpdate Bootloader...")
            elif scripts:
                self.text.insert("\nInstall Test Scripts...")
            else:
                self.text.insert("\nUpdate Software...")

            self.text.insert("Unpacking file: {}".format(file))
            status = False
            extractdir = None
            try:
                basedir = os.path.dirname(file)
                basename = os.path.splitext(os.path.basename(file))[0]
                extractdir = basedir + "/" + basename
                archive = zipfile.ZipFile(file)
                archive.extractall(path=extractdir)
                u = UpdateSoftware(extractdir, self.text)
                status = (u.update_ema(self.emas, do_boot_flash=bootloader, bootloader_only=bootloader,
                                       scripts_only=scripts, do_reboot=not scripts)
                          and
                          u.update_csm(self.csms, do_boot_flash=bootloader, bootloader_only=bootloader,
                                       scripts_only=scripts, do_reboot=not scripts))
                # files = os.listdir(extractdir)
                # print(repr(files))
            except Exception as e:
                self.text.insert("ERROR: {}".format(e))
            if extractdir is not None:
                shutil.rmtree(extractdir)
            if status:
                self.text.insert("\n*** Software Update Succeeded ***")
                ret_val = True
            else:
                self.text.insert("\n*** Software Update FAILED ***")
            if not scripts:
                self.clear_ui_state()
        else:
            self.text.insert("Aborted - no file selected")
        return ret_val

    def zeroise_software_and_fill(self):
        self.text.insert("\nZeroise Software & Fill...")
        u = UpdateSoftware(None, self.text)
        u.zeroise_csms(self.csms)
        u.zeroise_emas(self.emas)
        self.text.insert("\n*** Zeroise Completed ***")

    def refresh_hw_config(self):
        global password_dict
        all_ok = True
        csm_pattern = re.compile(".*KT-950.*successfully refreshed$")
        ema_pattern = re.compile(".*EMA_.*B_.*[A|R] config info successfully refreshed$")
        for csm in self.csms:
            s = SSH(csm[1], password_dict)
            resp = s.send_command(self.CSM_REFRESH_HW_CONFIG_CMD).stderr.splitlines()
            ok = False
            for line in resp:
                if csm_pattern.match(line):
                    ok = True
            if ok:
                self.text.insert("{} config info updated".format(csm[0].rstrip(".local")))
            else:
                self.text.insert("ERROR: updating {} config info failed".format(csm[0]))
                all_ok = False
        for ema in self.emas:
            s = SSH(ema[1], password_dict)
            resp = s.send_command(self.EMA_REFRESH_HW_CONFIG_CMD).stderr.splitlines()
            ok = False
            for line in resp:
                if ema_pattern.match(line):
                    ok = True
            if ok:
                self.text.insert("{} config info updated".format(ema[0].rstrip(".local")))
            else:
                self.text.insert("ERROR: updating {} config info failed".format(ema[0]))
                all_ok = False
        return all_ok

    def recover_logs(self):
        global password_dict
        self.text.insert("\nRecover Log Files...")
        file_dir = filedialog.askdirectory()
        if file_dir is not None and file_dir != "":
            now = datetime.datetime.now()
            file_prefix = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}".format(now.year, now.month,
                                                                             now.day, now.hour,
                                                                             now.minute, now.second)
            for csm in self.csms:
                s = SSH(csm[1], password_dict)
                self.text.insert("Recovering logs from {}".format(csm[0].rstrip(".local")))
                for file_name in self.LOG_FILE_NAMES:
                    if "{}" in file_name:
                        file = file_name.format("csm")
                    else:
                        file = file_name
                    local_file = "{}/{}_{}_{}".format(file_dir, file_prefix, csm[0].rstrip(".local"), file)
                    try:
                        s.get_file("/run/media/mmcblk1p2/log/{}".format(file), local_file)
                        self.text.insert("  {}".format(local_file))
                    except FileNotFoundError:
                        pass
            for ema in self.emas:
                s = SSH(ema[1], password_dict)
                self.text.insert("Recovering logs from {}".format(ema[0].rstrip(".local")))
                for file_name in self.LOG_FILE_NAMES:
                    if "{}" in file_name:
                        file = file_name.format("ema")
                    else:
                        file = file_name
                    local_file = "{}/{}_{}_{}".format(file_dir, file_prefix, ema[0].rstrip(".local"), file)
                    try:
                        s.get_file("/run/media/mmcblk0p2/log/{}".format(file), local_file)
                        self.text.insert("  {}".format(local_file))
                    except FileNotFoundError:
                        pass
        else:
            self.text.insert("Aborted - no directory selected")

    def reconfigure_slot_order(self):
        self.text.insert("\r\nReconfigure Slot Order...")
        r = ReconfigureSlotOrder(self.text, self.csms)
        r.reconfigure()

    def reboot_system(self):
        global password_dict
        self.text.insert("\r\nReboot system...")
        for csm in self.csms:
            s = SSH(csm[1], password_dict)
            s.send_command(self.REBOOT_CMD).stderr.splitlines()
            self.text.insert("{} rebooted".format(csm[0].rstrip(".local")))
        for ema in self.emas:
            s = SSH(ema[1], password_dict)
            s.send_command(self.REBOOT_CMD).stderr.splitlines()
            self.text.insert("{} rebooted".format(ema[0].rstrip(".local")))

    def clear_ui_state(self):
        # Clear modules so that system discovery must be re-ran
        self.csms = []
        self.emas = []
        for key in self.buttons:
            # Disable all buttons except "Discover Modules"
            if key != "dsc":
                self.buttons[key]["state"] = DISABLED

    def ip_dialog(self):
        d = IpDialog(root, self)
        root.wait_window(d.top)

    def system_settings(self):
        d = SystemDialog(root, self)
        root.wait_window(d.top)

    def get_title(self):
        return "K-CEMA Maintenance Tool v{}.{}.{}".format(self.VERSION_MAJOR, self.VERSION_MINOR, self.VERSION_PATCH)

    def get_part_number(self):
        return "KT-956-0372-00"


class IpDialog:
    NETWORK_INTERFACES_FILE = "/etc/network/interfaces"
    RUN_FILE_CSM = "/run/media/mmcblk1p2/run.sh"
    SETTINGS_FILE_CSM = "/run/media/mmcblk1p2/settings/network_settings.json"
    SETTINGS_FILE_EMA = "/run/media/mmcblk0p2/settings/network_settings.json"
    REBOOT_CMD = "/sbin/reboot"

    def __init__(self, parent, app):
        self.app = app
        self.top = Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title("Set IP Addresses")
        self.top.iconbitmap("kirintec_logo.ico")
        self.top.geometry("+" + str(root.winfo_x() + 200) + "+" + str(root.winfo_y() + 50))
        self.modules = self.app.csms + self.app.emas
        self.get_slot_order()

        table_ip = Frame(self.top)
        label_slot = Label(table_ip, text="Slot", font="TkDefaultFont 10 bold")
        label_module = Label(table_ip, text="Module", font="TkDefaultFont 10 bold")
        label_mode = Label(table_ip, text="Mode", font="TkDefaultFont 10 bold")
        label_address = Label(table_ip, text="Address", font="TkDefaultFont 10 bold")
        label_netmask = Label(table_ip, text="Netmask", font="TkDefaultFont 10 bold")
        label_gateway = Label(table_ip, text="Gateway", font="TkDefaultFont 10 bold")
        button_retrieve = Button(self.top, text="Retrieve Settings", command=self.retrieve_settings)
        button_dhcp = Button(self.top, text="Set Default DHCP", command=self.default_dhcp)
        button_static = Button(self.top, text="Set Default Static IP", command=self.default_static)
        button_send = Button(self.top, text="Send Settings", command=self.send_settings)
        button_cancel = Button(self.top, text="Cancel", command=self.cancel)

        table_ip.pack()
        label_slot.grid(row=0, column=0)
        label_module.grid(row=0, column=1)
        label_mode.grid(row=0, column=2)
        label_address.grid(row=0, column=3)
        label_netmask.grid(row=0, column=4)
        label_gateway.grid(row=0, column=5)

        self.entries = []
        for module_hostname, module_ip, module_slot in self.modules:
            label_slot = Label(table_ip, text="{}".format(module_slot))
            label_module = Label(table_ip, text="{}".format(module_hostname.rstrip(".local")))
            cb_mode = ttk.Combobox(table_ip)
            cb_mode["values"] = ["DHCP", "Static"]
            cb_mode["state"] = "readonly"
            entry = {
                "slot": int(module_slot),
                "host": module_hostname,
                "current_ip": module_ip,
                "mode": cb_mode,
                "address": Entry(table_ip),
                "netmask": Entry(table_ip),
                "gateway": Entry(table_ip)
            }
            module_row = int(module_slot) + 1
            label_slot.grid(row=module_row, column=0)
            label_module.grid(row=module_row, column=1)
            entry["mode"].grid(row=module_row, column=2)
            entry["address"].grid(row=module_row, column=3)
            entry["netmask"].grid(row=module_row, column=4)
            entry["gateway"].grid(row=module_row, column=5)
            self.entries.append(entry)

        button_retrieve.pack(side=LEFT, expand=NO, padx=10, pady=25)
        button_dhcp.pack(side=LEFT, expand=NO, padx=10, pady=25)
        button_static.pack(side=LEFT, expand=NO, padx=10, pady=25)
        button_cancel.pack(side=RIGHT, expand=NO, padx=10, pady=25)
        button_send.pack(side=RIGHT, expand=NO, padx=10, pady=25)

    def reset_entries(self):
        for entry in self.entries:
            entry["mode"].set("")
            entry["address"].delete(0, END)
            entry["netmask"].delete(0, END)
            entry["gateway"].delete(0, END)
            entry["address"].config(state=DISABLED)
            entry["netmask"].config(state=DISABLED)
            entry["gateway"].config(state=DISABLED)

    def retrieve_settings(self):
        global password_dict
        temp_dir = TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, "interfaces")
        self.reset_entries()
        for entry in self.entries:
            s = SSH(entry["current_ip"], password_dict)
            s.get_file(self.NETWORK_INTERFACES_FILE, temp_file)
            found_eth0 = False
            mode = ""
            address = ""
            netmask = ""
            gateway = ""
            try:
                with open(temp_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("iface eth0"):
                            found_eth0 = True
                            mode = line.split(" ")[-1]
                        elif found_eth0:
                            if line.startswith("iface"):
                                # Another interface; stop processing
                                break
                            elif line.startswith("address"):
                                address = line.split(" ")[1]
                            elif line.startswith("netmask"):
                                netmask = line.split(" ")[1]
                            elif line.startswith("gateway"):
                                gateway = line.split(" ")[1]
                if mode.lower() == "dhcp":
                    entry["mode"].set("DHCP")
                elif mode.lower() == "static":
                    entry["mode"].set("Static")
                    entry["address"].config(state=NORMAL)
                    entry["netmask"].config(state=NORMAL)
                    entry["gateway"].config(state=NORMAL)
                    entry["address"].insert(0, address)
                    entry["netmask"].insert(0, netmask)
                    entry["gateway"].insert(0, gateway)
            except FileNotFoundError:
                self.app.text.insert("ERROR: could not retrieve {} from {}".format(self.NETWORK_INTERFACES_FILE,
                                                                                   entry["host"]))

    def default_dhcp(self):
        self.reset_entries()
        for entry in self.entries:
            entry["mode"].set("DHCP")

    def default_static(self):
        self.reset_entries()
        for entry in self.entries:
            entry["mode"].set("Static")
            entry["address"].config(state=NORMAL)
            entry["netmask"].config(state=NORMAL)
            entry["gateway"].config(state=NORMAL)
            entry["address"].insert(0, "192.168.1.{}".format(entry["slot"] + 10))
            entry["netmask"].insert(0, "255.255.255.0")
            entry["gateway"].insert(0, "192.168.1.254")

    def get_slot_order(self):
        global password_dict
        temp_dir = TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, "run.sh")
        # Connect to the CSM and get the run file
        s = SSH(self.modules[0][1], password_dict)
        s.get_file(self.RUN_FILE_CSM, temp_file)
        slots = {}
        with open(temp_file, "r") as f:
            for line in f:
                pattern = "^export SLOT_(?P<slot>[0-9])_MAC=(?P<mac>(?:(?:[0-9a-fA-F]){2}:){5}(?:[0-9a-fA-F]){2})$"
                match = re.fullmatch(pattern, line.strip())
                if match is not None:
                    slots[match.group("mac").lower()] = match.group("slot")
        for module in self.modules:
            if module[0].startswith("EMA"):
                mac = get_mac_address(ip=module[1]).lower()
                if mac in slots.keys():
                    # Append slot number to this EMA module
                    try:
                        module[2] = slots[mac]
                    except IndexError:
                        module.append(slots[mac])
                    self.app.text.insert("Slot {}, MAC {}, {}".format(slots[mac], mac, module[0]))
            else:
                # Assume this is a CSM and assign slot 0 to any CSM
                try:
                    module[2] = 0
                except IndexError:
                    module.append(0)

    def send_settings(self):
        global password_dict
        temp_dir = TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, "network_settings.json")
        for entry in self.entries:
            s = SSH(entry["current_ip"], password_dict)
            data = {
                "eth0": {
                    "mode": entry["mode"].get().lower(),
                    "address": entry["address"].get(),
                    "netmask": entry["netmask"].get(),
                    "gateway": entry["gateway"].get()
                }
            }
            with open(temp_file, "w") as file:
                json.dump(data, file, indent=4)
            remote_file = ""
            if entry["host"].startswith("CSM"):
                remote_file = self.SETTINGS_FILE_CSM
            elif entry["host"].startswith("EMA"):
                remote_file = self.SETTINGS_FILE_EMA
            if remote_file:
                self.app.text.insert("\nSending network settings to {}".format(entry["host"]))
                s.send_file(temp_file, remote_file)
                self.app.text.insert("Rebooting {}".format(entry["host"]))
                s.send_command(self.REBOOT_CMD)
        self.top.destroy()

    def cancel(self):
        self.top.destroy()


class SystemDialog:
    NMEA_SETTINGS_FILE = "/run/media/mmcblk1p2/settings/nmea_settings.json"
    SYSTEM_GROUP_SETTINGS_FILE = "/run/media/mmcblk1p2/settings/system_group_settings.json"

    def __init__(self, parent, app):
        self.app = app
        self.top = Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title("System Network Settings")
        self.top.iconbitmap("kirintec_logo.ico")
        self.top.geometry("+" + str(root.winfo_x() + 200) + "+" + str(root.winfo_y() + 50))
        table_settings = Frame(self.top)
        label_system_name = Label(table_settings, text="System Name:", font="TkDefaultFont 10")
        label_system_group = Label(table_settings, text="System Group:", font="TkDefaultFont 10")
        label_empty = Label(table_settings, text=" ", font="TkDefaultFont 10")
        label_nmea_mode = Label(table_settings, text="NMEA Mode:", font="TkDefaultFont 10")
        label_nmea_port = Label(table_settings, text="NMEA TCP Port:", font="TkDefaultFont 10")
        label_nmea_server_ip = Label(table_settings, text="NMEA Server IP:", font="TkDefaultFont 10")

        self.entry_system_name = Entry(table_settings)
        self.entry_system_group = Entry(table_settings)
        self.entry_nmea_port = Entry(table_settings)
        self.entry_nmea_server_ip = Entry(table_settings)
        self.nmea_modes = ("Client", "Server")
        self.var_nmea_mode = StringVar()
        self.var_nmea_mode.trace("w", self.nmea_mode_changed)
        self.var_nmea_mode.set(self.nmea_modes[0])
        self.option_nmea_mode = OptionMenu(table_settings, self.var_nmea_mode, *self.nmea_modes)

        table_settings.pack()
        label_system_name.grid(row=0, column=0, sticky="w")
        self.entry_system_name.grid(row=0, column=1, padx=5, sticky="w")
        label_system_group.grid(row=1, column=0, sticky="w")
        self.entry_system_group.grid(row=1, column=1, padx=5, sticky="w")
        label_empty.grid(row=2, column=0, columnspan=2, sticky="w")
        label_nmea_mode.grid(row=3, column=0, sticky="w")
        self.option_nmea_mode.grid(row=3, column=1, padx=5, sticky="w")
        label_nmea_port.grid(row=4, column=0, sticky="w")
        self.entry_nmea_port.grid(row=4, column=1, padx=5, sticky="w")
        label_nmea_server_ip.grid(row=5, column=0, sticky="w")
        self.entry_nmea_server_ip.grid(row=5, column=1, padx=5, sticky="w")

        button_retrieve = Button(self.top, text="Retrieve Settings", command=self.retrieve_settings)
        button_send = Button(self.top, text="Send Settings", command=self.send_settings)
        button_cancel = Button(self.top, text="Cancel", command=self.cancel)
        button_retrieve.pack(side=LEFT, expand=NO, padx=10, pady=25)
        button_send.pack(side=LEFT, expand=NO, padx=10, pady=25)
        button_cancel.pack(side=LEFT, expand=NO, padx=10, pady=25)
        try:
            self.csm_ip = self.app.csms[0][1]
        except Exception:
            self.csm_ip = ""

    def nmea_mode_changed(self, *args):
        if self.var_nmea_mode.get() == "Server":
            self.set_entry(self.entry_nmea_server_ip, "")
            self.entry_nmea_server_ip.config(state=DISABLED)
        else:
            self.entry_nmea_server_ip.config(state=NORMAL)

    def set_entry(self, entry, text):
        entry.delete(0, END)
        entry.insert(0, text)

    def retrieve_settings(self):
        global password_dict
        if self.csm_ip:
            temp_dir = TemporaryDirectory()
            temp_file = os.path.join(temp_dir.name, "settings")
            try:
                s = SSH(self.csm_ip, password_dict)
                s.get_file(self.NMEA_SETTINGS_FILE, temp_file)
                with open(temp_file, "r") as file:
                    data = json.load(file)
                    if "mode" in data:
                        if data["mode"] == "server":
                            self.var_nmea_mode.set(self.nmea_modes[1])
                        else:
                            self.var_nmea_mode.set(self.nmea_modes[0])
                    if "port" in data:
                        self.set_entry(self.entry_nmea_port, data["port"])
                    if "server_ip" in data:
                        self.set_entry(self.entry_nmea_server_ip, data["server_ip"])
            except json.decoder.JSONDecodeError:
                pass
            except FileNotFoundError:
                pass

            try:
                s.get_file(self.SYSTEM_GROUP_SETTINGS_FILE, temp_file)
                with open(temp_file, "r") as file:
                    data = json.load(file)
                    if "system_name" in data:
                        self.set_entry(self.entry_system_name, data["system_name"])
                    if "system_group" in data:
                        self.set_entry(self.entry_system_group, data["system_group"])
            except json.decoder.JSONDecodeError:
                pass
            except FileNotFoundError:
                pass

    def send_settings(self):
        global password_dict
        if self.csm_ip:
            temp_dir = TemporaryDirectory()
            temp_file = os.path.join(temp_dir.name, "settings")
            s = SSH(self.csm_ip, password_dict)

            # System/Group Settings
            data = {
                "system_name": self.entry_system_name.get(),
                "system_group": self.entry_system_group.get()
            }
            try:
                self.app.text.insert("Sending system name/group settings...")
                self.app.text.insert(data)
                self.app.text.insert("")
                with open(temp_file, "w") as file:
                    json.dump(data, file, indent=4)
                s.send_file(temp_file, self.SYSTEM_GROUP_SETTINGS_FILE)
            except Exception as e:
                self.app.text.insert("ERROR sending system name/group settings")
                self.app.text.insert(e)

            # NMEA Settings
            data = {
                "mode": self.var_nmea_mode.get().lower(),
                "port": self.entry_nmea_port.get(),
                "server_ip": self.entry_nmea_server_ip.get()
            }
            try:
                self.app.text.insert("Sending NMEA settings...")
                self.app.text.insert(data)
                self.app.text.insert("")
                self.app.text.insert("Note: system must be rebooted to start using new NMEA settings")
                self.app.text.insert("")
                with open(temp_file, "w") as file:
                    json.dump(data, file, indent=4)
                s.send_file(temp_file, self.NMEA_SETTINGS_FILE)
            except Exception as e:
                self.app.text.insert("ERROR sending NMEA settings")
                self.app.text.insert(e)
        self.top.destroy()

    def cancel(self):
        self.top.destroy()


if __name__ == "__main__":
    # Redirect stderr to stdout so that we see exceptions when running from console but stop
    # py2exe from trying to create an error log file which generates a user dialog when exiting the app
    sys.stderr = sys.stdout
    root = Tk()
    root.option_add('*font', ('verdana', 10))
    display = App(root)
    root.title(display.get_title())
    root.mainloop()
