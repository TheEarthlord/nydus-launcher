
import os
from nydus.common import validity
from nydus.common.Config import Config

SERVER_CONFIG_FILE = "/etc/nydus/nydus-server.conf"

IPADDR = "IpAddr"
PORT = "Port"
CERTFILE = "CertFile"
CERTPRIVKEY = "CertPrivKey"
MCVERSION = "McVersion"
MSALCID = "MSALClientId"
ALLOCFILE = "AllocFile"
ACCOUNTSFILE = "AccountsFile"
SERVER_PARNAMES = [
    IPADDR, 
    PORT,
    CERTFILE,
    CERTPRIVKEY,
    MCVERSION,
    MSALCID,
    ALLOCFILE,
    ACCOUNTSFILE,
]

SERVER_DEFCONFIG = {
    IPADDR: "192.168.1.1",
    PORT: "2011",
    CERTFILE: "/etc/nydus/nydus-server.crt",
    CERTPRIVKEY: "/etc/nydus/nydus-server.key",
    MCVERSION: "1.20.6",
    MSALCID: "1ab23456-7890-1c2d-e3fg-45h6789ijk01",
    ALLOCFILE: "/etc/nydus/nydus-alloc.csv",
    ACCOUNTSFILE: "/etc/nydus/ms-usernames.txt",
}

# Maps between the parameter name used in the config file
# and the attribute name used in the Config class
SERVER_VARNAMES = {
    IPADDR: "ip_addr",
    PORT: "port",
    CERTFILE: "cert_file",
    CERTPRIVKEY: "cert_privkey",
    MCVERSION: "mc_version",
    MSALCID: "msal_cid",
    ALLOCFILE: "alloc_file",
    ACCOUNTSFILE: "accounts_file",
}

class ServerConfig(Config):

    def __init__(self, path=SERVER_CONFIG_FILE, parnames=SERVER_PARNAMES, defconfig=SERVER_DEFCONFIG, varnames=SERVER_VARNAMES):
        super().__init__(path, parnames, defconfig, varnames)

    def validate_config(self):
        if not validity.is_valid_ipaddr(self.ip_addr):
            raise ValueError("Value for {} is not a valid IP address: {}".format(IPADDR, self.ip_addr))

        if not validity.is_valid_port(self.port):
            raise ValueError("Value for {} is not a valid port: {}".format(PORT, self.port))

        if not validity.is_valid_file(self.cert_file):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(CERTFILE, self.cert_file))

        if not validity.is_valid_file(self.cert_privkey):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(CERTPRIVKEY, self.cert_privkey))

        if not validity.is_valid_minecraft_version(self.mc_version):
            raise ValueError("Value for {} is not a valid Minecraft version: {}".format(MCVERSION, self.mc_version))

        if not validity.is_valid_msal_cid(self.msal_cid):
            raise ValueError("Value for {} is not a valid MSAL Client ID: {}".format(MSALCID, self.msal_cid))

        if not validity.is_valid_file(self.alloc_file):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(ALLOCFILE, self.alloc_file))

        if not validity.is_valid_file(self.accounts_file):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(ACCOUNTSFILE, self.accounts_file))

    def get_ip_addr(self):
        return self.ip_addr

    def get_port(self):
        return self.port

    def get_cert_file(self):
        return self.cert_file

    def get_cert_privkey(self):
        return self.cert_privkey

    def get_mc_version(self):
        return self.mc_version

    def get_msal_cid(self):
        return self.msal_cid

    def get_alloc_file(self):
        return self.alloc_file

    def get_accounts_file(self):
        return self.accounts_file
