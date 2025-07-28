
from nydus.client.JSONVersion import JSONVersion
from nydus.common import validity
from nydus.common.MCAccount import MCAccount

"""
Class which sets up and launches Minecraft.
Uses JSONVersion for most of the work of processing a specific
version's json file, then downloading the materials and forming
the launch command.
This class uses those tools to read ancestors for any inheritance
relation, and actually creates the new Minecraft subprocess.
"""
class MCLauncher:

    """
    version: string, a Minecraft version
    mc_account: MCAccount instance, containing the auth information
        which will later be used to launch Minecraft.
    """
    def __init__(self, version, mc_account):

        if not validity.is_valid_minecraft_version(version):
            raise ValueError("MCLauncher was given invalid Minecraft version {}".format(version))

        if not isinstance(mc_account, MCAccount):
            raise TypeError("MCLauncher expected an instance of MCAccount but was instead given {}".format(type(mc_account)))

        self.version = version
        self.mc_account = mc_account

        # This list will hold the JSONVersion instances for this Minecraft
        # version and any ancestors it inherits from.
        # Index 0 will be the target version's JSONVersion instance,
        # index 1 the version the target inherits from,
        # index 2 the version that inherits from, and so on.
        self.versions_list = []

        self.load_versions()

    def get_target_json_version(self):
        return self.versions_list[0]

    def get_mc_account(self):
        return self.mc_account.copy()

    def load_versions(self):

        current_version = self.version

        # Loop through ancestors until there are no more
        while current_version:
            jv = JSONVersion.from_version(current_version)
            self.versions_list.append(jv)
            current_version = jv.get_inherits_from()

        # Now manually perform the data inheritance so our target
        # version is fully filled out.
        # Iterate backwards so we start at the furthest ancestor,
        # bring its data into its immediate child, and so on,
        # until the flow of data reaches the target version.
        for i in range(len(self.versions_list) - 2, -1, -1):
            child = self.versions_list[i]
            parent = self.versions_list[i+1]
            child.inherit_from(parent)

    def download_all(self):
        # We only need to download all the files referenced by
        # the target version, since data from its ancestors has
        # already been inherited by it.
        self.get_target_json_version().download_all()

    def launch(self):

        command = self.get_target_json_version().make_launch_command(self.mc_account)

        # We want to run from inside the minecraft dir, which is self.game_dir
        # so that logs end up in there, not dumped in random spots on the filesystem
        subprocess.run(command, cwd=utils.get_minecraft_path())

        # subprocess.run should block until the process finishes. So we'll return when
        # Minecraft is closed and we're ready to release the account.
