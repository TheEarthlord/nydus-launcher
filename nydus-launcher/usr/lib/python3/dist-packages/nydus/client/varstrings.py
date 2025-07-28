
# Functions for dealing with strings that contain
# variables; e.g. ${varname}

VARNAME_START = "${"
VARNAME_END = "}"

# These are the variables in the version JSON which we will
# remove, along with their invoking arguments, if they appear
# at all. We don't know how to get their actual values and
# they don't seem necessary.

# Twopart variables come with a preceeding argument that names
# the information, and a succeeding argument that uses the variable
# name. e.g.
# "--clientId", "${clientid}"
# Both the arg containing the varname and the preceeding one
# need to be deleted from the list.

CLIENTID_VAR = "clientid"
XUID_VAR = "xuid"

IGNORED_TWOPART_VARIABLES = [
    CLIENTID_VAR,
    XUID_VAR,
]

IGNORED_ONEPART_VARIABLES = []


"""
Returns True if name is a string and a variable for the JSON version
purposes (i.e. starts with '${', ends with '}', and has something in
between)
"""
def is_variable(name):
    if not isinstance(name, str):
        return False
    if name.startswith(VARNAME_START):
        if name.endswith(VARNAME_END):
            nstart = len(VARNAME_START)
            nend = len(name) - len(VARNAME_END)
            middle = name[nstart:nend]
            middle = middle.strip()
            if middle:
                return True
    return False

"""
Returns True if arg is a string of the form
"name=variable"
where variable begin with VARNAME_START and end with VARNAME_END
as in is_variable.
Note that strings which make is_variable True will make this function False;
this function requires something in front of the variable.
"""
def contains_variable(arg):
    if not isinstance(arg, str):
        return False
    nstart = arg.find(VARNAME_START)
    if nstart < 0:
        return False
    nend = arg.find(VARNAME_END)
    if nend < 0:
        return False

    # Start must be before end
    if nend <= nstart:
        return False

    if nstart > 0 and nend > nstart:
        if arg[nstart - 1] == "=":

            # Everything before the equals
            prepart = arg[:nstart - 1]

            # Changing nstart to the index after the end
            # the VARSTART, rather than the index of the
            # beginning
            nstart += len(VARSTART)
            middle = arg[nstart:nend]
            
            # We want the variable name and part before
            # the variable to be nonempty
            if prepart.strip() and middle.strip():
                return True
    return False
    
"""
If arg is a string which is a variable or contains a variable
(according to is_variable and contains_variable), then get
the name of that variable (the part between VARNAME_START and
VARNAME_END) and return it. Else, return empty string.
"""
def get_varname(arg):

    if is_variable(arg) or contains_variable(arg):
        nstart = arg.find(VARNAME_START) + len(VARNAME_START)
        nend = arg.find(VARNAME_END)
        middle = arg[nstart:nend]
        return middle
        
    return ""

"""
arg: string, an argument containing a variable or which is a variable
    according to is_variable or contains_variable
newval: string, a value which will be placed where the variable was in
    the argument, including removal of VARSTART and VAREND
Returns the arg with newval placed where the variable was.
If no variable can be found or newval is not a string, return empty string.
"""
def replace_varname(arg, newval):
    if not isinstance(newval, str):
        return ""

    if is_variable(arg) or contains_variable(arg):
        nstart = arg.find(VARNAME_START)
        nend = arg.find(VARNAME_END) + len(VARNAME_END)
        first_part = arg[:nstart]
        last_part = arg[nend:]
        result = first_part + newval + last_part
        return result

    return ""

"""
varlist: any list of variables (all elements should be strings)
There are some variables which we don't expand because for one reason or another we don't
know how to get values for them. This method deletes all such variables from our instance
data.
Returns nothing; the list is modified in-place.
"""
def remove_ignored_variables_from_list(varlist):

    if not isinstance(varlist, list):
        raise TypeError("remove_ignored_variables_from_list expects a list as input; got {}".format(type(varlist)))
    
    # We iterate backwards because that makes it much easier to deal with
    # ignored variables that have a preceeding argument attached

    idx = len(varlist) - 1

    while idx >= 0:
        arg = varlist[idx]

        if varstrings.is_variable(arg) or varstrings.contains_variable(arg):
            varname = varstrings.get_varname(arg)

            if varname in varstrings.IGNORED_ONEPART_VARIABLES:
                varlist.pop(idx)
            elif varname in varstrings.IGNORED_TWOPART_VARIABLES:
                if idx < 1:
                    raise IndexError("Tried to delete ignored twopart variable {} from list {} but there is no arg in front of it to delete".format(varname, varlist))
                varlist.pop(idx)
                varlist.pop(idx - 1)
                # Reduce idx an extra time so we skip both the places where we
                # deleted an argument
                idx -= 1
        idx -= 1

"""
arglist: list of strings, possibly including some variables in those arg strings
funcdict: dictionary. Keys are variable names (string), values are function/method
    pointers which require no arguments and when called return the current value of
    the corresponding variable (as a string).
This function accepts a list of strings which may contain variable names, and a
dictionary defining how to get each variable's value. It replaces all variable
instances in the list with their values.
Returns nothing. The list is modified in-place.
"""
def replace_variables_in_list(arglist, funcdict):

    if not isinstance(arglist, list):
        raise TypeError("Expected a list of args as first argument to replace_variables_in_list. Instead, got {}".format(type(arglist)))

    if not isinstance(funcdict, dict):
        raise TypeError("Expected a dictionary of varname: varfunction pairs as second argument to replace_variables_in_list. Instead, got {}".format(type(funcdict)))

    for idx in range(len(arglist)):
        arg = arglist[idx]
        if is_variable(arg) or contains_variable(arg):
            varname = get_varname(arg)
            varfunc = funcdict.get(varname)
            if not varfunc:
                raise ValueError("Found variable name {} in argument {} but there was no function to compute the variable's true value".format(varname, arg))

            value = varfunc()

            newarg = replace_varname(arg, value)
            arglist[idx] = newarg

