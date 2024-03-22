#!/usr/bin/env python3

from tkinter import END


class TextUpdate:
    def __init__(self, text, master):
        self.text = text
        self.master = master

    def insert(self, message):
        self.text.insert(END, "{}\n".format(message))
        self.text.see(END)
        self.master.update()
