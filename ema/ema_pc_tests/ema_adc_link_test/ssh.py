from fabric import *


class SSH:
    COMMAND_TIMEOUT_S = 15
    COMMAND_RETRIES = 4
    FILE_SEND_RETRIES = 3
    PASSWORDS = ["gbL^58TJc", "root"]

    client = None

    def __init__(self, address, password_dict={}, username="root"):
        self.address = address
        self.username = username
        self.password_dict = password_dict
        self.connect()

    def connect(self):
        attempt = 0
        passwords = []
        if self.address in self.password_dict.keys():
            # Try the existing password if it is in the dictionary
            passwords.append(self.password_dict[self.address])
        passwords.extend(self.PASSWORDS)
        for password in passwords:
            attempt += 1
            self.client = Connection(host=self.address, user=self.username, port=22,
                                     connect_kwargs={"password": password})
            try:
                self.client.create_session()
                print("Connected to {}".format(self.address))
                self.password_dict[self.address] = password
                return True
            except:
                self.client.close()
                print("ERROR: connection attempt to {} using password {} failed".format(self.address, attempt))
        return False

    def send_command(self, command, timeout=COMMAND_TIMEOUT_S):
        reconnect = False
        for i in range(self.COMMAND_RETRIES):
            if reconnect:
                self.client.close()
                del self.client
                self.connect()
            # Check if connection still exists
            if self.client.is_connected:
                try:
                    return self.client.run(command, warn=True, timeout=timeout)
                except Exception as e:  # CommandTimedOut
                    print(e)
                    print("WARNING: command timed out, reconnecting...")
                    reconnect = True
            else:
                reconnect = True
        print("ERROR: could not execute command (connection not opened)")
        return ""

    def send_file(self, local, remote):
        reconnect = False
        for i in range(self.FILE_SEND_RETRIES):
            if reconnect:
                self.client.close()
                del self.client
                self.connect()
            # Check if connection still exists
            if self.client.is_connected:
                try:
                    return self.client.put(local, remote)
                except Exception as e:
                    print(e)
                    print("WARNING: file send timed out, reconnecting...")
                    reconnect = True
            else:
                reconnect = True
            print("ERROR: could not send file (connection not opened)")
        return ""

    def get_file(self, remote, local):
        # Check if connection still exists
        output = ""
        if self.client.is_connected:
            output = self.client.get(remote, local)
        else:
            print("ERROR: could not execute command (connection not opened)")
        return output

    def is_connected(self):
        return self.client.is_connected
