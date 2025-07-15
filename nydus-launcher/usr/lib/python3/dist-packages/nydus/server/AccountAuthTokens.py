
from nydus.common import validity
from nydus.server.AccessToken import AccessToken
from nydus.common.MCAccount import MCAccount

# Authenticating an account and preparing it for Minecraft
# launch involves several tokens and other data items.
# This class is for keeping all that data in one place for one
# account.

class AccountAuthTokens:
    
    """
    ms_username: string, Microsoft account username (email address)
    msal_token: AccessToken from auth to MSAL
    xbl_token: AccessToken from auth to Xbox Live
    xsts_token: AccessToken from auth to XSTS
    mc_token: AccessToken from auth to Minecraft
    mc_account: MCAccount containing uuid and username for Minecraft
    """
    def __init__(self, ms_username, msal_token, xbl_token, xsts_token, mc_token, mc_account):
    
        if not validity.is_valid_microsoft_username(ms_username):
            raise ValueError("Must provide valid Microsoft username to AccountAuthTokens. Was given {}".format(ms_username))

        if not isinstance(msal_token, AccessToken):
            raise TypeError("Must provide AccessToken for msal_token. Was given {}".format(type(msal_token)))

        if not validity.is_valid_msal_token(msal_token.get_token()):
            raise ValueError("Must provide a valid msal AccessToken for msal_token. Was given {}".format(msal_token))

        if not isinstance(xbl_token, AccessToken):
            raise TypeError("Must provide AccessToken for xbl_token. Was given {}".format(type(xbl_token)))

        if not validity.is_valid_xboxlive_token(xbl_token.get_token()):
            raise ValueError("Must provide a valid Xbox Live AccessToken for xbl_token. Was given {}".format(xbl_token))

        if not isinstance(xsts_token, AccessToken):
            raise TypeError("Must provide AccessToken for xsts_token. Was given {}".format(type(xsts_token)))

        if not validity.is_valid_xsts_token(xsts_token.get_token()):
            raise ValueError("Must provide a valid XSTS AccessToken for msal_token. Was given {}".format(xsts_token))

        if not isinstance(mc_token, AccessToken):
            raise TypeError("Must provide AccessToken for mc_token. Was given {}".format(type(mc_token)))

        if not validity.is_valid_minecraft_token(mc_token.get_token()):
            raise ValueError("Must provide a valid Minecraft AccessToken for mc_token. Was given {}".format(mc_token))

        if not isinstance(mc_account, MCAccount):
            raise TypeError("Must provide MCAccount for mc_account. Was given {}".format(type(mc_account)))

        self.ms_username = ms_username
        self.msal_token = msal_token
        self.xbl_token = xbl_token
        self.xsts_token = xsts_token
        self.mc_token = mc_token
        self.mc_account = mc_account

    def get_microsoft_username(self):
        return self.ms_username

    def get_msal_token(self):
        return self.msal_token

    def get_xboxlive_token(self):
        return self.xbl_token

    def get_xsts_token(self):
        return self.xsts_token

    def get_minecraft_token(self):
        return self.mc_token

    def get_minecraft_account(self):
        return self.mc_account

    def set_microsoft_username(self, ms_username):
        if not validity.is_valid_microsoft_username(ms_username):
            raise ValueError("AccountAuthTokens.set_microsoft_username must be given a valid Microsoft username. Was given {}".format(ms_username))

        self.ms_username = ms_username

    def set_msal_token(self, msal_token):
        if not isinstance(msal_token, AccessToken):
            raise TypeError("AccountAuthTokens.set_msal_token must be given an AccessToken instance. Was given a {}".format(type(msal_token)))
        self.msal_token = msal_token

    def set_xboxlive_token(self, xbl_token):
        if not isinstance(xbl_token, AccessToken):
            raise TypeError("AccountAuthTokens.set_xboxlive_token must be given an AccessToken instance. Was given a {}".format(type(xbl_token)))
        self.xbl_token = xbl_token

    def set_xsts_token(self, xsts_token):
        if not isinstance(xsts_token, AccessToken):
            raise TypeError("AccountAuthTokens.set_xsts_token must be given an AccessToken instance. Was given a {}".format(type(xsts_token)))
        self.xsts_token = xsts_token

    def set_minecraft_token(self, minecraft_token):
        if not isinstance(minecraft_token, AccessToken):
            raise TypeError("AccountAuthTokens.set_minecraft_token must be given an AccessToken instance. Was given a {}".format(type(minecraft_token)))
        self.mc_token = minecraft_token

    def set_minecraft_account(self, mc_account):
        if not isinstance(mc_account, MCAccount):
            raise TypeError("AccountAuthTokens.set_minecraft_account must be given an MCAccount instance. Was given a {}".format(type(mc_account)))
        self.mc_account = mc_account

    def copy(self):
        return AccountAuthTokens(
            self.ms_username,
            self.msal_token.copy(),
            self.xbl_token.copy(),
            self.xsts_token.copy(),
            self.mc_token.copy(),
            self.mc_account.copy()
        )
