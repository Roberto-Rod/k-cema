from tkinter import *
from functools import partial
from tkinter import filedialog
from tkinter import messagebox
import os
import subprocess
import tempfile
import shutil


class App:
    VERSION_MAJOR = 0
    VERSION_MINOR = 1
    VERSION_PATCH = 1

    def __init__(self, master):
        main_frame = Frame(master)
        mission_frame = Frame(main_frame)
        Label(main_frame, text="Select one or more mission files,\nnote that any mission location may be left empty:",
              justify=LEFT).grid(row=0, column=0, sticky="w", padx=0, pady=5)
        self.fields = []
        for slot in range(1, 6):
            Label(mission_frame, text="Mission {}:".format(slot)).grid(row=slot, column=0, padx=0, pady=5)
            entry = Entry(mission_frame, width=80, state="readonly")
            entry.grid(row=slot, column=1, padx=10, pady=5)
            self.fields.append(entry)
            Button(mission_frame, text="...", borderwidth=1, command=partial(self.select_file, slot)). \
                grid(row=slot, column=2, padx=0, pady=5)
            Button(mission_frame, text="X", borderwidth=1, command=partial(self.clear_file, slot)). \
                grid(row=slot, column=3, padx=5, pady=5)
        mission_frame.grid(row=1, column=0, sticky="w", padx=0, pady=5)
        self.button_package = Button(main_frame, text="Package Missions", state="disabled", command=self.package_missions)
        self.button_package.grid(row=2, column=0, padx=0, pady=5)
        main_frame.pack(fill=BOTH, expand=NO, side=TOP, padx=10, pady=10)

    def select_file(self, slot=0):
        file = filedialog.askopenfilename(filetypes=[("Encrypted Mission Files", "*.iff")])
        if file:
            field = self.fields[slot - 1]
            field.config(state="normal")
            field.delete(0, END)
            field.insert(0, file)
            field.config(state="readonly")
            # Now we've added this file there must be at least one file in a slot so enable the package button
            self.button_package.config(state="normal")

    def clear_file(self, slot=0):
        field = self.fields[slot - 1]
        field.config(state="normal")
        field.delete(0, END)
        field.config(state="readonly")
        # If no files are left in any of the slots then disable the package button
        all_empty = True
        for field in self.fields:
            if field.get():
                all_empty = False
        if all_empty:
            self.button_package.config(state="disabled")

    def package_missions(self):
        filepath = filedialog.asksaveasfilename(filetypes=[("Signed Package File", "*.p7s")])
        if filepath:
            file, ext = os.path.splitext(filepath)
            # If the extension is not .p7s then add it to the end of the path. If a different extension
            # has been specified then maintain this and just append .p7s to the end of the file name.
            if ext != ".p7s":
                filepath += ".p7s"
            # Create the temporary directory with the missions in it
            mission_dir = os.path.join(tempfile.gettempdir(), "k-cema_mission_packager")
            # Remove temporary directory if it has been left behind
            shutil.rmtree(mission_dir, ignore_errors=True)
            for slot in range(0, 5):
                dir = os.path.join(mission_dir, "missions", "{}".format(slot + 1))
                os.makedirs(dir)
                src = self.fields[slot].get()
                if src:
                    dst = os.path.join(dir, "mission.iff")
                    try:
                        shutil.copyfile(src, dst)
                    except FileNotFoundError:
                        # A file was not found, abort packaging
                        messagebox.showerror("File Not Found", "ERROR: \"{}\" (Mission {}) not found".format(src, slot))
                        return
            # Launch the external application to package the mission files
            process = subprocess.Popen(["packagedir\packagedir.exe", "any", mission_dir, filepath],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            # Remove the temporary directory
            shutil.rmtree(mission_dir)
            # Display status to user
            if stderr:
                messagebox.showerror("Packaging Failed", "Packaging failed with message:\r\n{}".
                                     format(stderr.decode("utf-8")))
            else:
                messagebox.showinfo("Packaging Complete", "Missions packaged into file: {}".format(filepath))

    def get_title(self):
        return "K-CEMA Mission Packager v{}.{}.{}".format(self.VERSION_MAJOR, self.VERSION_MINOR, self.VERSION_PATCH)


if __name__ == "__main__":
    root = Tk()
    root.option_add('*font', ('verdana', 10))
    root.resizable(False, False)
    display = App(root)
    root.title(display.get_title())
    root.mainloop()
