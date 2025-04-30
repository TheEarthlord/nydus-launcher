
import os
from nydus.common import validity

class Config:

    """
    path: a string, path to the configuration file to read
    parnames: a list. Each element in the list should be a string and the
        name of a configuration parameter which may appear in the configuration file.
    defconfig: a dictionary. The keys of the dictionary should be the elements
        of the parnames list, and the corresponding values the defaults for those
        configuration parameters.
    varnames: a dictionary. The keys of the dictionary should be the elements
        of the parnames list, and the corresponding values are the attribute names
        of the config class under which that configuration parameter's value will
        be stored.
    """
    def __init__(self, path, parnames, defconfig, varnames):
        
        if not validity.is_valid_file(path):
            raise ValueError("Configuration file could not be found or could not be read. Was {}".format(path))

        if not validity.is_valid_parnames(parnames):
            raise ValueError("Given parameter name list was invalid. It must be a list of strings containing no whitespace or equals signs. The object given was {}".format(parnames))

        if not validity.is_valid_defconfig(defconfig):
            raise ValueError("Given parameter defaults dictionary was invalid. It must be a dictionary with config parameters as keys and their defaults as values. The object given was {}".format(defconfig))

        if not validity.is_valid_varnames(varnames):
            raise ValueError("Given variable names dictionary was invalid. It must be a dictionary with config parameters as keys and class attribute names as values. The object given was {}".format(varnames))

        if set(parnames) != set(defconfig.keys()):
            raise ValueError("Keys of defconfig were not identical to contents of parnames. Parnames: {}. Defconfig keys: {}.".format(parnames, defconfig.keys()))

        if set(parnames) != set(varnames.keys()):
            raise ValueError("Keys of varnames were not identical to contents of parnames. Parnames: {}. Defconfig keys: {}.".format(parnames, varnames.keys()))

        self.parnames = parnames
        self.varnames = varnames

        for parname in self.parnames:
            setattr(self, self.varnames[parname], defconfig[parname])

        self.path = path
        self.read_config_file()
        self.validate_config()


    def read_config_file(self):

        # There may be exceptions trying to open the file
        # such as permission denied, or if it's been moved
        # since we checked for it (unlikely).
        # I don't want to except Exception but it would
        # be good to give more useful error messages than
        # python's defaults.
        with open(self.path, "r") as f:
            nline = 1
            for line in f:
                line = line.strip()

                # Empty line or comment
                if line == "" or line.startswith("#"):
                    continue
                
                # Look for the parameter name

                found_param = False
                for pname in self.parnames:
                    if line.startswith(pname):
                        rest = line[len(pname):]
                        rest = rest.strip()
                        if rest.startswith("="):
                            value = rest[1:]
                            value = value.strip()
                            setattr(self, self.varnames[pname], value)
                            found_param = True
                            break
                        else:
                            raise ValueError("Could not find value on line {} of configuration file. Parameter name {} appeared with no equals sign. Rest of line was '{}'".format(nline, pname, rest))

                if not found_param:
                    raise ValueError("Unknown parameter on line {} of configuration file. Line was '{}'".format(nline, line))

                nline += 1

