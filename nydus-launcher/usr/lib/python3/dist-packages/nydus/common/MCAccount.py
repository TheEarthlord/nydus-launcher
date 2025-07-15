
from nydus.common import validity

class MCAccount:

    def __init__(self, username, uuid, token):
        assert validity.is_valid_minecraft_username(username), "Minecraft username '{}' was invalid".format(username)
        assert validity.is_valid_minecraft_uuid(uuid), "Minecraft uuid '{}' was invalid".format(uuid)
        assert validity.is_valid_minecraft_token(token), "Minecraft token '{}' was invalid".format(token)
        self.username = username
        self.uuid = uuid
        self.token = token

    def get_username(self):
        return self.username

    def get_uuid(self):
        return self.uuid

    def get_token(self):
        return self.token

    def copy(self):
        return MCAccount(self.username, self.uuid, self.token)
