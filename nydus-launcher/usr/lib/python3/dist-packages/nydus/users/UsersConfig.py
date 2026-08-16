
import os
from nydus.common import validity
from nydus.common.Config import Config

# Remember this needs to be the same as the client config file
CLIENT_CONFIG_FILE = "/etc/nydus/nydus-client.conf"

# Because Users reads from the nydus-client configuration file,
# there will be configuration items it doesn't need.
# All the parameter names have to be included in the UsersConfig
# class so it recognises them as valid, but the class
# only includes validation and getter methods for the configuration
# that nydus-users will actually use.

SERVERIPADDR = "ServerIpAddr"
PORT = "Port"
RENEWALPERIOD = "RenewalPeriod"
CACHAINFILE = "CaChainFile"
CLIENT_PARNAMES = [SERVERIPADDR, PORT, RENEWALPERIOD, CACHAINFILE]
CLIENT_DEFCONFIG = {
    SERVERIPADDR: "192.168.1.1",
    PORT: "2011",
    RENEWALPERIOD: "15",
    CACHAINFILE: "nydus-ca.crt",
}

# Maps between the parameter named used in the config file
# and the attribute name used in the Config class
CLIENT_VARNAMES = {
    SERVERIPADDR: "server_ip",
    PORT: "port",
    RENEWALPERIOD: "renewal_period",
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
        # Port needs to be in int form for most uses,
        # but it'll be a string from reading the config
        # file, so we convert it.
        return int(self.port)

    def get_ca_chain(self):
        return self.ca_chain
