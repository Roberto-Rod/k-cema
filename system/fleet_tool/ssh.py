from fabric import *


class SSH:
    COMMAND_TIMEOUT_S = 5
    COMMAND_ATTEMPTS = 1

    client = None

    def __init__(self, address, username="root", password="root"):
        self.address = address
        self.username = username
        self.password = password
        self.connect()

    def connect(self):
        self.client = Connection(host=self.address, user=self.username, port=22,
                                 connect_kwargs={"password": self.password})
        try:
            self.client.run("", warn=True, timeout=self.COMMAND_TIMEOUT_S)
        except Exception as e:
            print("ERROR: could not connect to {} - {}".format(self.address, e))

    def send_command(self, command):
        reconnect = False
        for i in range(self.COMMAND_ATTEMPTS):
            if reconnect:
                print("Reconnecting...")
                self.client.close()
                del self.client
                self.connect()
            # Check if connection still exists
            if self.client.is_connected:
                try:
                    return self.client.run(command, warn=True, timeout=self.COMMAND_TIMEOUT_S)
                except Exception as e:  # CommandTimedOut
                    print("WARNING: {}".format(e))
                    reconnect = True
            else:
                reconnect = True
        print("ERROR: could not execute command (connection not opened)")
        return ""

    def send_file(self, local, remote):
        output = ""
        # Check if connection still exists
        if self.client.is_connected:
            try:
                output = self.client.put(local, remote)
            except ConnectionResetError as e:
                print("ERROR: {}".format(e))
        else:
            print("ERROR: could not send file (connection not opened)")
        return output

    def get_file(self, remote, local):
        output = ""
        # Check if connection still exists
        if self.client.is_connected:
            try:
                output = self.client.get(remote, local)
            except ConnectionResetError as e:
                print("ERROR: {}".format(e))
        else:
            print("ERROR: could not get file (connection not opened)")
        return output

    def is_connected(self):
        return self.client.is_connected
