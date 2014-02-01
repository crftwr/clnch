
# パフォーマンスのために、ここで import するのは IPCのために必要な最小限にとどめる

import sys
import os

os.environ["PATH"] = os.path.join( os.path.split(sys.argv[0])[0], 'lib' ) + ";" + os.environ["PATH"]

sys.path[0:0] = [
    os.path.join( os.path.split(sys.argv[0])[0], '..' ),
    os.path.join( os.path.split(sys.argv[0])[0], 'extension' ),
    os.path.join( os.path.split(sys.argv[0])[0], 'lib' ),
    ]

import getopt
import locale

import ckit

ckit.setLocale( locale.getdefaultlocale()[0] )

import pyauto

import clnch_ipc
import clnch_debug
import clnch_resource

#--------------------------------------------------------------------

debug = False
profile = False

ipc_data = clnch_ipc.IpcData()

option_list, args = getopt.getopt( sys.argv[1:], "dp", [] + clnch_ipc.IpcData.options )
for option in option_list:
    if option[0]=="-d":
        debug = True
    elif option[0]=="-p":
        profile = True
    elif ipc_data.trySetOption( option[0], option[1] ):
        pass

#--------------------------------------------------------------------

def findExistingClnchWindow():
    found = [None]
    def callback( wnd, arg ):
        if wnd.getClassName()=="ClnchWindowClass" and wnd.getText()==clnch_resource.clnch_appname:
            found[0] = wnd
            return False
        return True
    pyauto.Window.enum( callback, None )
    return found[0]
    
def sendIpc(wnd):

    print( "another CraftLaunch instance already exists." )
    print( "sending Ipc data." )
    
    ckit.Window.sendIpc( wnd.getHWND(), ipc_data.getValue() )
    
    print( "done." )

existing_clnch_wnd = findExistingClnchWindow()
if existing_clnch_wnd:
    sendIpc(existing_clnch_wnd)
    sys.exit(0)

#--------------------------------------------------------------------

# IPCのために必要でないモジュールはここで import する

import os
import shutil

import clnch
import clnch_mainwindow
import clnch_ini
import clnch_misc

if __name__ == "__main__":

    ckit.registerWindowClass( "Clnch" )
    ckit.registerCommandInfoConstructor( ckit.CommandInfo )

    sys.path[0:0] = [
        os.path.join( ckit.getAppExePath(), 'extension' ),
        ]

    # exeと同じ位置にある設定ファイルを優先する
    if os.path.exists( os.path.join( ckit.getAppExePath(), 'config.py' ) ):
        ckit.setDataPath( ckit.getAppExePath() )
    else:    
        ckit.setDataPath( os.path.join( ckit.getAppDataPath(), clnch_resource.clnch_dirname ) )
        if not os.path.exists(ckit.dataPath()):
            os.mkdir(ckit.dataPath())

    default_config_filename = os.path.join( ckit.getAppExePath(), '_config.py' )
    config_filename = os.path.join( ckit.dataPath(), 'config.py' )
    clnch_ini.ini_filename = os.path.join( ckit.dataPath(), 'clnch.ini' )

    # config.py がどこにもない場合は作成する
    if not os.path.exists(config_filename) and os.path.exists(default_config_filename):
        shutil.copy( default_config_filename, config_filename )

    clnch_ini.read()

    ckit.JobQueue.createDefaultQueue()

    _main_window = clnch_mainwindow.MainWindow(
        config_filename = config_filename,
        debug=debug,
        profile=profile )

    _main_window.configure()

    _main_window.start()

    _main_window.topLevelMessageLoop()

    _main_window.stop()

    _main_window.saveState()

    clnch_debug.enableExitTimeout()

    ckit.JobQueue.cancelAll()

    _main_window.destroy()

    ckit.JobQueue.joinAll()

    clnch_ini.write()

    clnch_debug.disableExitTimeout()

