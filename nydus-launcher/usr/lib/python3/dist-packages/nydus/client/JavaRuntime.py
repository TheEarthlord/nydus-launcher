import os
import json
from json.decoder import JSONDecodeError
from nydus.common import validity
from nydus.client.DownloadFile import DownloadFile

MANIFEST_KEY = "manifest"
DESIRED_OS = "linux"
SHA1_KEY = "sha1"
URL_KEY = "url"

# Class for downloading Java runtimes to use in
# launching Minecraft.

# The json at ~/.minecraft/versions/jre_manifest.json
# contains the key "manifest". The corresponding dictionary
# has keys for different operating systems (we want "linux")
# and under those information for different java runtimes
# used by Minecraft. The file download information there
# only gives you that specific runtime's manifest file,
# a json file which tells you all the other materials
# you need for that particular java runtime and where to
# download them from.
# Runtimes are placed at
# ~/.minecraft/runtime/<runtime-name>/<os-name>/<runtime-name>/<path-from-manifest>
# The runtime manifest file doesn't seem to be stored anywhere
# under ~/.minecraft. So we'll probably put it in the directory
# under ~/.minecraft/runtime/<runtime-name>/<os-name> then get rid of it when finished.

# Which Java runtime you need for a specific Minecraft version is
# in that version's json file under javaVersion -> component.
# That's handled by MCVersion.

class JavaRuntime:

    """
    Accepts a Java runtime name.
    """
    def __init__(self, runtime):

        if not validity.is_valid_java_runtime(runtime):
            raise ValueError("Must provide valid Java Runtime name to JavaRuntime constructor. Was given {}".format(runtime))
        
        self.name = runtime
        self.game_dir = utils.get_minecraft_path()
        self.runtime_dir = self.get_runtime_dir()

    """
    Returns a string: the path to the jre manifest file
    which tells us how to download the manifests for
    different java runtimes.
    Usually of the form
    /home/<username>/.minecraft/versions/jre_manifest.json
    """
    def get_jre_manifest(self):
        return os.path.join(self.game_dir, "versions", "jre_manifest.json")

    """
    Returns a boolean. True if the jre manifest file exists; False if it
    doesn't.
    """
    def jre_manifest_exists(self):
        return validity.is_valid_file(self.get_jre_manifest())

    """
    Returns the location where all runtimes go.
    This is usually /home/<username>/.minecraft/runtime
    """
    def get_base_runtime_dir(self):
        return os.path.join(self.game_dir, "runtime")

    """
    Returns the directory where the data and files for the runtime
    represented by this specific instance of the JavaRuntime class will go.
    This is the root directory for everything the runtime's manifest tells
    you to download.
    Usually of the form
    /home/<username>/.minecraft/runtime/<runtime-name>/<os-name>/<runtime-name>
    """
    def get_runtime_dir(self):
        return os.path.join(self.get_base_runtime_dir(), self.name, DESIRED_OS, self.name)

    """
    Returns a path of the form
    /home/<username>/.minecraft/runtime/<runtime-name>/<os-name>/<runtime-name>.json
    This is where we'll put the runtime's manifest file while downloading everything.
    We'll delete it when finished.
    This path is totally custom to the Nydus Launcher; the Minecraft launcher seems
    not to save the runtime manifest anywhere as a file.
    """
    def get_runtime_manifest_path(self):
        return os.path.join(self.get_base_runtime_dir(), self.name, DESIRED_OS, "{}.json".format(self.name))

    """
    Returns a DownloadFile containing the information to download
    the manifest for the current java runtime.
    Information is taken from jre_manifest.json.
    The path to which the file should be downloaded will be set as
    ~/.minecraft/runtime/<runtime-name>
    because it isn't normally cached, so there's no correct place
    to put it.
    Returns None if the desired runtime can't be found.
    """
    def get_runtime_manifest(self):
        jre_fname = self.get_jre_manifest()
        with open(jre_fname, "r") as f:
            try:
                jre_json = json.load(f)
            except JSONDecodeError as e:
                raise ValueError("Failed to parse json in {} at line {} col {} char {}"\
                    .format(jre_fname, e.lineno, e.colno, e.pos))

        jre_content = jre_json.get(MANIFEST_KEY)
        if jre_content == None:
            raise KeyError("Jre manifest file {} contained no key {}; could not get manifest for runtime {}".format(jre_fname, MANIFEST_KEY, self.name))
        if not isinstance(jre_content, dict):
            raise TypeError("Contents of key {} in file {} was not a dict; could not get manifest for runtime {}".format(MANIFEST_KEY, jre_fname, self.name))

        os_runtimes = jre_content.get(DESIRED_OS)

        if os_runtimes == None:
            raise KeyError("Jre manifest file {} contained no runtimes for desired OS '{}'; could not get manifest for runtime {}".format(jre_fname, DESIRED_OS, self.name))

        if not isinstance(os_runtimes, dict):
            raise TypeError("Contents of desired OS key '{}' in file {} was not a dict; could not get manifest for runtime {}".format(DESIRED_OS, jre_fname, self.name))

        runtime_data = os_runtimes.get(self.name)

        if runtime_data == None:
            raise KeyError("Jre manifest file {} contained no runtime named '{}' for desired OS '{}'; could not proceed.".format(jre_fname, self.name, DESIRED_OS))

        if not isinstance(runtime_data, dict):
            raise TypeError("Contents of key '{}' for OS '{}' in file {} was not a dict; could not get runtime information.".format(self.name, DESIRED_OS, jre_fname))

        runtime_manifest = runtime_data.get(MANIFEST_KEY)

        if runtime_manifest == None:
            raise KeyError("Jre manifest file {} contained no key {} under {}; could not get manifest for runtime {}".format(jre_fname, MANIFEST_KEY, self.name, self.name))
        if not isinstance(runtime_manifest, dict):
            raise TypeError("Contents of key {} under {} in file {} was not a dict; could not get manifest for runtime {}".format(MANIFEST_KEY, self.name, jre_fname, self.name))

        sha1 = runtime_manifest.get(SHA1_KEY)
        url = runtime_manifest.get(URL_KEY)
        if url == None or sha1 == None:
            return

        fpath = self.get_runtime_manifest_path()
        fname = os.path.basename(fpath)
        path = os.path.dirname(fpath)
        
        df = DownloadFile(url, sha1, name=fname, path=path)
        return df
