import os
import sys
import msvcrt
import configparser

import ckit

import clnch_debug
import clnch_resource

ini = None
ini_filename = os.path.join( ckit.getAppDataPath(), clnch_resource.clnch_dirname, 'clnch.ini' )
dirty = False

#--------------------------------------------------------------------

def read():

    global ini
    global dirty

    ini = configparser.RawConfigParser()

    try:
        fd = open( ini_filename, "r", encoding="utf-8" )
        msvcrt.locking( fd.fileno(), msvcrt.LK_LOCK, 1 )
        ini.readfp(fd)
        fd.close()
    except:
        clnch_debug.printErrorInfo()

    dirty = False

def write():

    global dirty
    
    if not dirty: return

    try:
        fd = open( ini_filename, "w", encoding="utf-8" )
        msvcrt.locking( fd.fileno(), msvcrt.LK_LOCK, 1 )
        ini.write(fd)
        fd.close()
        dirty = False
    except:
        clnch_debug.printErrorInfo()

def get( section, option, default=None ):
    #print( "ini.get", section, option )
    try:
        return ini.get( section, option )
    except:
        if default!=None:
            return default
        raise

def getint( section, option, default=None ):
    #print( "ini.getint", section, option )
    try:
        return ini.getint( section, option )
    except:
        if default!=None:
            return default
        raise

def set( section, option, value ):
    
    global dirty
    
    #print( "ini.set", section, option, value )
    assert( type(value)==str )
    
    try:
        if ini.get(section,option)==value:
            return
    except:
        pass

    try:
        ini.add_section(section)
    except configparser.DuplicateSectionError:
        pass

    ini.set( section, option, value )
    
    dirty = True

def setint( section, option, value ):

    global dirty

    #print( "ini.setint", section, option, value )
    assert( type(value)==int )

    try:
        if ini.getint(section,option)==value:
            return
    except:
        pass

    try:
        ini.add_section(section)
    except configparser.DuplicateSectionError:
        pass

    ini.set( section, option, str(value) )

    dirty = True

def remove_section(section):

    global dirty

    if ini.remove_section(section):
        dirty = True
        return True
    else:
        return False    

def remove_option( section, option ):

    global dirty

    try:
        if ini.remove_option( section, option ):
            dirty = True
            return True
        else:
            return False
    except configparser.NoSectionError:
        return False
