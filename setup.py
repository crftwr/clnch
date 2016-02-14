import sys
import os
import fnmatch

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], ".." ),
    ]
 
import clnch_resource

from cx_Freeze import setup, Executable

executable = Executable( 
    script = "clnch_main.py",
    icon = "app.ico",
    base = "Win32GUI",
    targetName = "clnch.exe"
    )

options = {
    "build" : {
        "build_exe" : "dist/clnch",
    },

    "build_exe": {
        "optimize" : 2,
        
        "excludes" : [
            "tkinter",
            ],
        
        "includes" : [
            "clnch"
            ],
        
        "packages" : [
        ],
        "compressed" : 1,
        #"copy_dependent_files" : 1,
        #"create_shared_zip" : 1,
        #"append_script_to_exe" : 1,
        "include_files": [ 
            "dict",
            "extension",
            "license",
            "theme",
            "readme.txt",
            "migemo.dll",
            "_config.py",
            ( "doc/html", "doc" ),
            ],
        #"include_msvcr" : 1,
    },
}

setup( 
    name = "clnch",
    version = clnch_resource.clnch_version,
    description = "",
    executables = [executable],
    options = options,
    )

def fixup():
    
    exe_dirname = options["build"]["build_exe"]
    lib_dirname = os.path.join( exe_dirname, "lib" )
    
    if not os.path.exists(lib_dirname):
        os.mkdir(lib_dirname)
    
    for name in os.listdir(exe_dirname):
        if ( fnmatch.fnmatch(name,"*.dll") or fnmatch.fnmatch(name,"*.pyd") ) and not name=="python35.dll":
            old_path = os.path.join( exe_dirname, name )
            new_path = os.path.join( lib_dirname, name )

            print( "moving %s -> %s" % (old_path,new_path) )

            if os.path.exists(new_path):
                os.unlink(new_path)
            os.rename( old_path, new_path )

fixup()



























"""






import sys
import os

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    ]

from distutils.core import setup
import py2exe

import clnch_resource

py2exe_options = {
    "compressed": 1,
    "optimize": 2,
    "bundle_files": 3,

    "packages": [
        'clnch',
    ],

    "excludes": [
        'readline',
        "Tkconstants","Tkinter","tcl"
    ],

    "dll_excludes": [
        "MSVCP90.dll",
    ],
}

setup(
    options = { "py2exe" : py2exe_options },
    windows = [ {
                    "script" : "clnch_main.py",
                    "dest_base" : "clnch",
                    "icon_resources": [(1,"app.ico")],

                    # バージョン情報
                    "name" : "CraftLaunch",
                    "version" : clnch_resource.clnch_version,
                    "description" : "",
                    "company_name" : "craftware",
                    "url" : "http://sites.google.com/site/craftware/",
                }
              ],
    zipfile = "lib/library.zip"
)


"""
