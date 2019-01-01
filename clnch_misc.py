import sys
import os
import shutil
import datetime
import ctypes

import pyauto
import ckit

import clnch_resource
from ckit.ckit_const import *

## @addtogroup misc その他雑多な機能
## @{

#--------------------------------------------------------------------

ignore_1second = True

#--------------------------------------------------------------------

def getFileSizeString(size):
    
    if size < 1000:
        return "%dB" % ( size, )
    
    if size < 1000*1024:
        s = "%.1fK" % ( size / float(1024), )
        if len(s)<=6 : return s

    if size < 1000*1024*1024:
        s = "%.1fM" % ( size / float(1024*1024), )
        if len(s)<=6 : return s

    if size < 1000*1024*1024*1024:
        s = "%.1fG" % ( size / float(1024*1024*1024), )
        if len(s)<=6 : return s
    
    return "%.1fT" % ( size / float(1024*1024*1024*1024), )

#--------------------------------------------------------------------

_net_connection_handler = None

def registerNetConnectionHandler(handler):
    global _net_connection_handler
    _net_connection_handler = handler

def checkNetConnection(path):

    drive, tail = os.path.splitdrive(path)
    unc = ( drive.startswith("\\\\") or drive.startswith("//") )

    if unc:
        remote_resource_name = drive.replace('/','\\').rstrip('\\')
        try:
            _net_connection_handler(remote_resource_name)
        except Exception as e:
            print( e )

#--------------------------------------------------------------------

def compareTime( t1, t2 ):
    
    if ignore_1second:
        delta = abs( datetime.datetime(*t1) - datetime.datetime(*t2) )
        if delta.days==0 and delta.seconds<=1 : return 0

    return cmp(t1,t2)

#--------------------------------------------------------------------

def findExistingClnchWindow():
    found = [None]
    def callback( wnd, arg ):
        if wnd.getClassName()=="ClnchWindowClass" and wnd.getText()==clnch_resource.clnch_appname + " MainWindow":
            found[0] = wnd
            return False
        return True
    pyauto.Window.enum( callback, None )
    return found[0]
    
#--------------------------------------------------------------------

def replaceMacro( s, map = { "%%" : "%" }, environ=True ):
    
    search_pos = 0
    
    while 1:
    
        var_start = s.find('%',search_pos)
        if var_start < 0 : break;

        var_end = s.find('%',var_start+1)
        if var_end < 0 : break;

        try:
            after = map[ s[ var_start : var_end+1 ] ]
            s = s[:var_start] + after + s[var_end+1:]
            search_pos += len(after)
            continue
        except KeyError:
            pass

        if environ:
            try:
                after = os.environ[ s[ var_start + 1 : var_end ] ]
                s = s[:var_start] + after + s[var_end+1:]
                search_pos += len(after)
                continue
            except KeyError:
                pass

        search_pos += 1

    return s

def joinArgs( args ):
    result = ''
    for arg in args:
        if arg.find(' ') >= 0 :
            result += ' '+ '"' + arg + '"'
        else:
            result += ' '+ arg
    return result.strip()

#--------------------------------------------------------------------

_commandline_normalize_table = str.maketrans(
    "\t\r\n",
    "   "
    )

def normalizeCommandLineText(s):
    s = s.translate(_commandline_normalize_table)
    while s.find("  ")>=0:
        s = s.replace( "  ", " " )
    return s

#--------------------------------------------------------------------

def adjustWindowPosition( base_window, new_window, default_up, monitor_adjust_vertical=True, monitor_adjust_horizontal=True ):

    base_window_rect = base_window.getWindowRect()
    
    x1 = base_window_rect[0]
    x2 = base_window_rect[2]
    y1 = base_window_rect[1]
    y2 = base_window_rect[3]
    
    if default_up:
        y = y1
        origin_y = ORIGIN_Y_BOTTOM
    else:
        y = y2
        origin_y = ORIGIN_Y_TOP

    x = x1
    origin_x = ORIGIN_X_LEFT
           
    monitor_info_list = pyauto.Window.getMonitorInfo()
    for monitor_info in monitor_info_list:
        if monitor_info[0][0] <= x1 < monitor_info[0][2] and monitor_info[0][1] <= y1 < monitor_info[0][3]:
            
            new_window_rect = new_window.getWindowRect()
            char_w, char_h = new_window.getCharSize()
            
            if monitor_adjust_vertical:
                if default_up:
                    if y1 - (new_window_rect[3]-new_window_rect[1]) < monitor_info[1][1]:
                        y = y2
                        origin_y = ORIGIN_Y_TOP
                else:
                    if y2 + (new_window_rect[3]-new_window_rect[1]) >= monitor_info[1][3]:
                        y = y1
                        origin_y = ORIGIN_Y_BOTTOM
            
            if monitor_adjust_horizontal:
                if x1 + (new_window_rect[2]-new_window_rect[0]) >= monitor_info[1][2]:
                    x = x2
                    origin_x = ORIGIN_X_RIGHT
            break

    new_window.setPosSize( x, y, new_window.width(), new_window.height(), origin_x | origin_y )

## @} misc
