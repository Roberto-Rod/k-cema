import ssh

HOSTNAME = 'EMA-010471.local'
USERNAME = 'root'
PASSWORD = 'root'
EMA_GET_TAMPER_FLAGS = "/usr/sbin/i2cget -f -y 0 0x68 0xF"

if __name__ == "__main__":
    print("Connecting to {}".format(HOSTNAME))
    connection = ssh.SSH(HOSTNAME, USERNAME, PASSWORD)
    tamper_flags = str(connection.send_command(EMA_GET_TAMPER_FLAGS).stdout).strip()
    print("Tamper Flags: {}".format(tamper_flags))