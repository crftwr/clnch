import os
import sys
from clnch import *


# 設定処理
def configure(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを起動する
    def command_Help(info):
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.cmd_keymap[ "F1" ] = command_Help

    # --------------------------------------------------------------------
    # Ctrl-E で、入力中のファイルパスを編集する
    window.cmd_keymap[ "C-E" ] = window.command.Edit

    # --------------------------------------------------------------------
    # Alt-Space で、自動補完を一時的にOn/Offする
    window.keymap[ "A-Space" ] = window.command.AutoCompleteToggle

    # --------------------------------------------------------------------
    # テキストエディタを設定する
    window.editor = "notepad.exe"

    # --------------------------------------------------------------------
    # ファイルタイプごとの動作設定
    window.association_list += [
        ( "*.mpg *.mpeg *.avi *.wmv", window.command_ShellExecute( None, "wmplayer.exe", "/prefetch:7 /Play %param%", "" ) ),
    ]

    # --------------------------------------------------------------------
    # 非アクティブ時の時計の形式
    if 1:
        # 年と秒を省略した短い形式
        window.clock_format = "%m/%d(%a) %H:%M"
    else:
        # 年月日(曜日) 時分秒 の全てを表示する
        window.clock_format = "%Y/%m/%d(%a) %H:%M:%S"

    # --------------------------------------------------------------------
    # 空欄コマンド
    #   コマンド名なしでEnterを押したときに実行されるコマンドです。
    #   この例では、ほかのアプリケーションをフォアグラウンド化するために使います。
    def command_QuickActivate(info):

        def callback( wnd, arg ):
            process_name, class_name = arg[0], arg[1]
            if (process_name==None or wnd.getProcessName()==process_name) and (class_name==None or wnd.getClassName()==class_name):
                wnd = wnd.getLastActivePopup()
                wnd.setForeground(True)
                return False
            return True

        if info.mod==MODKEY_SHIFT:
            pyauto.Window.enum( callback, ["cfiler.exe",None] )
        elif info.mod==MODKEY_CTRL:
            pyauto.Window.enum( callback, ["notepad.exe","Notepad"] )
        elif info.mod==MODKEY_SHIFT|MODKEY_CTRL:
            pyauto.Window.enum( callback, ["mintty.exe","MinTTY"] )

    window.launcher.command_list += [ ( "", command_QuickActivate ) ]

    # --------------------------------------------------------------------
    # "NetDrive" コマンド
    #   ネットワークドライブを割り当てるか解除を行います。
    #    NetDrive;L;\\server\share : \\machine\public を Lドライブに割り当てます
    #    NetDrive;L                : Lドライブの割り当てを解除します
    def command_NetDrive(info):
        
        if len(info.args)>=1:
            drive_letter = info.args[0]
            if len(info.args)>=2:
                path = info.args[1]
                checkNetConnection(path)
                if window.subProcessCall( [ "net", "use", drive_letter+":", os.path.normpath(path), "/yes" ], cwd=None, env=None, enable_cancel=False )==0:
                    print( "%s に %sドライブを割り当てました。" % ( path, drive_letter ) )
            else:
                if window.subProcessCall( [ "net", "use", drive_letter+":", "/D" ], cwd=None, env=None, enable_cancel=False )==0:
                    print( "%sドライブの割り当てを解除しました。" % ( drive_letter ) )
        else:
            print( "ドライブの割り当て : NetDrive;<ドライブ名>;<パス>" )
            print( "ドライブの解除     : NetDrive;<ドライブ名>" )

    # --------------------------------------------------------------------
    # コマンドを登録する
    window.launcher.command_list += [
        ( "NetDrive",  command_NetDrive ),
        ( "Cfiler",    window.command_ShellExecute( None, "C:/ols/cfiler/cfiler.exe", "", "" ) ),
        ( "Peggy",     window.command_ShellExecute( None, "C:/ols/anchor/peggy/peggypro.exe", "", "" ) ),
        ( "Becky",     window.command_ShellExecute( None, "C:/ols/becky/B2.exe", "", "" ) ),
        ( "FireFox",   window.command_ShellExecute( None, "C:/Program Files/Mozilla Firefox/firefox.exe", "", "C:/Program Files/Mozilla Firefox" ) ),
        ( "Google",    window.command_URL( "http://www.google.com/search?ie=utf8&q=%param%", encoding="utf8" ) ),
        ( "Eijiro",    window.command_URL( "http://eow.alc.co.jp/%param%/UTF-8/", encoding="utf8" ) ),
    ]


# リストウインドウの設定処理
def configure_ListWindow(window):

    # --------------------------------------------------------------------
    # F1 キーでヘルプファイルを表示する

    def command_Help(info):
        print( "Helpを起動 :" )
        help_path = os.path.join( getAppExePath(), 'doc\\index.html' )
        shellExecute( None, help_path, "", "" )
        print( "Done.\n" )

    window.keymap[ "F1" ] = command_Help

