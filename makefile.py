import os
import sys
import getopt
import shutil
import zipfile
import hashlib
import subprocess
import py_compile

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    ]

import clnch_resource

#-------------------------------------------

action = "all"

debug = False

option_list, args = getopt.getopt( sys.argv[1:], "d" )
for option in option_list:
    if option[0]=="-d":
        debug = True

if len(args)>0:
    action = args[0]

#-------------------------------------------

PYTHON_DIR = "c:/Python35"

PYTHON = PYTHON_DIR + "/python.exe"

DOXYGEN_DIR = "c:/Program Files/doxygen"

DIST_DIR = "dist/clnch"
VERSION = clnch_resource.clnch_version.replace(".","")
ARCHIVE_NAME = "clnch_%s.zip" % VERSION

DIST_FILES = {
    "clnch.exe" :           "clnch/clnch.exe",
    "lib" :                 "clnch/lib",
    "python35.dll" :        "clnch/python35.dll",
    "_config.py" :          "clnch/_config.py",
    "readme.txt" :          "clnch/readme.txt",
    "theme/black" :         "clnch/theme/black",
    "theme/white" :         "clnch/theme/white",
    "license" :             "clnch/license",
    "doc/html" :            "clnch/doc",
    "library.zip" :         "clnch/library.zip",
    "dict/.keepme" :        "clnch/dict/.keepme",
    "extension/.keepme" :   "clnch/extension/.keepme",
    }

#-------------------------------------------

def unlink(filename):
    try:
        os.unlink(filename)
    except OSError:
        pass

def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError:
        pass

def rmtree(dirname):
    try:
        shutil.rmtree(dirname)
    except OSError:
        pass

def compilePythonRecursively( src, dst, file_black_list=[], directory_black_list=[] ):

    for root, dirs, files in os.walk( src ):

        for directory_to_remove in directory_black_list:
            if directory_to_remove in dirs:
                dirs.remove(directory_to_remove)

        for file_to_remove in file_black_list:
            if file_to_remove in files:
                files.remove(file_to_remove)

        for filename in files:
            if filename.endswith(".py"):
                src_filename = os.path.join(root,filename)
                dst_filename = os.path.join(dst+root[len(src):],filename+"c")
                print("compile", src_filename, dst_filename )
                py_compile.compile( src_filename, dst_filename, optimize=2 )


def createZip( zip_filename, items ):
    z = zipfile.ZipFile( zip_filename, "w", zipfile.ZIP_DEFLATED, True )
    for item in items:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                for f in files:
                    f = os.path.normpath(os.path.join(root,f))
                    print( f )
                    z.write(f)
        else:
            print( item )
            z.write(item)
    z.close()


#-------------------------------------------

def target_all():

    target_compile()
    target_copy()
    target_document()
    target_dist()
    target_archive()


def target_compile():

    # compile python source files
    compilePythonRecursively( "c:/Python35/Lib", "build/Lib", 
        directory_black_list = [
            "site-packages",
            "test",
            "tests",
            "idlelib",
            ]
        )
    compilePythonRecursively( "c:/Python35/Lib/site-packages/PIL", "build/Lib/PIL" )
    compilePythonRecursively( "../ckit", "build/Lib/ckit" )
    compilePythonRecursively( "../pyauto", "build/Lib/pyauto" )
    compilePythonRecursively( ".", "build/Lib", 
        file_black_list = [
            "makefile.py",
            "_config.py",
            "config.py",
            ]
        )

    # archive python compiled files
    os.chdir("build/Lib")
    createZip( "../../library.zip", "." )
    os.chdir("../..")


def target_copy():

    rmtree("lib")

    shutil.copy( "c:/Python35/python35.dll", "python35.dll" )

    shutil.copytree( "c:/Python35/DLLs", "lib", 
        ignore=shutil.ignore_patterns(
            "tcl*.*",
            "tk*.*",
            "_tk*.*",
            "*.pdb",
            "*_d.pyd",
            "*_d.dll",
            "*_test.pyd",
            "_test*.pyd",
            "*.ico",
            "*.lib"
            )
        )

    shutil.copy( "c:/Python35/Lib/site-packages/PIL/_imaging.cp35-win32.pyd", "lib/_imaging.pyd" )

    shutil.copy( "../ckit/ckitcore.pyd", "lib/ckitcore.pyd" )
    shutil.copy( "../pyauto/pyautocore.pyd", "lib/pyautocore.pyd" )
    shutil.copy( "clnch_native.pyd", "lib/clnch_native.pyd" )
    shutil.copy( "migemo.dll", "lib/migemo.dll" )


def target_document():
    rmtree( "doc/html" )
    makedirs( "doc/obj" )
    makedirs( "doc/html" )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/index.txt", "doc/obj/index.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/index.txt", "doc/obj/index.htm_" ] )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/changes.txt", "doc/obj/changes.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/changes.txt", "doc/obj/changes.htm_" ] )

    subprocess.call( [ DOXYGEN_DIR + "/bin/doxygen.exe", "doc/doxyfile" ] )
    shutil.copytree( "doc/image", "doc/html/image", ignore=shutil.ignore_patterns("*.pdn",) )


def target_dist():
    
    rmtree("dist/clnch")

    src_root = "."
    dst_root = "./dist"
    
    for src, dst in DIST_FILES.items():

        src = os.path.join(src_root,src)
        dst = os.path.join(dst_root,dst)

        print( "copy : %s -> %s" % (src,dst) )
            
        if os.path.isdir(src):
            shutil.copytree( src, dst )
        else:
            makedirs( os.path.dirname(dst) )
            shutil.copy( src, dst )


def target_archive():

    makedirs("dist")

    os.chdir("dist")
    createZip( ARCHIVE_NAME, DIST_FILES.values() )
    os.chdir("..")
    
    fd = open( "dist/%s" % ARCHIVE_NAME, "rb" )
    m = hashlib.md5()
    while 1:
        data = fd.read( 1024 * 1024 )
        if not data: break
        m.update(data)
    fd.close()
    print( "" )
    print( m.hexdigest() )


def target_clean():
    rmtree("dist")
    rmtree("build")
    rmtree("doc/html_en")
    rmtree("doc/html_ja")
    unlink( "tags" )


#-------------------------------------------

eval( "target_" + action +"()" )
