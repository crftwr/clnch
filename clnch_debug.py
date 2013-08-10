import sys
import os
import time
import threading
import traceback
import ctypes

import ckit

import clnch_resource

#--------------------------------------------------------------------

block_detect_thread = None

def enableBlockDetector():

    global block_detect_thread
    
    # インタプリタが長時間ブロックしたときに呼ばれる関数
    def blockDetector():
        print( "" )
        print( "Block detected:" )
        traceback.print_stack()
        print( "" )

    ckit.enableBlockDetector( blockDetector )

    # インタプリタが長時間ブロックしたことを検出するために、
    # 定期的にインタプリタを動かし続ける
    class BlockDetectThread( threading.Thread ):

        def __init__(self):
            threading.Thread.__init__(self)
            self.canceled = False

        def run(self):
            ckit.setBlockDetector()
            while not self.canceled:
                time.sleep(0.1)
        
        def cancel(self):
            self.canceled = True
    
    block_detect_thread = BlockDetectThread()
    block_detect_thread.start()

    ckit.setBlockDetector()

def disableBlockDetector():
    
    global block_detect_thread
    
    if block_detect_thread:
        block_detect_thread.cancel()
        block_detect_thread.join()
        block_detect_thread = None

#--------------------------------------------------------------------

exit_timeout_thread = None

def _forceAbort():

    # 残存しているスレッドの情報
    message = "Remaining threads:\n"
    message += "\n"

    for thread in threading.enumerate():
        message += "  %s\n" % str(thread)
    message += "\n"

    for threadId, stack in sys._current_frames().items():
        message += "ThreadID: %s\n" % threadId
        for filename, lineno, name, line in traceback.extract_stack(stack):
            message += '  File: "%s", line %d, in %s\n' % (filename, lineno, name)
            if line:
                message += "    %s\n" % (line.strip())
        message += "\n"

    ctypes.windll.user32.MessageBoxW( 0, message, cfiler_resource.cfiler_appname, 0 )

    os.abort()

def enableExitTimeout():
    
    global exit_timeout_thread
    
    # インタプリタが長時間ブロックしたことを検出するために、
    # 定期的にインタプリタを動かし続ける
    class ExitTimeoutThread( threading.Thread ):

        def __init__(self):
            threading.Thread.__init__(self)
            self.event = threading.Event()

        def run(self):
            ckit.setBlockDetector()
            self.event.wait(10.0)
            if not self.event.isSet():
                _forceAbort()

        def cancel(self):
            self.event.set()
    
    exit_timeout_thread = ExitTimeoutThread()
    exit_timeout_thread.start()

def disableExitTimeout():
    
    global exit_timeout_thread
    
    if exit_timeout_thread:
        exit_timeout_thread.cancel()
        exit_timeout_thread.join()
        exit_timeout_thread = None

#--------------------------------------------------------------------

print_errorinfo_enabled = False

def enablePrintErrorInfo():
    global print_errorinfo_enabled
    print_errorinfo_enabled = True

def disablePrintErrorInfo():
    global print_errorinfo_enabled
    print_errorinfo_enabled = False

def printErrorInfo():
    if print_errorinfo_enabled:
        print( "Debug: ", end="" )
        traceback.print_exc()

#--------------------------------------------------------------------
    