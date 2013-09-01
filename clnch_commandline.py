import os
import fnmatch
import inspect
import traceback

import pyauto

import ckit
from ckit.ckit_const import *

import clnch_misc
import clnch_native


## @addtogroup commandline
## @{

#--------------------------------------------------------------------

def executeCommand( commandline, func, args, mod, history_item, quit ):

    # 引数を受け取らない関数やメソッドを許容するためのトリック                
    argspec = inspect.getargspec(func)
    if inspect.ismethod(func):
        num_args = len(argspec[0])-1
    else:
        num_args = len(argspec[0])

    try:
        if num_args==0:
            result = func()
        elif num_args==1:
            result = func(args)
        elif num_args==2:
            result = func(args,mod)
        else:
            raise TypeError("arg spec is not acceptable.")
    except Exception as e:
        print( e )
        return
    
    if isinstance(result,str):
        commandline.setText(result)
        commandline.updateWindowWidth(result)
        commandline.setSelection( [ 0, len(result) ] )
        commandline.paint()
        return

    if history_item!=None:
        commandline.appendHistory( history_item )

    if quit:
        commandline.quit()


## コマンドラインからのコマンド実行機能
class commandline_Launcher:

    def __init__( self, main_window ):
        self.main_window = main_window
        self.command_list = []

    def onCandidate( self, update_info ):

        basedir = "."

        left = update_info.text[ : update_info.selectionLeft() ]
        left_lower = left.lower()
        pos_arg = left.rfind(";")+1
        arg = left[ pos_arg : ]
        pos_dir = max( arg.rfind("/")+1, arg.rfind("\\")+1 )
        directory = arg[:pos_dir]
        directory_lower = directory.lower()
        name_prefix = arg[pos_dir:].lower()

        dirname_list = []
        filename_list = []
        candidate_list = []
        
        if len(directory)>0:

            try:
                path = ckit.joinPath( basedir, directory )
                unc = os.path.splitunc(path)
                if unc[0]:
                    clnch_misc.checkNetConnection(path)
                if unc[0] and not unc[1]:
                    servername = unc[0].replace('/','\\')
                    infolist = clnch_native.enumShare(servername)
                    for info in infolist:
                        if info[1]==0:
                            if info[0].lower().startswith(name_prefix):
                                if ckit.pathSlash():
                                    dirname_list.append( info[0] + "/" )
                                else:
                                    dirname_list.append( info[0] + "\\" )
                else:
                    infolist = clnch_native.findFile( ckit.joinPath(path,'*'), use_cache=True )
                    for info in infolist:
                        if info[0].lower().startswith(name_prefix):
                            if info[3] & ckit.FILE_ATTRIBUTE_DIRECTORY:
                                if ckit.pathSlash():
                                    dirname_list.append( info[0] + "/" )
                                else:
                                    dirname_list.append( info[0] + "\\" )
                            else:                    
                                filename_list.append( info[0] )
            except:
                pass

        for item in self.command_list:
            item_lower = item[0].lower()
            if item_lower.startswith(left_lower):
                candidate_list.append( item[0] )

        return dirname_list + filename_list + candidate_list

    def onEnter( self, commandline, text, mod ):
        
        args = text.split(';')
        
        command_name = args[0].lower()
        
        for command in self.command_list:
            if command[0].lower() == command_name:
                executeCommand( commandline, command[1], args[1:], mod, text, quit=True )
                return True
        
        return False
    
    def onStatusString( self, text ):
        return None
    

## コマンドラインでファイルパスを起動する機能
class commandline_ExecuteFile:

    def __init__( self, main_window ):
        self.main_window = main_window

    def onCandidate( self, update_info ):
        return []
    
    def onEnter( self, commandline, text, mod ):
    
        args = text.split(';')
        
        file = args[0]

        if not os.path.exists(file):
            return False
        
        for association in self.main_window.association_list:
            for pattern in association[0].split():
                if fnmatch.fnmatch( file, pattern ):
                    executeCommand( commandline, association[1], args, mod, text, quit=True )
                    return
        
        joint_args = clnch_misc.joinArgs(args[1:])
        
        directory, tmp = ckit.splitPath(file)
    
        #print( "File: %s" % ( file, ) )
        #print( "      %s" % ( joint_args, ) )

        def jobShellExecute( job_item ):
            pyauto.shellExecute( None, file, joint_args, directory )

        def jobShellExecuteFinished( job_item ):
            pass

        job_item = ckit.JobItem( jobShellExecute, jobShellExecuteFinished )
        ckit.JobQueue.defaultQueue().enqueue(job_item)

        commandline.appendHistory( text )
        
        commandline.quit()

        return True

    def onStatusString( self, text ):
        return None


## コマンドラインで URL を起動する機能
class commandline_ExecuteURL:

    def __init__( self, main_window ):
        self.main_window = main_window

    def onCandidate( self, update_info ):
        return []
    
    def onEnter( self, commandline, text, mod ):
    
        if not (text.lower().startswith("http:") or text.lower().startswith("https:")):
            return False    
        
        #print( "URL: %s" % ( text, ) )

        def jobShellExecute( job_item ):
            pyauto.shellExecute( None, text, "", "" )

        def jobShellExecuteFinished( job_item ):
            pass

        job_item = ckit.JobItem( jobShellExecute, jobShellExecuteFinished )
        ckit.JobQueue.defaultQueue().enqueue(job_item)

        commandline.appendHistory( text )
        
        commandline.quit()

        return True

    def onStatusString( self, text ):
        return None


## コマンドラインでの計算機能
class commandline_Calculator:

    def __init__( self, main_window ):
        self.main_window = main_window

    def onCandidate( self, update_info ):
        return []
    
    def onEnter( self, commandline, text, mod ):
        
        from math import sin, cos, tan, acos, asin, atan
        from math import e, fabs, log, log10, pi, pow, sqrt

        try:
            result = eval(text)
        except:
            return False
        
        if isinstance(result,int):
            result_string = "%d" % result
        elif isinstance(result,float):
            result_string = "%f" % result
        else:
            return False

        commandline.appendHistory( text )
        
        if result_string!=text:

            print( "%s => %s" % ( text, result_string ) )
            commandline.setText( result_string )
            commandline.selectAll()
        
        return True

    def onStatusString( self, text ):
        return None


## コマンドラインでの 10進 <-> 16進 変換機能
class commandline_Int32Hex:

    def __init__( self, main_window ):
        self.main_window = main_window

    def onCandidate( self, update_info ):
        return []
    
    def onEnter( self, commandline, text, mod ):
    
        def base16to10(src):
            if src[:2].lower() != "0x":
                raise ValueError
            i = int( src, 16 )
            if i<0 or i>0xffffffff:
                raise ValueError
            if i>=0x80000000:
                dst = "%d" % ( -0x80000000 + ( i - 0x80000000 ) )
            else:
                dst = "%d" % i
            return dst    

        def base10to16(src):
            i = int( src, 10 )
            if i<-0x80000000 or i>=0x80000000:
                raise ValueError
            if i<0:
                dst = "0x%08x" % ( 0x80000000 + ( i + 0x80000000 ) )
            else:
                dst = "0x%08x" % i
            return dst
        
        text = text.strip()

        try:
            result_string = base10to16(text)
        except:
            try:
                result_string = base16to10(text)
            except:
                return False    

        commandline.appendHistory( text )
        
        if result_string!=text:

            print( "%s => %s" % ( text, result_string ) )
            commandline.setText( result_string )
            commandline.selectAll()
        
        return True

    def onStatusString( self, text ):
        return None
