import os
import json
from nydus.common import validity

MANIFEST_KEY = "manifest"
DESIRED_OS = "linux"


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
# under ~/.minecraft/runtime/<runtime-name> then get rid of it when finished.

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
