
clnch_appname = "CraftLaunch"
clnch_dirname = "CraftLaunch"
clnch_version = "3.33"

_startup_string_fmt = """\
%s version %s:
  http://sites.google.com/site/craftware/
"""

def startupString():
    return _startup_string_fmt % ( clnch_appname, clnch_version )
