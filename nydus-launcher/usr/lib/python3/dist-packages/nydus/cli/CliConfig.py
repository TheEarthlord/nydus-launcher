
import os
from nydus.common import validity
from nydus.common.Config import Config

# Remember this needs to be the same as the server config file
CLI_CONFIG_FILE = "/etc/nydus/nydus-server.conf"

# Because Cli reads from the nydus-server configuration file,
# there will be configuration items it doesn't need.
# All the parameter names have to be included in the CliConfig
# class so it recognises them as valid, but the class
# only includes validation and getter methods for configuration
# that nydus-cli will actually use.

IPADDR = "IpAddr"
PORT = "Port"
CERTFILE = "CertFile"
CERTPRIVKEY = "CertPrivKey"
MCVERSION = "McVersion"
BROWSERUID = "BrowserUid"
MSALCID = "MSALClientId"
ALLOCFILE = "AllocFile"
ACCOUNTSFILE = "AccountsFile"

CLI_PARNAMES = [
    IPADDR, 
    PORT,
    CERTFILE,
    CERTPRIVKEY,
    MCVERSION,
    BROWSERUID,
    MSALCID,
    ALLOCFILE,
    ACCOUNTSFILE,
]

CLI_DEFCONFIG = {
    IPADDR: "192.168.1.1",
    PORT: "2011",
    CERTFILE: "/etc/nydus/nydus-server.crt",
    CERTPRIVKEY: "/etc/nydus/nydus-server.key",
    MCVERSION: "1.20.6",
    BROWSERUID: "1000",
    MSALCID: "1ab23456-7890-1c2d-e3fg-45h6789ijk01",
    ALLOCFILE: "/etc/nydus/nydus-alloc.csv",
    ACCOUNTSFILE: "/etc/nydus/ms-usernames.txt",
}

CLI_VARNAMES = {
    IPADDR: "ip_addr",
    PORT: "port",
    CERTFILE: "cert_file",
    CERTPRIVKEY: "cert_privkey",
    MCVERSION: "mc_version",
    BROWSERUID: "browser_uid",
    MSALCID: "msal_cid",
    ALLOCFILE: "alloc_file",
    ACCOUNTSFILE: "accounts_file",
}

class CliConfig(Config):

    def __init__(self, path=CLI_CONFIG_FILE, parnames=CLI_PARNAMES, defconfig=CLI_DEFCONFIG, varnames=CLI_VARNAMES):
        super().__init__(path, parnames, defconfig, varnames)

    def validate_config(self):
        if not validity.is_valid_system_uid(self.browser_uid):
            raise ValueError("Value for {} is not a valid system user ID number: {}".format(BROWSERUID, self.browser_uid))

        if not validity.is_valid_msal_cid(self.msal_cid):
            raise ValueError("Value for {} is not a valid MSAL Client ID: {}".format(MSALCID, self.msal_cid))

        if not validity.is_valid_file(self.alloc_file):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(ALLOCFILE, self.alloc_file))

        if not validity.is_valid_file(self.accounts_file):
            raise ValueError("Value for {} is not a file, cannot be found, or cannot be read: {}".format(ACCOUNTSFILE, self.accounts_file))

    def get_browser_uid(self):
        return self.browser_uid

    def get_msal_cid(self):
        return self.msal_cid

    def get_alloc_file(self):
        return self.alloc_file

    def get_accounts_file(self):
        return self.accounts_file
