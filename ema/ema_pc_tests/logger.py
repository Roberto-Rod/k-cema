import sys
import os


class Logger:
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, "wb")

    def write(self, message):
        self.terminal.write(message)
        try:
            # If the backspace-space-backspace command has been sent to erase a character
            # in the terminal then erase the last character from the file
            if message == "\b \b":
                self.log.seek(-1, os.SEEK_END)
                self.log.truncate()
            else:
                self.log.write(message.encode("utf-8"))
        except:
            pass

    def flush(self):
        self.terminal.flush()

    def close_file(self):
        self.log.close()
