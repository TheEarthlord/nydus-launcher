
import os
from nydus.common import validity
from nydus.common.Config import Config

CLIENT_CONFIG_FILE = "/etc/nydus/nydus-client.conf"

SERVERIPADDR = "ServerIpAddr"
PORT = "Port"
CACHAINFILE = "CaChainFile"
CLIENT_PARNAMES = [SERVERIPADDR, PORT, CACHAINFILE]
CLIENT_DEFCONFIG = {
    SERVERIPADDR: "192.168.1.1",
    PORT: "2011",
    CACHAINFILE: "nydus-ca.crt",
}

# Maps between the parameter named used in the config file
# and the attribute name used in the Config class
CLIENT_VARNAMES = {
    SERVERIPADDR: "server_ip",
    PORT: "port",
    CACHAINFILE: "ca_chain",
}

class ClientConfig(Config):

    """
    path: a string, path to the configuration file to read
    """
    def __init__(self, path=CLIENT_CONFIG_FILE, parnames=CLIENT_PARNAMES, defconfig=CLIENT_DEFCONFIG, varnames=CLIENT_VARNAMES):
        super().__init__(path, parnames, defconfig, varnames)
        
    def validate_config(self):
        if not validity.is_valid_ipaddr(self.server_ip):
            raise ValueError("Value for {} is not a valid IP address: {}".format(SERVERIPADDR, self.server_ip))

        if not validity.is_valid_port(self.port):
            raise ValueError("Value for {} is not a valid port: {}".format(PORT, self.port))

        if not validity.is_valid_file(self.ca_chain):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(CACHAINFILE, self.ca_chain))

    def get_server_ip(self):
        return self.server_ip

    def get_port(self):
        return self.port

    def get_ca_chain(self):
        return self.ca_chain
