import os
import sys
import re
import time
import datetime
import profile
import fnmatch
import threading
import zipfile
import configparser
import filecmp
import traceback

import pyauto
import ckit
from ckit.ckit_const import *

import clnch_statusbar
import clnch_msgbox
import clnch_listwindow
import clnch_consolewindow
import clnch_commandwindow
import clnch_musicplayer
import clnch_configmenu
import clnch_commandline
import clnch_misc
import clnch_ini
import clnch_ipc
import clnch_native
import clnch_debug
import clnch_resource
from clnch_resource import *

os.stat_float_times(False)

## @addtogroup mainwindow メインウインドウ機能
## @{

#--------------------------------------------------------------------

PAINT_STATUS_BAR         = 1<<14
PAINT_ALL                = PAINT_STATUS_BAR

## メインウインドウ
#
#  CraftLaunchのメインウインドウを表すクラスです。
#  
#  設定ファイル config.py の configure() に渡される window 引数は、MainWindow クラスのオブジェクトです。
#  CraftLaunch のさまざまな機能が、MainWindowのメソッドとして提供されています。
#
class MainWindow( ckit.TextWindow ):

    def __init__( self, config_filename, debug=False, profile=False ):
    
        self.initialized = False

        self.config_filename = config_filename

        self.debug = debug
        self.profile = profile

        self.loadState()

        self.loadTheme()

        self.status_bar = clnch_statusbar.StatusBar()
        self.simple_status_bar_layer = clnch_statusbar.SimpleStatusBarLayer()
        self.simple_status_bar_resistered = False
        self.custom_status_bar_map = {}
        self.status_bar_paint_hook = None
        self.commandline_edit = None

        self.cmd_keymap = ckit.Keymap()
        self.keymap = ckit.Keymap()
        self.compare_list = []
        self.sorter_list = []
        self.association_list = []
        self.editor = "notepad.exe"
        self.clock_format = "%m/%d(%a) %H:%M"
        self.commandline_list = []
        self.commandline_history = []
        self.commandLineHistoryLoad()

        ckit.TextWindow.__init__(
            self,
            x=0,
            y=0,
            width=clnch_ini.getint( "GEOMETRY", "min_width", 18 ),
            height=1,
            font_name = clnch_ini.get( "FONT", "name", "" ),
            font_size = clnch_ini.getint( "FONT", "size", 12 ),
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            border_size = 3,
            resizable = False,
            noframe = True,
            title_bar = False,
            title = clnch_resource.clnch_appname,
            show = False,
            cursor = True,
            tool = True,
            activate_handler = self._onActivate,
            close_handler = self._onClose,
            endsession_handler = self._onEndSession,
            move_handler = self._onMove,
            size_handler = self._onSize,
            keydown_handler = self._onKeyDown,
            char_handler = self._onChar,
            lbuttondown_handler = self._onLeftButtonDown,
            rbuttondown_handler = self._onRightButtonDown,
            dropfiles_handler = self._onDropFiles,
            ipc_handler = self._onIpc,
            )

        if clnch_ini.getint( "DEBUG", "detect_block", 0 ):
            clnch_debug.enableBlockDetector()

        if clnch_ini.getint( "DEBUG", "print_errorinfo", 0 ):
            clnch_debug.enablePrintErrorInfo()

        self.resetPos()
            
        self.updateTopMost()
        
        self.show(True)

        self.setCursorPos( -1, -1 )

        self.updateHotKey()
        
        self.command = ckit.CommandMap(self)

        self.launcher = clnch_commandline.commandline_Launcher(self)

        self.keydown_hook = None
        self.char_hook = None
        self.enter_hook = None
        self.mouse_event_mask = False
        
        self.quit_requested = False
        
        self.mouse_click_info = None

        self.musicplayer = None

        self.synccall = ckit.SyncCall()

        self.child_window_lock = threading.RLock()
        
        self.last_monitor_info_list = pyauto.Window.getMonitorInfo()

        self.setTimer( self.onTimer, 10 )
        self.setTimer( self.onTimerMonitor, 1000 )

        clnch_misc.registerNetConnectionHandler( self._onCheckNetConnection )

        try:
            self.createThemePlane()
        except:
            traceback.print_exc()

        ckit.initTemp("clnch_")

        self.console_window = clnch_consolewindow.ConsoleWindow( self, debug=debug )
        self.console_window.registerStdio()

        self.updateInactiveBehavior()

        self.initialized = True

        self.paint()

    def destroy(self):
        self.console_window.unregisterStdio()
        self.console_window.destroy()
        ckit.destroyTemp()
        ckit.TextWindow.destroy(self)

    def onTimer(self):
        ckit.JobQueue.checkAll()
        self.synccall.check()

    ## サブスレッドで処理を実行する
    #
    #  @param self              -
    #  @param func              サブスレッドで実行する呼び出し可能オブジェクト
    #  @param arg               引数 func に渡す引数
    #  @param cancel_func       ESCキーが押されたときのキャンセル処理
    #  @param cancel_func_arg   引数 cancel_func に渡す引数
    #  @param raise_error       引数 func のなかで例外が発生したときに、それを raise するか
    #  @param print_traceback   引数 func のなかで例外が発生したときに、エラー発生位置を詳細に出力するか
    #
    #  メインスレッドのユーザインタフェイスの更新を止めずに、サブスレッドの中で任意の処理を行うための関数です。
    #
    #  この関数のなかでは、引数 func をサブスレッドで呼び出しながら、メインスレッドでメッセージループを回します。
    #  返値には、引数 func の返値がそのまま返ります。
    #
    #  ファイルのコピーや画像のデコードなどの、比較的時間のかかる処理は、メインスレッドではなくサブスレッドの中で処理するように心がけるべきです。
    #  さもないと、メインスレッドがブロックし、ウインドウの再描画などが長時間されないままになるといった弊害が発生します。
    #
    def subThreadCall( self, func, arg, cancel_func=None, cancel_func_arg=(), raise_error=False, print_traceback=False ):

        class SubThread( threading.Thread ):

            def __init__( self, main_window ):
                threading.Thread.__init__(self)
                self.main_window = main_window
                self.result = None
                self.error = None

            def run(self):
                try:
                    self.result = func(*arg)
                except Exception as e:
                    if print_traceback:
                        traceback.print_exc()
                    self.error = e

        def onKeyDown( vk, mod ):
            if vk==VK_ESCAPE:
                if cancel_func:
                    cancel_func(*cancel_func_arg)
            return True

        def onChar( ch, mod ):
            return True

        keydown_hook_old = self.keydown_hook
        char_hook_old = self.char_hook
        mouse_event_mask_old = self.mouse_event_mask

        sub_thread = SubThread(self)
        sub_thread.start()

        self.keydown_hook = onKeyDown
        self.char_hook = onChar
        self.mouse_event_mask = True

        self.removeKeyMessage()
        self.messageLoop( sub_thread.isAlive )

        sub_thread.join()
        result = sub_thread.result
        error = sub_thread.error
        del sub_thread

        self.keydown_hook = keydown_hook_old
        self.char_hook = char_hook_old
        self.mouse_event_mask = mouse_event_mask_old

        if error:
            if raise_error:
                raise error
            else:
                print( error )
        
        return result

    ## コンソールプログラムをサブプロセスとして実行する
    #
    #  @param self              -
    #  @param cmd               コマンドと引数のシーケンス
    #  @param cwd               サブプロセスのカレントディレクトリ
    #  @param env               サブプロセスの環境変数
    #  @param enable_cancel     True:ESCキーでキャンセルする  False:ESCキーでキャンセルしない
    #
    #  任意のコンソールプログラムを、CraftLaunchのサブプロセスとして実行し、そのプログラムの出力を、コンソールウインドウにリダイレクトします。
    #
    #  引数 cmd には、サブプロセスとして実行するプログラムと引数をリスト形式で渡します。\n
    #  例:  [ "subst", "R:", "//remote-machine/public/" ]
    #
    def subProcessCall( self, cmd, cwd=None, env=None, enable_cancel=False ):

        p = ckit.SubProcess(cmd,cwd,env)
        
        if enable_cancel:
            cancel_handler = p.cancel
        else:
            cancel_handler = None

        return self.subThreadCall( p, (), cancel_handler )

    ## コマンドラインで文字列を入力する
    #
    #  @param self                      -
    #  @param title                     コマンド入力欄の左側に表示されるタイトル文字列
    #  @param text                      コマンド入力欄の初期文字列
    #  @param selection                 コマンド入力欄の初期選択範囲
    #  @param auto_complete             自動補完を有効にするか
    #  @param autofix_list              入力確定をする文字のリスト
    #  @param update_handler            コマンド入力欄の変更があったときに通知を受けるためのハンドラ
    #  @param candidate_handler         補完候補を列挙するためのハンドラ
    #  @param candidate_remove_handler  補完候補を削除するためのハンドラ
    #  @param status_handler            コマンド入力欄の右側に表示されるステータス文字列を返すためのハンドラ
    #  @param keydown_handler           コマンド入力欄でキー入力が行われたときのハンドラ
    #  @param char_handler              コマンド入力欄で文字入力が行われたときのハンドラ
    #  @param enter_handler             コマンド入力欄でEnterキーが押されたときのハンドラ
    #  @param escape_handler            コマンド入力欄でEscapeキーが押されたときのハンドラ
    #  @return                          入力された文字列
    #
    #  コマンド入力欄で任意の文字列の入力を受け付けるための関数です。
    #  コマンドを解釈/実行するのは、このメソッドの呼び出し元の役割です。
    #
    def commandLine( self, title, text="", selection=None, auto_complete=False, autofix_list=None, update_handler=None, candidate_handler=None, candidate_remove_handler=None, status_handler=None, keydown_handler=None, char_handler=None, enter_handler=None, escape_handler=None ):

        if title:
            title = " " + title + " "
        if selection==None : selection=[ len(text), len(text) ]
        title_width = self.getStringWidth(title)
        status_string = [ "" ]
        result = [ None ]

        class CommandLine:

            def __init__( commandline_self ):
                commandline_self.planned_command_list = []
                
            def _onKeyDown( commandline_self, vk, mod ):
            
                if keydown_handler:
                    if keydown_handler( commandline_self, vk, mod ):
                        return True
            
                if self.commandline_edit.onKeyDown( vk, mod ):
                    return True

                if vk==VK_RETURN:
                    result[0] = self.commandline_edit.getText()
                    if enter_handler:
                        self.commandline_edit.closeList()
                        if enter_handler( commandline_self, result[0], mod ):
                            return True
                    commandline_self.quit()

                elif vk==VK_ESCAPE:
                    if self.commandline_edit.getText():
                        self.commandline_edit.clear()
                    elif self.console_window.isVisible():
                        self.console_window.show(False)
                    else:
                        if escape_handler:
                            if escape_handler(commandline_self):
                                return True
                        commandline_self.quit()

                return True

            def _onChar( commandline_self, ch, mod ):

                if char_handler:
                    if char_handler( commandline_self, ch, mod ):
                        return True
            
                self.commandline_edit.onChar( ch, mod )

                return True

            def _onUpdate( commandline_self, update_info ):

                if update_handler:
                    if not update_handler(update_info):
                        return False
                if status_handler:
                    status_string[0] = status_handler(update_info)
                    self.paint(PAINT_STATUS_BAR)
                
                commandline_self.updateWindowWidth(update_info.text)

            def _onPaint( commandline_self, x, y, width, height ):
            
                if status_string[0]:
                    status_string_for_paint = "  " + status_string[0] + " "
                else:
                    status_string_for_paint = ""
                status_width = self.getStringWidth(status_string_for_paint)
                edit_width = width-title_width-status_width

                attr = ckit.Attribute( fg=ckit.getColor("bar_fg") )
                
                if self.active:
                    self.putString( x, y, title_width, height, attr, title )
                    self.putString( x+width-status_width, y, status_width, height, attr, status_string_for_paint )
                else:
                    self.putString( x, y, title_width, height, attr, " "*title_width )
                    self.putString( x+width-status_width, y, status_width, height, attr, " "*status_width )

                self.commandline_edit.setPosSize( x+title_width, y, edit_width, height )

                self.commandline_edit.enableCursor( self.active )
                if not self.active:
                    self.setCursorPos( -1, -1 )
                
                self.commandline_edit.paint()

            def paint(commandline_self):
                self.paint()

            def getText(commandline_self):
                return self.commandline_edit.getText()
            
            def setText( commandline_self, text ):
                self.commandline_edit.setText(text)

            def getSelection(commandline_self):
                return self.commandline_edit.getSelection()

            def setSelection(commandline_self,selection):
                self.commandline_edit.setSelection(selection)

            def selectAll(commandline_self):
                self.commandline_edit.selectAll()

            def getWindowWidthFromText( commandline_self, text ):

                edit_width = self.getStringWidth(text) + 2

                if status_string[0]:
                    status_width = self.getStringWidth(status_string[0]) + 2
                else:
                    status_width = 0

                window_width = title_width + edit_width + status_width

                window_width = max( window_width, clnch_ini.getint( "GEOMETRY", "min_width", 18 ) )
                window_width = min( window_width, clnch_ini.getint( "GEOMETRY", "max_width", 80 ) )
                
                return window_width

            def getEditWidthFromWindowWidth( commandline_self, window_width ):

                if status_string[0]:
                    status_width = self.getStringWidth(status_string[0]) + 2
                else:
                    status_width = 0

                edit_width = window_width - title_width - status_width
                
                return edit_width

            def updateWindowWidth( commandline_self, text ):
                
                window_width = commandline_self.getWindowWidthFromText(text)
                if window_width == self.width() : return
                window_rect = self.getWindowRect()
                self.setPosSize( window_rect[0], window_rect[1], window_width, self.height(), 0 )                    

            def planCommand( commandline_self, command, info, history ):
                commandline_self.planned_command_list.append( ( command, info, history ) )

            def executeCommand( commandline_self, command, info, history_item, quit ):

                try:
                    result = command(info)
                except Exception as e:
                    print( e )
                    return
    
                if isinstance(result,str):
                    commandline_self.setText(result)
                    commandline_self.updateWindowWidth(result)
                    commandline_self.setSelection( [ 0, len(result) ] )
                    commandline_self.paint()
                    return

                if history_item!=None:
                    commandline_self.appendHistory( history_item )

                if quit:
                    commandline_self.quit()

            def appendHistory(commandline_self,newentry):
                newentry_lower = newentry.lower()
                for i in range(len(self.commandline_history)):
                    if self.commandline_history[i].lower()==newentry_lower:
                        del self.commandline_history[i]
                        break
                self.commandline_history.insert( 0, newentry )

                if len(self.commandline_history)>1000:
                    self.commandline_history = self.commandline_history[:1000]

            def quit(commandline_self):
                commandline_self.updateWindowWidth("")
                self.console_window.show(False)
                self.quit()

        commandline_edit_old = self.commandline_edit
        keydown_hook_old = self.keydown_hook
        char_hook_old = self.char_hook
        mouse_event_mask_old = self.mouse_event_mask
        status_bar_paint_hook_old = self.status_bar_paint_hook

        commandline = CommandLine()
        
        if status_handler:
            status_string[0] = status_handler(ckit.EditWidget.UpdateInfo(text,selection))
        
        window_width = commandline.getWindowWidthFromText(text)
        edit_width = commandline.getEditWidthFromWindowWidth(window_width)
        
        self.commandline_edit = ckit.EditWidget( self, title_width, self.height()-1, edit_width, 1, text, selection, auto_complete=auto_complete, no_bg=False, autofix_list=autofix_list, update_handler=commandline._onUpdate, candidate_handler=candidate_handler, candidate_remove_handler=candidate_remove_handler )
        self.commandline_edit.setImeRect( ( 0, 0, clnch_ini.getint( "GEOMETRY", "max_width", 80 ), 1 ) )
        self.keydown_hook = commandline._onKeyDown
        self.char_hook = commandline._onChar
        self.mouse_event_mask = True
        self.status_bar_paint_hook = commandline._onPaint

        commandline.updateWindowWidth(text)

        self.paint(PAINT_STATUS_BAR)

        self.removeKeyMessage()
        def checkContinue():
            return self.active or len(self.commandline_edit.getText())>0
        self.messageLoop( checkContinue )

        self.commandline_edit.destroy()

        self.commandline_edit = commandline_edit_old
        self.keydown_hook = keydown_hook_old
        self.char_hook = char_hook_old
        self.mouse_event_mask = mouse_event_mask_old
        self.status_bar_paint_hook = status_bar_paint_hook_old
        
        self.enableIme(False)

        self.setCursorPos( -1, -1 )
        self.updateThemeSize()

        self.paint(PAINT_STATUS_BAR)

        for command, info, history in commandline.planned_command_list:
            commandline.executeCommand( command, info, history, quit=False )

        return result[0]

    def commandLineHistoryLoad(self):
        for i in range(1000):
            try:
                self.commandline_history.append( clnch_ini.get( "COMMANDLINE", "history_%d"%(i,) ) )
            except:
                break

    def commandLineHistorySave(self):
        i=0
        while i<len(self.commandline_history):
            clnch_ini.set( "COMMANDLINE", "history_%d"%(i,), self.commandline_history[i] )
            i+=1
        while True:
            if not clnch_ini.remove_option( "COMMANDLINE", "history_%d"%(i,) ) : break
            i+=1

    def _onActivate( self, active ):

        self.active = active
        
        self.paint()
        
        if self.commandline_edit:
            self.commandline_edit.onWindowActivate(active)

        if not active:
            self.saveState()
            clnch_ini.write()    

    def _onClose( self ):
        self.quit()

    def _onEndSession( self ):
        self.saveState()
        clnch_ini.write()    

    def _onMove( self, x, y ):

        if not self.initialized : return

        if self.commandline_edit:
            self.commandline_edit.onWindowMove()

    def _onSize( self, width, height ):
        self.updateThemeSize()
        self.paint()

    def _onKeyDown( self, vk, mod ):

        #print( "_onKeyDown", vk, mod )

        if self.keydown_hook:
            if self.keydown_hook( vk, mod ):
                return True

        return True

    def _onChar( self, ch, mod ):

        #print( "_onChar", ch, mod )

        if self.char_hook:
            if self.char_hook( ch, mod ):
                return

    def _onLeftButtonDown( self, x, y, mod ):

        #print( "_onLeftButtonDown", x, y, mod )

        #if self.mouse_event_mask : return
        
        self.drag(x,y);
        
    def _onRightButtonDown( self, x, y, mod ):
        
        #print( "_onRightButtonDown", x, y, mod )

        #if self.mouse_event_mask : return
        
        pass

    def _onDropFiles( self, x, y, filename_list ):

        #print( "_onDropFiles", filename_list )
        
        self.hotkey_Activate()

        for filename in filename_list:
            
            name = os.path.split(filename)[1]
            name = os.path.splitext(name)[0]
            name = name.replace(" ","")
        
            ext = os.path.splitext(filename)[1].lower()
            if ext=='.lnk':
                command = (name,) + clnch_native.getShellLinkInfo(filename)[:3]
            elif ext=='.url':
                command = ( name, clnch_native.getInternetShortcutInfo(filename), "", "" )
            else:
                directory = os.path.split(filename)[0]
                command = ( name, filename, "", directory )

            command = clnch_commandwindow.popCommandWindow( self, *command )
            if command:
                self.appendCommandToIniFile(command)


    def _onIpc( self, data ):
        ipc_data = clnch_ipc.IpcData(data)
        ipc_data.execute( self )
        ipc_data.commandLine( self )
        
    def _onCheckNetConnection( self, remote_resource_name ):
        
        def addConnection( hwnd, remote_resource_name ):
            try:
                clnch_native.addConnection( hwnd, remote_resource_name )
            except Exception as e:
                print( "ERROR : 接続失敗 : %s" % remote_resource_name )
                print( e, "\n" )
    
        self.synccall( addConnection, (self.getHWND(), remote_resource_name) )
            
    def ratioToScreen( self, ratio ):
        rect = self.getWindowRect()
        return ( int(rect[0] * (1-ratio[0]) + rect[2] * ratio[0]), int(rect[1] * (1-ratio[1]) + rect[3] * ratio[1]) )

    def centerOfWindowInPixel(self):
        rect = self.getWindowRect()
        return ( (rect[0]+rect[2])//2, (rect[1]+rect[3])//2 )

    def statusBar(self):
        return self.status_bar

    def registerStatusBar( self, func, priority=-1, interval=None ):

        if func in self.custom_status_bar_map:
            return
        
        class CustomStatusBarLayer(clnch_statusbar.StatusBarLayer):

            def __init__( layer_self ):
                clnch_statusbar.StatusBarLayer.__init__( layer_self, priority )
                if interval:
                    self.setTimer( layer_self.onTimer, interval )
            
            def destroy( layer_self ):
                if interval:
                    self.killTimer( layer_self.onTimer )
                
            def paint( layer_self, window, x, y, width, height ):
                s = " %s" % ( func(width) )
                s = ckit.adjustStringWidth( window, s, width-1 )
                attr = ckit.Attribute( fg=ckit.getColor("bar_fg") )
                window.putString( x, y, width, height, attr, s )
        
            def onTimer( layer_self ):
                if self.commandline_edit==None and self.status_bar.isActiveLayer(layer_self):
                    self.paint( PAINT_STATUS_BAR )
        
        custom_status_bar_layer = CustomStatusBarLayer()
        self.status_bar.registerLayer(custom_status_bar_layer)
        self.custom_status_bar_map[func] = custom_status_bar_layer
    
    def unregisterStatusBar( self, func ):

        if not func in self.custom_status_bar_map:
            return

        custom_status_bar_layer = self.custom_status_bar_map[func]
        self.status_bar.unregisterLayer(custom_status_bar_layer)
        custom_status_bar_layer.destroy()
        del self.custom_status_bar_map[func]
            
    def _onStatusMessageTimedout(self):
        self.clearStatusMessage()

    def setStatusMessage( self, message, timeout=None, error=False ):

        self.simple_status_bar_layer.setMessage(message,error)

        if not self.simple_status_bar_resistered:
            self.status_bar.registerLayer(self.simple_status_bar_layer)
            self.simple_status_bar_resistered = True

        if timeout!=None:
            self.killTimer( self._onStatusMessageTimedout )
            self.setTimer( self._onStatusMessageTimedout, timeout )

        self.paint( PAINT_STATUS_BAR )

    def clearStatusMessage( self ):
        self.simple_status_bar_layer.setMessage("")
        self.status_bar.unregisterLayer(self.simple_status_bar_layer)
        self.simple_status_bar_resistered = False
        self.paint( PAINT_STATUS_BAR )
        self.killTimer(self._onStatusMessageTimedout)

    #--------------------------------------------------------------------------

    def loadTheme(self):
        name = clnch_ini.get( "THEME", "name", ckit.default_theme_name )
        default_color = {
        }
        ckit.setTheme( name, default_color )
        self.theme_enabled = False

    def reloadTheme(self):
        self.loadTheme()
        self.destroyThemePlane()
        self.createThemePlane()
        self.updateColor()

    def createThemePlane(self):
        self.plane_statusbar = ckit.ThemePlane3x3( self, 'bar.png', 1.5 )
        self.theme_enabled = True
        self.updateThemeSize()
        
    def destroyThemePlane(self):
        self.plane_statusbar.destroy()
        self.theme_enabled = False

    def updateThemeSize(self):

        if not self.theme_enabled : return

        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()

        self.plane_statusbar.setPosSize( 0, 0, client_rect[2], client_rect[3] )

    #--------------------------------------------------------------------------

    def updateColor(self):
        self.setBGColor( ckit.getColor("bg") )
        self.setCursorColor( ckit.getColor("cursor0"), ckit.getColor("cursor1") )
        self.paint()
        
        self.console_window.updateColor()

    #--------------------------------------------------------------------------

    def updateFont(self):
        fontname = clnch_ini.get( "FONT", "name", "" )
        self.setFont( fontname, clnch_ini.getint( "FONT", "size", 12 ) )
        window_rect = self.getWindowRect()
        self.setPosSize( window_rect[0], window_rect[1], self.width(), self.height(), 0 )
        
        self.console_window.updateFont()

    #--------------------------------------------------------------------------

    def _onTimerTopmost(self):
        wnd = pyauto.Window.fromHWND( self.getHWND() )
        wnd = wnd.getPrevious()
        while wnd:
            if( wnd.isVisible() 
            and not wnd.getClassName().startswith("#")
            and not wnd.getClassName() in ( "ClnchWindowClass", "SysShadow" )
            and not wnd.getProcessName().lower().endswith(".scr") ):
                #print( "_onTimerTopmost", wnd.getClassName(), wnd.getText(), wnd.getProcessName() )
                self.topmost(True)
                break
            wnd = wnd.getPrevious()
        
    def updateTopMost(self):
        
        topmost = clnch_ini.getint( "GEOMETRY", "topmost", 0 )
        self.topmost(topmost!=0)
        
        if topmost==2:
            self.setTimer( self._onTimerTopmost, 10 )
        else:
            self.killTimer( self._onTimerTopmost )

    #--------------------------------------------------------------------------

    ## ウインドウ位置を初期化する
    #
    #  @param self  -
    #
    #  ウインドウ位置を、設定メニューの [表示位置の保存] で保存されたウインドウ位置にリセットします。
    #
    def resetPos(self):

        rect = self.getWindowRect()

        monitor = clnch_ini.getint( "GEOMETRY", "monitor", 0 )
        x = clnch_ini.getint( "GEOMETRY", "x", 0 )
        y = clnch_ini.getint( "GEOMETRY", "y", 0 )
        
        monitor_info_list = pyauto.Window.getMonitorInfo()
        if not monitor<len(monitor_info_list):
            monitor = 0
            x = 0
            y = 0
        
        monitor_info = monitor_info_list[monitor]
        if x>=0:
            x = monitor_info[0][0] + x
        else:
            x = monitor_info[0][2] + x - (rect[2]-rect[0]) + 1

        if y>=0:
            y = monitor_info[0][1] + y
        else:
            y = monitor_info[0][3] + y - (rect[3]-rect[1]) + 1

        self.setPosSize( x, y, self.width(), self.height(), 0 )                    

    def onTimerMonitor(self):
        monitor_info_list = pyauto.Window.getMonitorInfo()
        if monitor_info_list != self.last_monitor_info_list:
            self.resetPos()
            self.last_monitor_info_list = monitor_info_list

    #--------------------------------------------------------------------------

    def _statusbar_Clock( self, width ):
        now = datetime.datetime.now()
        return now.strftime(self.clock_format)

    def updateInactiveBehavior(self):

        inactive_behavior = clnch_ini.get( "MISC", "inactive_behavior", "clock" )
        
        if inactive_behavior=="clock":
            self.registerStatusBar( self._statusbar_Clock, priority=-1, interval=1000 )
        else:    
            self.unregisterStatusBar( self._statusbar_Clock )

    #--------------------------------------------------------------------------

    def paint( self, option=PAINT_ALL ):
    
        if not self.initialized : return

        if option & PAINT_STATUS_BAR:
            if self.status_bar_paint_hook:
                self.status_bar_paint_hook( 0, self.height()-1, self.width(), 1 )
            else:
                self.status_bar.paint( self, 0, self.height()-1, self.width(), 1 )

    #--------------------------------------------------------------------------

    ## 設定を読み込む
    #
    #  キーマップや command_list などをリセットした上で、config,py を再読み込みします。
    #
    def configure(self):

        default_keymap = clnch_ini.get( "MISC", "default_keymap", "106" )

        ckit.Keymap.init()
        self.cmd_keymap = ckit.Keymap()
        self.keymap = ckit.Keymap()
        self.keymap[ "C-K" ] = self.command.RemoveHistory
        self.cmd_keymap[ "C-Period" ] = self.command.MusicList
        self.cmd_keymap[ "C-S-Period" ] = self.command.MusicStop
        if default_keymap=="101":
            self.cmd_keymap[ "C-Slash" ] = self.command.ContextMenu
        elif default_keymap=="106":
            self.cmd_keymap[ "C-BackSlash" ] = self.command.ContextMenu

        self.association_list = [
            ( "*.mp3 *.wma *.wav", self.command.MusicPlay ), 
        ]

        self.commandline_list = [
            self.launcher,
            clnch_commandline.commandline_ExecuteURL(self),
            clnch_commandline.commandline_ExecuteFile(self),
            clnch_commandline.commandline_Int32Hex(self),
            clnch_commandline.commandline_Calculator(self),
        ]
        
        self.launcher.command_list = [
            ( "Edit",      self.command.Edit ),
            ( "History",   self.command.History ),
            ( "Command",   self.command.CommandList ),
            ( "Config",    self.command.ConfigMenu ),
            ( "Reload",    self.command.Reload ),
            ( "About",     self.command.About ),
            ( "Quit",      self.command.Quit ),
        ]
        
        self.loadCommandFromIniFile()

        ckit.reloadConfigScript( self.config_filename )
        ckit.callConfigFunc("configure",self)


    #--------------------------------------------------------------------------

    def loadState(self):
        
        if clnch_ini.get( "MISC", "directory_separator", "backslash" )=="slash":
            ckit.setPathSlash(True)
        else:
            ckit.setPathSlash(False)

    def saveState(self):

        try:
            clnch_ini.set( "GEOMETRY", "width", str(self.width()) )
            clnch_ini.set( "GEOMETRY", "height", str(self.height()) )

            self.commandLineHistorySave()
            
            self.console_window.saveState()

            if self.musicplayer:
                self.musicplayer.save( "MUSIC" )
                clnch_ini.set( "MUSIC", "restore", str(1) )
            else:
                clnch_ini.set( "MUSIC", "restore", str(0) )

        except Exception as e:
            print( "Save State Failed" )
            print( "  %s" % str(e) )
            #traceback.print_exc()

    #--------------------------------------------------------------------------

    def loadCommandFromIniFile(self):

        i=0
        while True:
            try:
                command_string = clnch_ini.get( "COMMANDLIST", "command_%d"%(i,) )
            except:
                break
            
            command_tuple = eval( command_string )
            command_name, command_args = command_tuple[0], command_tuple[1:]

            command = self.ShellExecuteCommand( None, *command_args )
            self.launcher.command_list.append( ( command_name, command ) )

            i+=1

    def appendCommandToIniFile( self, command_tuple ):
    
        i=0
        while True:
            try:
                clnch_ini.get( "COMMANDLIST", "command_%d"%(i,) )
            except:
                break
            i+=1
        clnch_ini.set( "COMMANDLIST", "command_%d"%(i,), str(tuple(command_tuple)) )
        command = self.ShellExecuteCommand( None, *command_tuple[1:] )
        self.launcher.command_list.append( ( command_tuple[0], command ) )    

    #--------------------------------------------------------------------------

    def start(self):
        
        print( clnch_resource.startupString() )

        # 音楽プレイヤの復元
        if clnch_ini.getint( "MUSIC", "restore", 0 ):
            if self.musicplayer==None:
                self.musicplayer = clnch_musicplayer.MusicPlayer(self)
            self.musicplayer.load( "MUSIC" )    
        
        self.console_window.setAutoShow(True)    

    def stop(self):
        self.console_window.setAutoShow(False)    

    #--------------------------------------------------------------------------
    
    def activeMessageLoop( self, text="", selection=None ):

        def onCandidate( update_info ):

            left = update_info.text[ : update_info.selectionLeft() ]
            left_lower = left.lower()
            pos_arg = left.rfind(";")+1
            arg = left[ pos_arg : ]
            pos_dir = max( arg.rfind("/")+1, arg.rfind("\\")+1 )
            directory = arg[:pos_dir]
            directory_lower = directory.lower()
            name_prefix = arg[pos_dir:].lower()

            candidate_list = []
            candidate_map = {}

            for item in self.commandline_history:
                item_lower = item.lower()
                if item_lower.startswith(left_lower):
                    cand = item[ pos_arg + pos_dir : ]
                    if cand and not cand in candidate_map:
                        candidate_list.append( cand )
                        candidate_map[cand] = True

            for commandline_function in self.commandline_list:
                for cand in commandline_function.onCandidate( update_info ):
                    if cand and not cand in candidate_map:
                        candidate_list.append( cand )
                        candidate_map[cand] = True

            return candidate_list, pos_arg + pos_dir

        def onCandidateRemove(text):
            try:
                self.commandline_history.remove(text)
                return True
            except ValueError:
                pass
            return False

        def statusString( update_info ):
            if update_info.text:
                for commandline_function in self.commandline_list:
                    if hasattr(commandline_function,"onStatusString"):
                        s = commandline_function.onStatusString(update_info.text)
                        if s!=None:
                            return s
            return None

        def onKeyDown( commandline, vk, mod ):
            try:
                func = self.cmd_keymap.table[ ckit.KeyEvent(vk,mod) ]
                quit = True
                append_history = True
            except KeyError:
                try:
                    func = self.keymap.table[ ckit.KeyEvent(vk,mod) ]
                    quit = False
                    append_history = False
                except KeyError:
                    return
            text = commandline.getText()    
            args = text.split(';')

            if append_history:
                history_item = text
            else:
                history_item = None
            
            info = ckit.CommandInfo()
            info.args = args
            info.mod = 0

            commandline.executeCommand( func, info, history_item, quit=quit )

            return True

        def onEnter( commandline, text, mod ):
            for commandline_function in self.commandline_list:
                if commandline_function.onEnter( commandline, text, mod ):
                    break
            return True

        def onEscape( commandline ):
            self.resetPos()
            self.inactivate()
            return True

        auto_complete = clnch_ini.getint( "MISC", "auto_complete", "1" )
        self.commandLine( "", text=text, selection=selection, auto_complete=auto_complete, autofix_list=["\\/",".",";"], candidate_handler=onCandidate, candidate_remove_handler=onCandidateRemove, status_handler=statusString, keydown_handler=onKeyDown, enter_handler=onEnter, escape_handler=onEscape )

    def inactiveMessageLoop(self):

        inactive_behavior = clnch_ini.get( "MISC", "inactive_behavior", "clock" )

        if inactive_behavior=="hide":
            self.show(False)

        self.removeKeyMessage()
        def checkContinue():
            return not self.active
        self.messageLoop( checkContinue )

    def topLevelMessageLoop(self):

        while not self.quit_requested:
            if self.active:
                self.activeMessageLoop()
            else:
                self.inactiveMessageLoop()

    #--------------------------------------------------------------------------

    def hotkey_Activate(self):

        hotkey_behavior = clnch_ini.get( "MISC", "hotkey_behavior", "activate" )
        
        if self.active and hotkey_behavior=="toggle":
            self.inactivate()
            return

        self.restore()
        self.foreground()
        if self.isEnabled():
            self.activate()

    def updateHotKey(self):

        activate_vk = clnch_ini.getint( "HOTKEY", "activate_vk", 0 )
        activate_mod = clnch_ini.getint( "HOTKEY", "activate_mod", 0 )

        self.killHotKey( self.hotkey_Activate )
        self.setHotKey( activate_vk, activate_mod, self.hotkey_Activate )

    #--------------------------------------------------------------------------

    def executeCommand( self, name, info ):
        try:
            command = getattr( self, "command_" + name )
        except AttributeError:
            return False

        command(info)
        return True

    def enumCommand(self):
        for attr in dir(self):
            if attr.startswith("command_"):
                yield attr[ len("command_") : ]

    #--------------------------------------------------------
    # ここから下のメソッドはキーに割り当てることができる
    #--------------------------------------------------------

    ## ファイルをテキストエディタで編集する
    #
    #  MainWindow.editor に設定されたテキストエディタを使って、引数に与えられたファイルを開きます。
    #
    def command_Edit( self, info ):

        def edit():
            for arg in info.args:
                if not os.path.isfile(arg) : continue
                if callable(self.editor):
                    self.editor(arg)
                else:
                    directory, tmp = os.path.split(arg)
                    pyauto.shellExecute( None, self.editor, '"%s"' % arg, directory )

        self.subThreadCall( edit, () )

    ## コンテキストメニューを開く
    #
    #  引数に与えられたファイルに関して、コンテキストメニューを開きます。
    #
    def command_ContextMenu( self, info ):
        
        if len(info.args)<=0 :
            return
        if not os.path.exists(info.args[0]) :
            return
        dirname, name = os.path.split( os.path.normpath(info.args[0]) )
        
        self.commandline_edit.closeList()
        
        pos = self.charToScreen( self.commandline_edit.x + self.commandline_edit.width, 1 )
        self.removeKeyMessage()
        clnch_native.popupContextMenu( self.getHWND(), pos[0], pos[1], dirname, [name] )

    ## 終了する
    #
    #  CraftLaunch を終了します。
    #
    def command_Quit( self, info ):
        self.quit_requested = True
        self.quit()

    ## 音楽プレイヤのファイルリストを開く
    #
    def command_MusicList( self, info ):

        if not self.musicplayer:
            self.setStatusMessage( "Musicがありません", 1000, error=True )
            return

        musicplayer_items, selection = self.musicplayer.getPlayList()

        items = []
        for music_item in musicplayer_items:
            items.append( music_item )

        def onKeyDown( vk, mod ):

            if vk==VK_OEM_PERIOD and mod==MODKEY_CTRL:
                self.musicplayer.pause()
                if self.musicplayer.isPlaying():
                    self.setStatusMessage( "Music : 再開", 3000 )
                else:
                    self.setStatusMessage( "Music : 一時停止", 3000 )
                list_window.cancel()
                return True

            elif vk==VK_OEM_PERIOD and mod==MODKEY_CTRL|MODKEY_SHIFT:
                self.command.MusicStop()
                list_window.cancel()
                return True

            elif vk==VK_LEFT and mod==MODKEY_CTRL:
                self.musicplayer.advance( -10.0 )

            elif vk==VK_RIGHT and mod==MODKEY_CTRL:
                self.musicplayer.advance( 10.0 )

        def onStatusMessage( width, select ):
            return ""

        pos = self.centerOfWindowInPixel()
        list_window = clnch_listwindow.ListWindow( pos[0], pos[1], 5, 1, 80, 16, self, False, "music player", items, initial_select=selection, keydown_hook=onKeyDown, onekey_search=False, statusbar_handler=onStatusMessage )
        clnch_misc.adjustWindowPosition( self, list_window, default_up=False )
        list_window.show(True)
        self.enable(False)
        list_window.messageLoop()
        result = list_window.getResult()
        self.enable(True)
        self.activate()
        list_window.destroy()

        if result<0 : return

        self.musicplayer.select(result)

    ## 音楽の再生を開始する
    #
    def command_MusicPlay( self, info ):

        playlist = []
        selection = 0

        for arg in info.args:
            dirname, name = os.path.split(arg)
            ext = os.path.splitext(arg)[1].lower()
            fileinfo_list = clnch_native.findFile( os.path.join(dirname,"*") )
            for fileinfo in fileinfo_list:
                if os.path.splitext(fileinfo[0])[1].lower()==ext:
                    if not (fileinfo[3] & ckit.FILE_ATTRIBUTE_DIRECTORY):
                        playlist.append( ckit.joinPath( dirname, fileinfo[0] ) )
                        if arg==info.args[0] and fileinfo[0].lower()==name.lower():
                            selection = len(playlist)-1

        if len(playlist) :
            if self.musicplayer==None:
                self.musicplayer = clnch_musicplayer.MusicPlayer(self)
            self.musicplayer.setPlayList( playlist, selection )
            self.musicplayer.play()

    ## 音楽の再生を停止する
    #
    def command_MusicStop( self, info ):
        if self.musicplayer:
            self.musicplayer.destroy()
            self.musicplayer = None
            self.setStatusMessage( "Music : 停止", 3000 )

    ## アプリケーションやファイルの起動を行うコマンドオブジェクトを生成する
    #
    #  @param self          -
    #  @param verb          操作
    #  @param filename      操作対象のファイル
    #  @param param         操作のパラメータ
    #  @param directory     既定のディレクトリ
    #  @param swmode        表示状態
    #
    #  指定されたプログラムを起動するコマンドオブジェクトを生成し、返します。
    #
    #  引数verbには、実行する操作を文字列で渡します。指定可能な文字列は対象によって異なりますが、一般的には次のような操作が指定可能です。
    #
    #  open
    #       ファイルを開きます。またはプログラムを起動します。
    #  edit
    #       ファイルを編集します。
    #  properties
    #       ファイルのプロパティを表示します。
    #
    #  引数swmodeには、以下のいずれかの文字列(またはNone)を渡します。
    #
    #  "normal"または""またはNone
    #       アプリケーションを通常の状態で起動します。
    #  "maximized"
    #       アプリケーションを最大化状態で起動します。
    #  "minimized"
    #       アプリケーションを最小化状態で起動します。
    #
    #  引数の意味の詳細については、以下の解説を参照してください。
    #  http://msdn.microsoft.com/ja-jp/library/cc422072.aspx
    #
    #  プログラムの起動は、サブスレッドの中で行われます。
    #
    def ShellExecuteCommand( self, verb, filename, param, directory, swmode=None ):

        def jobShellExecute( job_item ):
        
            _filename = filename
            _param = param
            _directory = directory

            if _param==None or len(_param)==0:
                _param = "%param%"
            
            joint_args = clnch_misc.joinArgs(job_item.args)

            _filename = clnch_misc.replaceMacro( _filename, { "%%":"%", "%param%":joint_args }, environ=True )
            _param = clnch_misc.replaceMacro( _param, { "%%":"%", "%param%":joint_args }, environ=True )
            _directory = clnch_misc.replaceMacro( _directory, { "%%":"%", "%param%":joint_args }, environ=True )
            
            try:
                pyauto.shellExecute( verb, _filename, _param, _directory, swmode )
            except Exception as e:
                print( 'Error : 実行に失敗' )
                print( "  %s" % str(e) )

        def jobShellExecuteFinished( job_item ):
            pass

        def command_ShellExecute(info):
            job_item = ckit.JobItem( jobShellExecute, jobShellExecuteFinished )
            job_item.args = info.args
            ckit.JobQueue.defaultQueue().enqueue(job_item)

        return command_ShellExecute

    # 互換目的。廃止予定
    def command_ShellExecute( self, verb, filename, param, directory, swmode=None ):
        print( 'Warning : "%s"は古い書式です。"%s"を使ってください。' % ("command_ShellExecute","ShellExecuteCommand") )
        return self.ShellExecuteCommand( verb, filename, param, directory, swmode )

    ## URLを開くコマンドオブジェクトを生成する
    #
    #  @param self          -
    #  @param url           URL
    #  @param encoding      URLの文字列のエンコーディング
    #
    def UrlCommand( self, url, encoding="utf8" ):

        def jobShellExecute( job_item ):
        
            _url = url
            
            if len(job_item.args) > 0 :
                import urllib.parse
                keyword = job_item.args[0].encode(encoding)
                keyword = urllib.parse.quote_plus(keyword)
            else:
                keyword = ""

            _url = clnch_misc.replaceMacro( _url, { "%%":"%", "%param%":keyword }, environ=False )

            pyauto.shellExecute( None, _url, "", "" )

        def jobShellExecuteFinished( job_item ):
            pass

        def command_URL(info):
            job_item = ckit.JobItem( jobShellExecute, jobShellExecuteFinished )
            job_item.args = info.args
            ckit.JobQueue.defaultQueue().enqueue(job_item)

        return command_URL

    # 互換目的。廃止予定
    def command_URL( self, url, encoding="utf8" ):
        print( 'Warning : "%s"は古い書式です。"%s"を使ってください。' % ("command_URL","UrlCommand") )
        return self.UrlCommand( url, encoding )

    ## コマンド履歴リストを開く
    #
    def command_History( self, info ):

        items = []
        
        for item in self.commandline_history:
            if item:
                items.append( ( item, ) )

        initial_select = 0
        max_width = clnch_ini.getint( "GEOMETRY", "max_width", 80 )

        def onKeyDown( vk, mod ):
            if vk==VK_DELETE and mod==0:
                select = list_window.getResult()
                self.commandline_history.remove(items[select][0])
                list_window.remove(select)
                return True

        def onStatusMessage( width, select ):
            return ""

        pos = self.centerOfWindowInPixel()
        list_window = clnch_listwindow.ListWindow( pos[0], pos[1], 5, 1, max_width, 16, self, False, "履歴リスト", items, initial_select=0, keydown_hook=onKeyDown, onekey_search=False, statusbar_handler=onStatusMessage )
        clnch_misc.adjustWindowPosition( self, list_window, default_up=True )
        list_window.show(True)
        self.enable(False)
        list_window.messageLoop()
        result = list_window.getResult()
        self.enable(True)
        self.activate()
        list_window.destroy()

        if result<0 : return

        text = items[result][0]
        
        self.activeMessageLoop( text, [ 0, len(text) ] )

    ## 入力中の文字列をコマンド履歴から削除する
    #
    def command_RemoveHistory( self, info ):
        self.commandline_edit.removeCandidate()

    ## コマンドのリストを開く
    #
    def command_CommandList( self, info ):

        items = []
        select = 0

        i=0
        while True:
            try:
                command_string = clnch_ini.get( "COMMANDLIST", "command_%d"%(i,) )
            except:
                break
        
            command_tuple = eval( command_string )
            items.append(command_tuple)

            i+=1

        while True:

            max_width = clnch_ini.getint( "GEOMETRY", "max_width", 80 )
            
            edit_new = [False]

            def onKeyDown( vk, mod ):
            
                if vk==VK_E and mod==0:
                    list_window.command.Enter()
                    return True

                elif vk==VK_E and mod==MODKEY_SHIFT:
                    edit_new[0] = True
                    list_window.command.Enter()
                    return True

                elif vk==VK_UP and mod==MODKEY_SHIFT:
                    select = list_window.getResult()
                    if select>0:
                        item = items[select]
                        del items[select]
                        select -= 1
                        items.insert( select, item )
                        list_window.command.CursorUp()

                elif vk==VK_DOWN and mod==MODKEY_SHIFT:
                    select = list_window.getResult()
                    if select<len(items)-1:
                        item = items[select]
                        del items[select]
                        select += 1
                        items.insert( select, item )
                        list_window.command.CursorDown()

                elif vk==VK_DELETE and mod==0:
                    select = list_window.getResult()
                    
                    result = clnch_msgbox.popMessageBox( list_window, clnch_msgbox.MSGBOX_TYPE_YESNO, "コマンドの削除", "[ %s ] を削除しますか？" % (items[select][0],) )
                    if result!=clnch_msgbox.MSGBOX_RESULT_YES : return True
                    
                    list_window.remove(select)
                    return True
                    
            def onStatusMessage( width, select ):
                return "Shift-E:新規  Shift-↑↓:移動"

            pos = self.centerOfWindowInPixel()
            list_window = clnch_listwindow.ListWindow( pos[0], pos[1], 32, 16, max_width, 16, self, False, "コマンドリスト", items, select, keydown_hook=onKeyDown, onekey_search=False, statusbar_handler=onStatusMessage )
            clnch_misc.adjustWindowPosition( self, list_window, default_up=True )
            list_window.show(True)
            self.enable(False)
            list_window.messageLoop()
            result = list_window.getResult()
            self.enable(True)
            self.activate()
            list_window.destroy()

            if result<0 : break
            
            select = result
            
            if edit_new[0]:
                edit_result = clnch_commandwindow.popCommandWindow( self, "", "", "", "" )
                if edit_result:
                    items.append( edit_result )
            else:
                edit_result = clnch_commandwindow.popCommandWindow( self, *items[result] )
                if edit_result:
                    items[result] = edit_result

        # iniファイルに反映させる
        clnch_ini.remove_section("COMMANDLIST")
        for i in range(len(items)):
            clnch_ini.set( "COMMANDLIST", "command_%d"%(i,), str(tuple(items[i])) )
        
        # 設定を再読み込みする
        self.configure()    

    ## 設定メニューを開く
    #
    def command_ConfigMenu( self, info ):
        clnch_configmenu.doConfigMenu(self)

    ## 設定ファイルをリロードする
    #
    def command_Reload( self, info ):
        self.configure()
        print( "設定スクリプトをリロードしました.\n" )

    ## コンソールウインドウを開く
    #
    def command_ConsoleOpen( self, info ):
        self.console_window.show(True)
        self.activate()

    ## コンソールウインドウを閉じる
    #
    def command_ConsoleClose( self, info ):
        self.console_window.show(False)

    ## コンソールウインドウの表示状態をトグルで切り替える
    #
    def command_ConsoleToggle( self, info ):
        if self.console_window.isVisible():
            self.command.ConsoleClose()
        else:
            self.command.ConsoleOpen()

    ## 自動補完をOnにする
    #
    def command_AutoCompleteOn( self, info ):
        if self.commandline_edit:
            print( "自動補完 ON\n" )
            self.commandline_edit.setAutoComplete(True)

    ## 自動補完をOffにする
    #
    def command_AutoCompleteOff( self, info ):
        if self.commandline_edit:
            print( "自動補完 OFF\n" )
            self.commandline_edit.setAutoComplete(False)

    ## 自動補完のOn/Offをトグルで切り替える
    #
    def command_AutoCompleteToggle( self, info ):
        if self.commandline_edit:
            if self.commandline_edit.getAutoComplete():
                self.command.AutoCompleteOff()
            else:    
                self.command.AutoCompleteOn()

    ## CraftLaunchのバージョン情報を表示する
    #
    def command_About( self, info ):
        print( clnch_resource.startupString() )

#--------------------------------------------------------------------

## @} mainwindow
