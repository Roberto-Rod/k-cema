#!/usr/bin/env python3
import re

import json
import os
import pynmeagps
import shutil
import sys
import time
import threading
import tkinter
import zipfile
from enum import Enum
from pathlib import Path
from ping3 import ping
from ssh import SSH
from tempfile import TemporaryDirectory
from text_update import *
from tkinter import filedialog
from tkintermapview import TkinterMapView
from tksheet import Sheet

from invoke import loader

from kcema_system import *
from recover_software import *


class SelectedType(Enum):
    NONE = 0
    SYSTEM = 1
    GROUP = 2


class App:
    APP_VERSION = "1.0.0"
    APP_NAME = "K-CEMA Fleet Tool v" + APP_VERSION
    WIDTH = 1200
    HEIGHT = 800
    MAP_RADIUS = 7
    BUTTON_PADX = 10
    BUTTON_PADY = 5
    ACTION_BUTTON_WIDTH = 15
    ZOOM_WORLD = 0
    ZOOM_METRO = 9
    ZOOM_LOCAL = 18
    SHEET_REFRESH_MILLISECONDS = 500
    MAP_UPDATE_RATE = 10  # Number of sheet refreshes per map update
    JAM_REQUEST_FILE = "/var/tmp/jam_request"
    JAM_ACTIVE_FILE = "/var/tmp/jam_active"
    FAULT_FLAG_FILE = "/var/tmp/fault_flag"
    STOP_JAMMING_CMD = "/bin/rm {}".format(JAM_REQUEST_FILE)

    def __init__(self, systems, groups, mutex, root):
        # Get the user home directory and create our save directory if it doesn't already exist
        company_dir = os.path.join(Path.home(), ".Kirintec")
        save_dir = os.path.join(company_dir, "k-cema_fleet_tool")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        self.save_file = os.path.join(save_dir, "save_file.json")

        # The GUI main object
        self.root = root
        self.root.title(App.APP_NAME)
        self.root.iconbitmap("kirintec_logo.ico")
        self.root.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.root.minsize(App.WIDTH, App.HEIGHT)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.map_widget = None
        self.tile_server = None
        self.systems_sheet = None
        self.groups_sheet = None
        self.modules_sheet = None
        self.modules_title = None
        self.marker_list = []
        self.map_update_count = 0
        self.selected_group = ""
        self.selected_system_idx = 0
        self.selected_type = SelectedType.NONE
        self.systems = systems
        self.system_groups = groups
        self.mutex = mutex
        self.load_systems_from_file()

        # Create left and right frames inside main window
        root.grid_columnconfigure(0, weight=0)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)
        frame_left = Frame(master=root, width=150)
        frame_left.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        frame_right = Frame(master=root)
        frame_right.grid(row=0, column=1, rowspan=1, pady=5, padx=5, sticky="nsew")

        # No sub-frames inside left frame, configure for one row, one column
        frame_left.grid_rowconfigure(0, minsize=10)

        # Create top and bottom frames inside right frame
        frame_right.grid_columnconfigure(0, weight=1)
        frame_right.grid_rowconfigure(0, weight=1)
        frame_right.grid_rowconfigure(1, weight=1)
        frame_top = Frame(master=frame_right)
        frame_top.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        frame_bottom = Frame(master=frame_right)
        frame_bottom.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Create left and right frames inside top frame
        frame_top.grid_columnconfigure(0, weight=10)
        frame_top.grid_columnconfigure(1, weight=1)
        frame_top.grid_rowconfigure(0, weight=1)
        frame_top_left = Frame(master=frame_top)
        frame_top_left.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        frame_top_right = Frame(master=frame_top)
        frame_top_right.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Crete left and right frames inside bottom frame
        frame_bottom.grid_columnconfigure(0, weight=1)
        frame_bottom.grid_columnconfigure(1, weight=3)
        frame_bottom.grid_rowconfigure(0, weight=1)
        frame_bottom_left = Frame(master=frame_bottom)
        frame_bottom_left.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        frame_bottom_right = Frame(master=frame_bottom)
        frame_bottom_right.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Assign frames to variables which are named based on the frames' usage
        self.frame_actions = frame_left
        self.frame_systems = frame_top_left
        self.frame_groups = frame_top_right
        self.frame_modules = frame_bottom_left
        self.frame_map = frame_bottom_right

        # Create rows/columns in systems frame
        self.frame_systems.grid_rowconfigure(0, weight=0)
        self.frame_systems.grid_rowconfigure(1, weight=1)
        self.frame_systems.grid_columnconfigure(0, weight=0)
        self.frame_systems.grid_columnconfigure(1, weight=0)
        self.frame_systems.grid_columnconfigure(2, weight=0)
        self.frame_systems.grid_columnconfigure(3, weight=1)

        # Create rows/columns in groups frame
        self.frame_groups.grid_rowconfigure(0, weight=0)
        self.frame_groups.grid_rowconfigure(1, weight=1)
        self.frame_groups.grid_columnconfigure(0, weight=0)
        self.frame_groups.grid_columnconfigure(1, weight=0)
        self.frame_groups.grid_columnconfigure(2, weight=0)
        self.frame_groups.grid_columnconfigure(3, weight=1)

        # Create rows/columns in modules frame
        self.frame_modules.grid_rowconfigure(0, weight=0)
        self.frame_modules.grid_rowconfigure(1, weight=1)
        self.frame_modules.grid_columnconfigure(0, weight=1)

        # Create rows/columns in maps frame
        self.frame_map.grid_rowconfigure(0, weight=1)
        self.frame_map.grid_rowconfigure(1, weight=0)
        self.frame_map.grid_columnconfigure(0, weight=1)
        self.frame_map.grid_columnconfigure(1, weight=0)
        self.frame_map.grid_columnconfigure(2, weight=0)
        self.frame_map.grid_columnconfigure(3, weight=0)

        # Create action buttons
        self.create_action_buttons()

        # Create map buttons
        self.create_map_buttons()

        # Call Street View event to set a default tile server and create map widget
        self.street_view_event()

        # Create initial group list contents
        self.create_group_list()

        # Create initial module list contents
        self.create_module_list()

        # Create initial system list contents
        self.create_systems_list()

    def create_map_buttons(self):
        button_street = Button(master=self.frame_map, text="Street View", command=self.street_view_event)
        button_street.grid(row=1, column=3, sticky="w", padx=App.BUTTON_PADX, pady=App.BUTTON_PADY)
        button_satellite = Button(master=self.frame_map, text="Satellite View", command=self.satellite_view_event)
        button_satellite.grid(row=1, column=2, sticky="w", padx=App.BUTTON_PADX, pady=App.BUTTON_PADY)

    def create_action_buttons(self):
        # Add label above buttons
        group_action_label = Label(master=self.frame_actions, text="Actions", font="TkDefaultFont 10 bold")
        group_action_label.grid(row=1, column=0)

        # Add buttons to actions frame
        button_start_jam = Button(master=self.frame_actions, text="Start Jamming", width=self.ACTION_BUTTON_WIDTH,
                                  command=self.start_jamming_event)
        button_stop_jam = Button(master=self.frame_actions, text="Stop Jamming", width=self.ACTION_BUTTON_WIDTH,
                                 command=self.stop_jamming_event)
        button_update_mission = Button(master=self.frame_actions, text="Update Mission", width=self.ACTION_BUTTON_WIDTH,
                                       command=self.update_mission_event)
        button_recover_software = Button(master=self.frame_actions, text="Recover Software", width=self.ACTION_BUTTON_WIDTH,
                                         command=self.recover_software_event)
        button_reboot = Button(master=self.frame_actions, text="Reboot", width=self.ACTION_BUTTON_WIDTH,
                               command=self.reboot_event)
        button_zeroise = Button(master=self.frame_actions, text="Zeroise", width=self.ACTION_BUTTON_WIDTH,
                                command=self.zeroise_event)
        button_start_jam.grid(pady=App.BUTTON_PADY, padx=App.BUTTON_PADX, row=2, column=0)
        button_stop_jam.grid(pady=App.BUTTON_PADY, padx=App.BUTTON_PADX, row=3, column=0)
        button_update_mission.grid(pady=App.BUTTON_PADY, padx=App.BUTTON_PADX, row=4, column=0)
        button_recover_software.grid(pady=App.BUTTON_PADY, padx=App.BUTTON_PADX, row=5, column=0)
        button_reboot.grid(pady=App.BUTTON_PADY, padx=App.BUTTON_PADX, row=6, column=0)
        button_zeroise.grid(pady=App.BUTTON_PADY, padx=App.BUTTON_PADX, row=7, column=0)

    def create_map_widget(self):
        position = [51.9133319, -2.5821587]  # WSH
        zoom = 10
        if self.map_widget:
            position = self.map_widget.get_position()
            zoom = self.map_widget.zoom
            del self.map_widget
        self.map_widget = TkinterMapView(self.frame_map, width=450, height=250, corner_radius=App.MAP_RADIUS)
        self.map_widget.canvas.unbind("<MouseWheel>")
        self.map_widget.grid(row=0, rowspan=1, column=0, columnspan=4, sticky="nswe", padx=20, pady=20)
        self.map_widget.set_tile_server(self.tile_server, max_zoom=21)
        self.map_widget.set_position(position[0], position[1])
        self.map_widget.set_zoom(zoom)

    def create_group_list(self):
        label = Label(self.frame_groups, text="Groups", font="TkDefaultFont 10 bold")
        label.grid(row=0, column=0, columnspan=4, sticky="nw")
        self.groups_sheet = Sheet(self.frame_groups, total_rows=0, total_columns=1,
                                  headers=["Group"],
                                  header_font="TkDefaultFont 10 bold",
                                  show_row_index=False,
                                  show_top_left=False)
        self.groups_sheet.readonly_header()
        self.groups_sheet.readonly_columns()
        self.groups_sheet.enable_bindings("single_select", "edit_cell", "arrowkeys")
        self.groups_sheet.extra_bindings("cell_select", func=self.select_group_event)
        self.groups_sheet.grid(row=1, column=0, columnspan=4, sticky="nswe")
        self.add_group_event("<All Groups>")
        for group in self.system_groups:
            self.add_group_event(group)
            self.groups_sheet.set_all_cell_sizes_to_text()
            self.groups_sheet.redraw()

    def create_systems_list(self):
        label = Label(self.frame_systems, text="Systems", font="TkDefaultFont 10 bold")
        button_plus = Button(self.frame_systems, command=self.add_system_event, text="+")
        button_minus = Button(self.frame_systems, command=self.delete_system_event, text="-")
        label.grid(row=0, column=0, sticky="nw")
        button_plus.grid(row=0, column=1, sticky="nw")
        button_minus.grid(row=0, column=2, sticky="nw")
        self.systems_sheet = Sheet(self.frame_systems, total_rows=0, total_columns=8,
                                   headers=["IP Address", "System Name", "CSM Hostname", "Group",
                                            "State", "Health Status", "Location", "Poll Status"],
                                   header_font="TkDefaultFont 10 bold",
                                   show_row_index=False,
                                   show_top_left=False)
        self.systems_sheet.readonly_header()
        self.systems_sheet.readonly_columns([2, 4, 5, 6, 7])
        self.systems_sheet.enable_bindings("single_select", "drag_select", "edit_cell", "arrowkeys")
        self.systems_sheet.extra_bindings("cell_select", func=self.select_system_event)
        self.systems_sheet.grid(row=1, column=0, columnspan=4, sticky="nswe")
        for system in self.systems:
            self.add_system_to_systems_sheet(system)
        self.update_systems_on_map()
        self.refresh_sheets()

    def add_system_to_systems_sheet(self, system):
        self.systems_sheet.insert_row(values=[system.csm.ip_address, system.csm.system_name, system.csm.hostname,
                                              system.csm.system_group, system.csm.state, system.csm.health,
                                              system.csm.location, ""], redraw=True)
        self.systems_sheet.set_all_cell_sizes_to_text()
        self.systems_sheet.redraw()

    def create_module_list(self):
        self.mutex.acquire()
        selected_system = None
        selected_group = None
        label_text = ""
        if self.selected_type == SelectedType.GROUP:
            label_text = "Modules in Group: " + self.selected_group
            selected_group = self.selected_group
        elif self.selected_type == SelectedType.SYSTEM:
            if len(self.systems) > self.selected_system_idx:
                selected_system = self.systems[self.selected_system_idx]
                label_text = "Modules in System: " + self.get_system_name(selected_system)
        else:
            label_text = "Please Select a System or a Group"

        if not self.modules_title:
            self.modules_title = Label(master=self.frame_modules, text=label_text, font="TkDefaultFont 10 bold")
            self.modules_title.grid(row=0, column=0, sticky="nw")
        else:
            self.modules_title["text"] = label_text
        self.modules_sheet = Sheet(self.frame_modules, total_rows=0, total_columns=8,
                                   headers=["IP Address", "Parent System", "Module Hostname", "Band",
                                            "Software Version", "State", "Health Status", "Location"],
                                   header_font="TkDefaultFont 10 bold",
                                   show_row_index=False,
                                   show_top_left=False)
        self.modules_sheet.display_columns([0, 1, 2, 3, 4, 5], enable=True, refresh=True)
        self.modules_sheet.enable_bindings("single_select", "arrowkeys")
        self.modules_sheet.extra_bindings("cell_select", func=self.select_module_event)
        self.modules_sheet.grid(row=1, column=0, sticky="nswe")

        if selected_system:
            for system in self.systems:
                system.selected = False
            selected_system.selected = True
            csm = selected_system.csm
            self.modules_sheet.insert_row(values=[csm.ip_address, self.get_system_name(selected_system),
                                                  csm.hostname, "-", csm.software_version,
                                                  csm.state, csm.health, csm.location])
            for ema in selected_system.emas:
                self.modules_sheet.insert_row(values=[ema.ip_address, self.get_system_name(selected_system),
                                                      ema.hostname, ema.band, ema.software_version,
                                                      ema.state, ema.health, csm.location])
        elif selected_group:
            for system in self.systems:
                if selected_group == system.csm.system_group or selected_group == "<All Groups>":
                    system.selected = True
                    csm = system.csm
                    self.modules_sheet.insert_row(values=[csm.ip_address, self.get_system_name(system),
                                                          csm.hostname, "-", csm.software_version,
                                                          csm.state, csm.health, csm.location])
                    for ema in system.emas:
                        self.modules_sheet.insert_row(values=[ema.ip_address, self.get_system_name(system),
                                                              ema.hostname, ema.band, ema.software_version,
                                                              ema.state, ema.health, csm.location])
                else:
                    system.selected = False
        self.mutex.release()
        self.modules_sheet.set_all_cell_sizes_to_text()
        self.modules_sheet.redraw()
        self.modules_sheet.select_cell(row=0, column=0)

    def street_view_event(self, event=None):
        self.tile_server = "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga"
        self.create_map_widget()
        self.update_systems_on_map()

    def satellite_view_event(self, event=None):
        self.tile_server = "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga"
        self.create_map_widget()
        self.update_systems_on_map()

    def add_system_marker(self, system):
        location = system.csm.location.split(",")
        if len(location) == 2:
            lat = float(location[0])
            long = float(location[1])
            marker_text = self.get_system_name(system)
            state = system.csm.state
            health = system.csm.health
            # Default marker colour grey
            marker_colour_outside = "#A6ACAF"
            marker_colour_circle = "#CACFD2"
            if health == "FAULT":
                # Red
                marker_colour_outside = "#C0392B"
                marker_colour_circle = "#EC7063"
            elif state == "Standby":
                # Yellow
                marker_colour_outside = "#F4D03F"
                marker_colour_circle = "#F7DC6F"
            elif state.startswith("Jamming"):
                # Green
                marker_colour_outside = "#229954"
                marker_colour_circle = "#52BE80"

            marker = self.map_widget.set_marker(lat, long,
                                                text=marker_text,
                                                text_color="#000000",
                                                font="Arial 11 bold",
                                                marker_color_circle=marker_colour_circle,
                                                marker_color_outside=marker_colour_outside)
            self.marker_list.append(marker)

    def clear_markers(self):
        for marker in self.marker_list:
            marker.delete()

    def update_systems_on_map(self):
        self.clear_markers()
        if self.selected_type == SelectedType.GROUP:
            for system in self.systems:
                if system.csm.system_group == self.selected_group or self.selected_group == "<All Groups>":
                    self.add_system_marker(system)
        else:
            if len(self.systems) > self.selected_system_idx:
                self.add_system_marker(self.systems[self.selected_system_idx])

    def add_group_event(self, group="<New Group>"):
        nr_rows = self.groups_sheet.get_total_rows()
        # If this is the <All Groups> alias then insert it as the next element
        # Find the position for any other groups alphabetically
        if group == "<All Groups>":
            insert_row = nr_rows
        elif self.groups_sheet.get_total_rows() > 0:
            # If we don't find an insert position then insert at the end
            insert_row = nr_rows
            for row in range(2, nr_rows):
                this_group = self.groups_sheet.get_cell_data(row, 0)
                if group > this_group:
                    # Insert the new group before the one we've found in the sheet
                    self.groups_sheet.insert_row()
                    break
        self.groups_sheet.insert_row(values=[group], idx=insert_row)
        self.groups_sheet.readonly_cells(row=insert_row, column=0)
        self.groups_sheet.set_all_cell_sizes_to_text()
        self.groups_sheet.redraw()

    # TODO: remove function
    def delete_group_event(self):
        if self.groups_sheet:
            rows = self.groups_sheet.get_selected_rows(get_cells_as_rows=True)
            # Selected rows will be a contiguous set, each time we delete the row numbers change so delete
            # the first index in the set each time we delete and delete number of rows based on length of the set
            first_row = -1
            number_rows = -1
            try:
                if rows:
                    number_rows = len(rows)
                    first_row = rows.pop()
                    for i in range(number_rows):
                        group = self.groups_sheet.get_cell_data(r=first_row, c=0)
                        if group != "<All Groups>":
                            self.groups_sheet.delete_row(idx=first_row, redraw=True)
                    self.groups_sheet.select_cell(first_row, 0)
            except:
                print("ERROR deleting rows: {}, {}".format(first_row, number_rows))

    def select_group_event(self, event=None):
        # Deselect all in the systems sheet when a group is selected
        self.systems_sheet.deselect("all")
        self.selected_group = self.groups_sheet.get_cell_data(event.row, event.column)
        self.selected_type = SelectedType.GROUP
        self.create_module_list()
        self.update_systems_on_map()
        if self.selected_group == "<All Groups>":
            self.map_widget.set_zoom(self.ZOOM_WORLD)
        else:
            self.map_widget.set_zoom(self.ZOOM_METRO)

    def select_system_event(self, event=None):
        if event:
            # Deselect all in the groups sheet when a system is selected
            self.groups_sheet.deselect("all")
            self.selected_system_idx = event.row
            self.selected_type = SelectedType.SYSTEM
            self.create_module_list()
            self.update_systems_on_map()
            self.map_widget.set_zoom(self.ZOOM_LOCAL)

    def select_module_event(self, event=None):
        module_sheet_location_column = 7
        if event:
            location_str = self.modules_sheet.get_cell_data(event.row, module_sheet_location_column)
            if location_str:
                location = location_str.split(",")
                self.map_widget.set_position(float(location[0]), float(location[1]))

    def get_system_name(self, system):
        if system.csm.system_name == "":
            return system.csm.ip_address
        else:
            return system.csm.system_name

    def refresh_sheets(self):
        self.mutex.acquire()
        # Update systems sheet
        try:
            for row in range(self.systems_sheet.get_total_rows()):
                ip = self.systems_sheet.get_cell_data(r=row, c=0)
                for system in self.systems:
                    if system.csm.ip_address == ip:
                        self.systems_sheet.set_cell_data(r=row, c=1, value=system.csm.system_name)
                        self.systems_sheet.set_cell_data(r=row, c=2, value=system.csm.hostname)
                        self.systems_sheet.set_cell_data(r=row, c=3, value=system.csm.system_group)
                        self.systems_sheet.set_cell_data(r=row, c=4, value=system.csm.state)
                        self.systems_sheet.set_cell_data(r=row, c=5, value=system.csm.health)
                        self.systems_sheet.set_cell_data(r=row, c=6, value=system.csm.location)
                        self.systems_sheet.set_cell_data(r=row, c=7, value=system.poll_status)
            self.systems_sheet.set_all_cell_sizes_to_text()
            self.systems_sheet.redraw()
            # Update groups sheet
            refresh_groups = False
            groups = []
            for row in range(self.groups_sheet.get_total_rows()):
                groups.append(self.groups_sheet.get_cell_data(r=row, c=0))
            for group in self.system_groups:
                if group not in groups:
                    refresh_groups = True
                    break
            if refresh_groups:
                self.add_group_event(group)
            # Update modules sheet
            for row in range(self.modules_sheet.get_total_rows()):
                ip = self.modules_sheet.get_cell_data(r=row, c=0)
                for system in self.systems:
                    if system.csm.ip_address == ip:
                        self.modules_sheet.set_cell_data(r=row, c=1, value=system.csm.system_name)
                        self.modules_sheet.set_cell_data(r=row, c=2, value=system.csm.hostname)
                        self.modules_sheet.set_cell_data(r=row, c=4, value=system.csm.software_version)
                        self.modules_sheet.set_cell_data(r=row, c=5, value=system.csm.state)
                        self.modules_sheet.set_cell_data(r=row, c=6, value=system.csm.health)
                        self.modules_sheet.set_cell_data(r=row, c=7, value=system.csm.location)
                    else:
                        for ema in system.emas:
                            if ema.ip_address == ip:
                                self.modules_sheet.set_cell_data(r=row, c=1, value=system.csm.system_name)
                                self.modules_sheet.set_cell_data(r=row, c=2, value=ema.hostname)
                                self.modules_sheet.set_cell_data(r=row, c=3, value=ema.band)
                                self.modules_sheet.set_cell_data(r=row, c=4, value=ema.software_version)
                                self.modules_sheet.set_cell_data(r=row, c=5, value=ema.state)
                                self.modules_sheet.set_cell_data(r=row, c=6, value=ema.health)
                                self.modules_sheet.set_cell_data(r=row, c=7, value=system.csm.location)
            self.modules_sheet.set_all_cell_sizes_to_text()
            self.modules_sheet.redraw()
            # Update the map pin-points every N cycles
            if self.map_update_count == self.MAP_UPDATE_RATE - 1:
                self.map_update_count = 0
                self.update_systems_on_map()
            else:
                self.map_update_count += 1
        except Exception:
            pass
        # Release the mutex
        self.mutex.release()
        # Refresh again after 500 ms
        self.root.after(self.SHEET_REFRESH_MILLISECONDS, self.refresh_sheets)

    def get_selected_systems(self):
        csms = []
        emas = []
        self.mutex.acquire()
        if self.selected_type == SelectedType.SYSTEM:
            if len(self.systems) > self.selected_system_idx:
                csms.append(self.systems[self.selected_system_idx].csm)
                emas.extend(self.systems[self.selected_system_idx].emas)
        elif self.selected_type == SelectedType.GROUP:
            for system in systems:
                if self.selected_group == "<All Groups>" or system.csm.system_group == self.selected_group:
                    csms.append(system.csm)
                    emas.extend(system.emas)
        self.mutex.release()
        return csms, emas

    def get_selected_ips(self):
        csm_ips = []
        ema_ips = []
        self.mutex.acquire()
        if self.selected_type == SelectedType.SYSTEM:
            if len(self.systems) > self.selected_system_idx:
                ips = self.systems[self.selected_system_idx].get_ip_addresses()
                csm_ips.append(ips["csm_ip_address"])
                ema_ips.extend(ips["ema_ip_addresses"])
        elif self.selected_type == SelectedType.GROUP:
            for system in systems:
                if self.selected_group == "<All Groups>" or system.csm.system_group == self.selected_group:
                    ips = system.get_ip_addresses()
                    csm_ips.append(ips["csm_ip_address"])
                    ema_ips.extend(ips["ema_ip_addresses"])
        self.mutex.release()
        return csm_ips, ema_ips

    def start_jamming_event(self):
        # Create the jam request file with the mission slot number in it
        temp_dir = TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, "jam_request")
        try:
            with open(temp_file, "w") as f:
                f.write("1")
            # Get a list of the CSM IPs to be operated on
            csm_ips, ema_ips = self.get_selected_ips()
            for ip in csm_ips:
                ssh = SSH(ip)
                ssh.send_file(temp_file, self.JAM_REQUEST_FILE)
        except Exception:
            pass

    def stop_jamming_event(self):
        # Get a list of the CSM IPs to be operated on
        csm_ips, ema_ips = self.get_selected_ips()
        for ip in csm_ips:
            ssh = SSH(ip)
            resp = ssh.send_command(self.STOP_JAMMING_CMD)

    def update_mission_event(self):
        csms, emas = self.get_selected_systems()
        if csms or emas:
            d = RecoverSoftwareDialog(self, csms, emas, Action.UPLOAD_MISSION)
            self.root.wait_window(d.top)

    def recover_software_event(self):
        csms, emas = self.get_selected_systems()
        if csms or emas:
            d = RecoverSoftwareDialog(self, csms, emas, Action.RECOVER_SOFTWARE)
            self.root.wait_window(d.top)

    def reboot_event(self):
        csms, emas = self.get_selected_systems()
        if csms or emas:
            d = RecoverSoftwareDialog(self, csms, emas, Action.REBOOT_SYSTEMS)
            self.root.wait_window(d.top)

    def zeroise_event(self):
        # Get a list of all the module IPs to be zeroised
        csms, emas = self.get_selected_systems()
        if csms or emas:
            d = RecoverSoftwareDialog(self, csms, emas, Action.ZEROISE_SYSTEMS)
            self.root.wait_window(d.top)

    def save_systems_to_file(self):
        self.mutex.acquire()
        data = []
        for system in systems:
            data.append(system.get_ip_addresses())
        with open(self.save_file, "w") as file:
            json.dump(data, file)
        self.mutex.release()

    def load_systems_from_file(self):
        self.mutex.acquire()
        try:
            with open(self.save_file, "r") as file:
                data = json.load(file)
            for system in data:
                self.systems.append(KCEMASystem(system["csm_ip_address"], system["ema_ip_addresses"]))
        except FileNotFoundError:
            print("Warning: {} not found".format(self.save_file))
        self.mutex.release()

    def add_system_event(self):
        d = AddSystemDialog(self)
        self.root.wait_window(d.top)

    def delete_system_event(self):
        if self.selected_type == SelectedType.SYSTEM:
            d = DeleteSystemDialog(self, self.selected_system_idx)
            self.root.wait_window(d.top)
        if False:
            if self.systems_sheet:
                rows = self.systems_sheet.get_selected_rows(get_cells_as_rows=True)
                columns = self.systems_sheet.get_selected_columns(get_cells_as_columns=True)
                # Selected rows will be a contiguous set, each time we delete the row numbers change so delete
                # the first index in the set each time we delete and delete number of rows based on length of the set
                first_row = -1
                number_rows = -1
                try:
                    if rows and columns:
                        number_rows = len(rows)
                        first_row = rows.pop()
                        first_column = columns.pop()
                        self.mutex.acquire()
                        print("Delete rows...")
                        for i in range(number_rows):
                            self.systems_sheet.delete_row(idx=first_row, redraw=True)
                        self.mutex.release()
                        self.systems_sheet.select_cell(first_row, first_column)
                except:
                    print("ERROR deleting rows: {}, {}".format(first_row, number_rows))

    def on_closing(self, event=0):
        self.root.destroy()

    def start(self):
        self.root.mainloop()


class AddSystemDialog:
    def __init__(self, parent):
        self.parent = parent
        self.top = Toplevel(parent.root)
        self.top.transient(parent.root)
        self.top.grab_set()
        self.top.iconbitmap("kirintec_logo.ico")
        self.top.title("Add System")
        self.top.geometry("+" + str(parent.root.winfo_x() + 200) + "+" + str(parent.root.winfo_y() + 50))
        self.top.resizable(False, False)
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_columnconfigure(1, weight=0)
        self.top.grid_columnconfigure(2, weight=0)
        self.top.grid_columnconfigure(3, weight=0)
        self.top.grid_rowconfigure(0, weight=1)
        self.top.grid_rowconfigure(1, weight=1)
        self.top.grid_rowconfigure(2, weight=1)
        self.top.grid_rowconfigure(3, weight=1)
        self.top.grid_rowconfigure(4, weight=1)
        self.top.grid_rowconfigure(5, weight=1)
        self.top.grid_rowconfigure(6, weight=1)
        label_csm_ip = Label(master=self.top, text="CSM IP Addres")
        self.entry_csm_ip = Entry(master=self.top)
        label_csm_ip.grid(row=0, column=0, sticky="w")
        self.entry_csm_ip.grid(row=0, column=1, columnspan=3, padx=10, pady=3, sticky="nswe")
        self.entry_ema_ip = []
        for i in range(5):
            label_ema_ip = Label(master=self.top, text="EMA {} IP Address".format(i+1))
            self.entry_ema_ip.append(Entry(master=self.top))
            label_ema_ip.grid(row=i+1, column=0, sticky="w")
            self.entry_ema_ip[i].grid(row=i+1, column=1, columnspan=3, padx=10, pady=3, sticky="nswe")
        button_fill = Button(master=self.top, text="Fill EMA IPs", command=self.fill_ema_event)
        button_add = Button(master=self.top, text="Add", command=self.add_event)
        button_cancel = Button(master=self.top, text="Cancel", command=self.cancel_event)
        button_fill.grid(row=6, column=1, padx=10, pady=10, sticky="e")
        button_add.grid(row=6, column=2, padx=10, pady=10, sticky="e")
        button_cancel.grid(row=6, column=3, padx=10, pady=10, sticky="e")

    def fill_ema_event(self):
        csm_ip = self.entry_csm_ip.get()
        if csm_ip:
            octets = csm_ip.split(".")
            if len(octets) == 4:
                try:
                    ema_base = int(octets[3]) + 1
                    for i in range(5):
                        ema_ip = "{}.{}.{}.{}".format(octets[0], octets[1], octets[2], ema_base + i)
                        entry = self.entry_ema_ip[i]
                        entry.delete(0, END)
                        entry.insert(0, ema_ip)
                except ValueError:
                    pass

    def add_event(self):
        # Get the mutex before removing the system from the list
        self.parent.mutex.acquire()
        # Perform all the add actions before destroying the dialog
        csm_ip = self.entry_csm_ip.get()
        ema_ips = []
        for i in range(5):
            ema_ip = self.entry_ema_ip[i].get()
            if ema_ip:
                ema_ips.append(ema_ip)
        new_system = KCEMASystem(csm_ip, ema_ips)
        self.parent.systems.append(new_system)

        # Add the new system to the parent systems list and to the UI systems sheet
        self.parent.add_system_to_systems_sheet(new_system)
        # Save updated system list to file
        self.parent.save_systems_to_file()
        self.parent.mutex.release()
        self.top.destroy()

    def cancel_event(self):
        self.top.destroy()


class RecoverSoftwareDialog:
    TITLE = {
        Action.RECOVER_SOFTWARE: "Recover Software",
        Action.UPLOAD_MISSION: "Upload Mission",
        Action.ZEROISE_SYSTEMS: "Zeroise Systems",
        Action.REBOOT_SYSTEMS: "Reboot Systems"
    }

    def __init__(self, parent, csms, emas, action=Action.ZEROISE_SYSTEMS):
        self.csms = csms
        self.emas = emas
        self.parent = parent
        self.top = Toplevel(parent.root)
        self.top.transient(parent.root)
        self.top.grab_set()
        self.top.iconbitmap("kirintec_logo.ico")
        self.top.geometry("+" + str(parent.root.winfo_x() + 200) + "+" + str(parent.root.winfo_y() + 50))
        self.top.resizable(False, False)
        self.top.title(RecoverSoftwareDialog.TITLE[action])
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_columnconfigure(1, weight=0)
        self.top.grid_columnconfigure(2, weight=0)
        self.top.grid_rowconfigure(0, weight=1)
        self.top.grid_rowconfigure(1, weight=1)
        self.top.grid_rowconfigure(2, weight=1)
        self.top.grid_rowconfigure(3, weight=1)
        self.top.grid_rowconfigure(4, weight=0)
        textbox = Text(self.top)
        self.text = TextUpdate(textbox, parent.root)
        self.text.insert(RecoverSoftwareDialog.TITLE[action])
        self.button_cancel = Button(master=self.top, text="Cancel", command=self.cancel_event)
        textbox.grid(row=0, column=0, columnspan=3, rowspan=4, padx=10, pady=10, sticky="nswe")
        if action == Action.RECOVER_SOFTWARE:
            self.button_select = Button(master=self.top, text="Select Package", command=self.select_package)
            self.text.insert("\nPress Select Package to continue")
        elif action == Action.UPLOAD_MISSION:
            self.button_select = Button(master=self.top, text="Upload Mission", command=self.upload_mission)
            self.text.insert("\nPress Upload Mission to continue")
        elif action == Action.ZEROISE_SYSTEMS:
            self.button_select = Button(master=self.top, text="ZEROISE", command=self.zeroise_systems)
            self.text.insert("\nThis will zeroise software and fills on selected systems!")
            self.text.insert("If you are sure you want to proceed then press ZEROISE")
        elif action == Action.REBOOT_SYSTEMS:
            self.text.insert("\nThis will reboot selected systems!")
            self.text.insert("If you are sure you want to proceed then press Reboot")
            self.button_select = Button(master=self.top, text="Reboot", command=self.reboot_systems)
        self.button_select.grid(row=4, column=1, padx=10, pady=10, sticky="e")
        self.button_cancel.grid(row=4, column=2, padx=10, pady=10, sticky="e")

    def zeroise_systems(self):
        u = RecoverSoftware(self.parent, self.text)
        u.zeroise_csms(self.csms)
        u.zeroise_emas(self.emas)
        self.done_event()

    def reboot_systems(self):
        u = RecoverSoftware(self.parent, self.text)
        u.reboot_csms(self.csms)
        u.reboot_emas(self.emas)
        self.done_event()

    def upload_mission(self):
        file = filedialog.askopenfilename(filetypes=[("IFF Files", "*.iff")])
        if file is not None and file != "":
            self.text.insert("Uploading file: {}\n".format(file))
            u = RecoverSoftware(self.parent, self.text)
            u.upload_mission(self.csms, self.emas, file)
            self.done_event()

    def select_package(self):
        file = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if file is not None and file != "":
            self.text.insert("Unpacking file: {}\n".format(file))
            status = False
            extract_dir = None
            try:
                basedir = os.path.dirname(file)
                basename = os.path.splitext(os.path.basename(file))[0]
                extract_dir = basedir + "/" + basename
                archive = zipfile.ZipFile(file)
                archive.extractall(path=extract_dir)
                u = RecoverSoftware(self.parent, self.text, extract_dir)
                status = u.update_csm(self.csms) and u.update_ema(self.emas)
                # files = os.listdir(extract_dir)
                # print(repr(files))
            except Exception as e:
                self.text.insert("ERROR: {}".format(e))
            if extract_dir is not None:
                shutil.rmtree(extract_dir)
            if status:
                self.text.insert("\n*** Software Update Succeeded ***")
                self.done_event()
            else:
                self.text.insert("\n*** Software Update FAILED ***")
        else:
            self.text.insert("Aborted - no file selected")

    def done_event(self):
        self.button_select.config(state="disabled")
        self.button_cancel["text"] = "Done"

    def cancel_event(self):
        self.top.destroy()


class DeleteSystemDialog:
    def __init__(self, parent, system_idx):
        if len(parent.systems) > system_idx:
            self.system = parent.systems[system_idx]
            system_ip = self.system.csm.ip_address
            system_group = self.system.csm.system_group
            system_name = parent.get_system_name(self.system)
            self.system_idx = system_idx
            self.parent = parent
            self.top = Toplevel(parent.root)
            self.top.transient(parent.root)
            self.top.grab_set()
            self.top.iconbitmap("kirintec_logo.ico")
            self.top.geometry("+" + str(parent.root.winfo_x() + 200) + "+" + str(parent.root.winfo_y() + 50))
            self.top.resizable(False, False)
            self.top.title("Delete System {}".format(system_name))
            self.top.grid_columnconfigure(0, weight=1)
            self.top.grid_columnconfigure(1, weight=0)
            self.top.grid_columnconfigure(2, weight=0)
            self.top.grid_rowconfigure(0, weight=1)
            self.top.grid_rowconfigure(1, weight=1)
            self.top.grid_rowconfigure(2, weight=1)
            self.top.grid_rowconfigure(3, weight=1)
            self.top.grid_rowconfigure(4, weight=1)
            if system_name == system_ip:
                system_name = "<unknown>"
            if system_group == "":
                system_group = "<unknown>"
            message = "Delete the following system from the Fleet Tool?\n\n"\
                      "This stops the Fleet Tool from tracking the system.\n\n"\
                      "No action is taken on the system."
            label_message = Label(master=self.top, text=message)
            label_ip = Label(master=self.top, text="CSM IP Address: {}".format(system_ip))
            label_name = Label(master=self.top, text="System Name: {}".format(system_name))
            label_group = Label(master=self.top, text="Group: {}".format(system_group))
            button_delete = Button(master=self.top, text="Delete", command=self.delete_event)
            button_cancel = Button(master=self.top, text="Cancel", command=self.cancel_event)
            label_message.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nswe")
            label_ip.grid(row=1, column=0, columnspan=3, padx=10, pady=0, sticky="w")
            label_name.grid(row=2, column=0, columnspan=3, padx=10, pady=0, sticky="w")
            label_group.grid(row=3, column=0, columnspan=3, padx=10, pady=0, sticky="w")
            button_delete.grid(row=4, column=1, padx=10, pady=10, sticky="w")
            button_cancel.grid(row=4, column=2, padx=10, pady=10, sticky="e")

    def delete_event(self):
        # Get the mutex before removing the system from the list
        self.parent.mutex.acquire()
        # Perform all the deletion actions before destroying the dialog
        del self.parent.systems[self.system_idx]
        # Check that the index refers to the systems sheet row with the expected CSM IP address in it
        ip = self.parent.systems_sheet.get_cell_data(self.system_idx, 0)
        if ip == self.system.csm.ip_address:
            self.parent.systems_sheet.delete_row(self.system_idx, deselect_all=True, redraw=True)
        # Clear the modules list in the parent window
        self.parent.selected_type = SelectedType.NONE
        self.parent.create_module_list()
        # Save updated system list to file
        self.parent.save_systems_to_file()
        self.parent.mutex.release()
        self.top.destroy()

    def cancel_event(self):
        self.top.destroy()


class SystemPollThread(threading.Thread):
    SYSTEM_GROUP_SETTINGS_FILE = "/run/media/mmcblk1p2/settings/system_group_settings.json"
    JAM_ACTIVE_FILE = "/var/tmp/jam_active"
    FAULT_FLAG_FILE = "/var/tmp/fault_flag"
    GET_HOSTNAME_CMD = "/bin/hostname"
    GET_GNSS_POSITION_CMD = "/usr/bin/get_nmea_gnrmc /dev/ttyUL8"
    CHECK_EMA_APP_CMD = "/bin/ls /run/media/mmcblk0p1/ema_app.bin"
    CHECK_CSM_APP_CMD = "/bin/ls /run/media/mmcblk1p1/csm_app.bin"
    CHECK_APP_REGEXP = "^.*cannot access.*$"
    GET_BAND_EMA_CMD = "/usr/bin/getband"
    GET_CSM_VERSION_CMD = "/bin/grep Application:\ Version /run/media/mmcblk1p2/log/k-cema-csm.log -a | tail -1"
    GET_EMA_VERSION_CMD = "/bin/grep Application:\ Version /run/media/mmcblk0p2/log/k-cema-ema.log -a | tail -1"
    VERSION_REGEXP = "^.*Application: Version (?P<version>[0-9]+\.[0-9]+\.[0-9]+) \(Build ID: (?P<build_id>[0-9a-f]{8})\).*$"

    def __init__(self, systems, groups, mutex):
        threading.Thread.__init__(self)
        self.systems = systems
        self.groups = groups
        self.mutex = mutex
        self.quit = False

    def run(self):
        while not self.quit:
            for system in self.systems:
                if self.quit:
                    break
                self.mutex.acquire()
                ip = system.csm.ip_address
                system.poll_status = "Polling..."
                self.mutex.release()
                poll_status = "Not Found"
                csm_hostname = ""
                csm_state = ""
                csm_health = ""
                csm_software_version = ""
                system_location = ""
                system_name = ""
                system_group = ""
                # Can we ping the module?
                resp = ping(ip)
                # resp may be None or False if the ping failed
                # resp will be a float if the ping succeeded and this
                # may be 0.0 which would evaluate as False so test the type
                if type(resp) == float:
                    poll_status = "Found"
                    ssh = SSH(ip)
                    # Get CSM hostname if we haven't already found it
                    if system.csm.hostname:
                        csm_hostname = system.csm.hostname
                    else:
                        resp = ssh.send_command(self.GET_HOSTNAME_CMD)
                        if resp:
                            # TODO: check that hostname makes sense
                            csm_hostname = resp.stdout.strip()
                        else:
                            poll_status = "Lost"
                    # Get GNSS position
                    resp = ssh.send_command(self.GET_GNSS_POSITION_CMD)
                    if resp:
                        try:
                            gnss_data = pynmeagps.NMEAReader.parse(resp.stdout.strip())
                            # Status code is "A" for valid
                            if gnss_data.status == "A":
                                system_location = "{},{}".format(gnss_data.lat, gnss_data.lon)
                        except pynmeagps.NMEAParseError:
                            print("ERROR: NMEA parse error")
                    else:
                        poll_status = "Lost"
                    # Get system & group name
                    temp_dir = TemporaryDirectory()
                    temp_file = os.path.join(temp_dir.name, "interfaces")
                    try:
                        if not ssh.get_file(self.SYSTEM_GROUP_SETTINGS_FILE, temp_file):
                            poll_status = "Lost"
                    except FileNotFoundError:
                        print("ERROR: {} not found".format(self.SYSTEM_GROUP_SETTINGS_FILE))
                    try:
                        with open(temp_file, "r") as f:
                            data = json.load(f)
                            if "system_name" in data:
                                system_name = data["system_name"]
                            if "system_group" in data:
                                system_group = data["system_group"]
                    except FileNotFoundError:
                        print("ERROR: {} not found".format(temp_file))
                    except json.decoder.JSONDecodeError:
                        print("ERROR: invalid JSON data in {}".format(temp_file))
                    # Get jamming status, if anything goes wrong then leave csm state empty
                    try:
                        if ssh.get_file(self.JAM_ACTIVE_FILE, temp_file):
                            with open(temp_file, "r") as f:
                                slot = int(f.readline())
                                if slot == 0:
                                    csm_state = "Standby"
                                elif 5 >= slot >= 1:
                                    csm_state = "Jamming"
                    except Exception:
                        pass
                    # Get health status
                    try:
                        if ssh.get_file(self.FAULT_FLAG_FILE, temp_file):
                            with open(temp_file, "r") as f:
                                fault = int(f.readline())
                                if fault == 0:
                                    csm_health = "OK"
                                else:
                                    csm_health = "FAULT"
                    except Exception:
                        pass
                    # Get CSM software version
                    try:
                        resp = ssh.send_command(self.GET_CSM_VERSION_CMD)
                        if resp:
                            match = re.match(self.VERSION_REGEXP, resp.stdout.strip())
                            csm_software_version = "{} ({})".format(match.group("version"), match.group("build_id"))
                    except Exception:
                        pass
                    # Check if CSM is zeroised
                    try:
                        resp = ssh.send_command(self.CHECK_CSM_APP_CMD)
                        if resp.stderr:
                            match = re.match(self.CHECK_APP_REGEXP, resp.stderr.strip())
                            if match:
                                csm_state = "Zeroised"
                    except Exception:
                        pass

                # If this is the selected system or it is in the selected group then get EMA data
                ema_hostnames = []
                ema_states = []
                ema_bands = []
                ema_software_versions = []

                if system.selected:
                    for ema in system.emas:
                        if self.quit:
                            break
                        ema_hostname = ""
                        ema_state = ""
                        ema_software_version = ""
                        ema_band = ""
                        # Can we ping the module?
                        resp = ping(ema.ip_address)
                        if type(resp) == float:
                            ssh = SSH(ema.ip_address)
                            # Get EMA hostname
                            resp = ssh.send_command(self.GET_HOSTNAME_CMD)
                            if resp:
                                # TODO: check that hostname makes sense
                                ema_hostname = resp.stdout.strip()
                            # Get EMA software version
                            try:
                                resp = ssh.send_command(self.GET_EMA_VERSION_CMD)
                                if resp:
                                    match = re.match(self.VERSION_REGEXP, resp.stdout.strip())
                                    ema_software_version = "{} ({})".format(match.group("version"), match.group("build_id"))
                            except Exception:
                                pass
                            # Get EMA band
                            try:
                                resp = ssh.send_command(self.GET_BAND_EMA_CMD)
                                if resp:
                                    ema_band = resp.stdout.strip()
                            except Exception:
                                pass
                            # Check if EMA is zeroised
                            try:
                                resp = ssh.send_command(self.CHECK_EMA_APP_CMD)
                                if resp.stderr:
                                    match = re.match(self.CHECK_APP_REGEXP, resp.stderr.strip())
                                    if match:
                                        ema_state = "Zeroised"
                                else:
                                    ema_state = csm_state
                            except Exception:
                                pass
                        ema_hostnames.append(ema_hostname)
                        ema_states.append(ema_state)
                        ema_bands.append(ema_band)
                        ema_software_versions.append(ema_software_version)

                # Acquire mutex and update values for this system
                self.mutex.acquire()
                system.poll_status = poll_status
                system.csm.hostname = csm_hostname
                system.csm.software_version = csm_software_version
                system.csm.state = csm_state
                system.csm.health = csm_health
                system.csm.location = system_location
                system.csm.system_name = system_name
                system.csm.system_group = system_group
                if system_group and system_group not in self.groups:
                    self.groups.append(system_group)
                if ema_hostnames:
                    for i in range(len(ema_hostnames)):
                        system.emas[i].hostname = ema_hostnames[i]
                        system.emas[i].state = ema_states[i]
                        system.emas[i].band = ema_bands[i]
                        system.emas[i].software_version = ema_software_versions[i]
                self.mutex.release()
                # Sleep for a while before going around the loop and starting next ping
                time.sleep(0.5)

    def stop(self):
        self.quit = True


if __name__ == "__main__":
    # Redirect stderr to stdout so that we see exceptions when running from console but stop
    # py2exe from trying to create an error log file which generates a user dialog when exiting the app
    sys.stderr = sys.stdout
    root = Tk()
    root.option_add('*font', ('verdana', 10))
    systems = []
    groups = []
    mutex = threading.RLock()
    app = App(systems, groups, mutex, root)
    th = SystemPollThread(systems, groups, mutex)
    th.start()
    app.start()
    th.stop()
    th.join()
