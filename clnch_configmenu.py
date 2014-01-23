import os
import sys

import pyauto

import ckit
from ckit.ckit_const import *

import clnch_listwindow
import clnch_msgbox
import clnch_misc
import clnch_ini
import clnch_resource
import clnch_statusbar

#--------------------------------------------------------------------

def _configTheme( main_window ):

    def enumThemes():
        
        theme_list = []
        theme_parent = os.path.join( ckit.getAppExePath(), 'theme' )
        theme_dir_list = os.listdir(theme_parent)
        
        for theme_dir in theme_dir_list:
            
            if os.path.exists( os.path.join( theme_parent, theme_dir, "theme.ini" ) ):
                theme_list.append( theme_dir )
        
        return theme_list

    theme_list = enumThemes()

    current_theme_name = clnch_ini.get( "THEME", "name", "" )

    try:
        initial_select = theme_list.index(current_theme_name)
    except:
        initial_select = 0

    result = clnch_listwindow.popMenu( main_window, 40, 16, "テーマ", theme_list, initial_select )
    if result<0 : return

    clnch_ini.set( "THEME", "name", theme_list[result] )
    
    main_window.reloadTheme()
    
    return False

def _configFontName( main_window ):
    font_list = main_window.enumFonts()

    current_font_name = clnch_ini.get( "FONT", "name", "" )

    try:
        initial_select = font_list.index(current_font_name)
    except:
        initial_select = 0

    result = clnch_listwindow.popMenu( main_window, 40, 16, "フォント", font_list, initial_select )
    if result<0 : return

    clnch_ini.set( "FONT", "name", font_list[result] )
    
    main_window.updateFont()

def _configFontSize( main_window ):

    size_list = range(6,33)

    current_font_size = clnch_ini.getint( "FONT", "size", 12 )

    try:
        initial_select = size_list.index(current_font_size)
    except:
        initial_select = 0

    size_list = list(map( str, size_list ))

    result = clnch_listwindow.popMenu( main_window, 40, 16, "フォントサイズ", size_list, initial_select )
    if result<0 : return

    clnch_ini.set( "FONT", "size", size_list[result] )

    main_window.updateFont()

def _configMinWidth( main_window ):

    width_list = range(12,81)

    min_width = clnch_ini.getint( "GEOMETRY", "min_width", 18 )

    try:
        initial_select = width_list.index(min_width)
    except:
        initial_select = 0

    width_list = list(map( str, width_list ))

    result = clnch_listwindow.popMenu( main_window, 40, 16, "最小のウインドウサイズ", width_list, initial_select )
    if result<0 : return

    clnch_ini.set( "GEOMETRY", "min_width", width_list[result] )

def _configMaxWidth( main_window ):

    width_list = range(16,161)

    max_width = clnch_ini.getint( "GEOMETRY", "max_width", 80 )

    try:
        initial_select = width_list.index(max_width)
    except:
        initial_select = 0

    width_list = list(map( str, width_list ))

    result = clnch_listwindow.popMenu( main_window, 40, 16, "最大のウインドウサイズ", width_list, initial_select )
    if result<0 : return

    clnch_ini.set( "GEOMETRY", "max_width", width_list[result] )

def _configPosition( main_window ):

    result = clnch_msgbox.popMessageBox( main_window, clnch_msgbox.MSGBOX_TYPE_YESNO, "ウインドウ位置の保存の確認", "現在のウインドウ位置を保存しますか？" )
    if result!=clnch_msgbox.MSGBOX_RESULT_YES : return
    
    rect = list( main_window.getWindowRect() )
    
    monitor_info_list = pyauto.Window.getMonitorInfo()
    
    for i in range(len(monitor_info_list)):
        monitor_info = monitor_info_list[i]
        if monitor_info[0][0] <= rect[0] < monitor_info[0][2] and monitor_info[0][1] <= rect[1] < monitor_info[0][3]:
            if rect[2]>monitor_info[0][2]:
                delta = rect[2]-monitor_info[0][2]
                rect[0] -= delta
                rect[2] -= delta
            if rect[3]>monitor_info[0][3]:
                delta = rect[3]-monitor_info[0][3]
                rect[1] -= delta
                rect[3] -= delta
            break
    else:
        left = monitor_info_list[0][0][0]
        top  = monitor_info_list[0][0][1]
        rect = [ left, top, left+rect[2]-rect[0], top+rect[3]-rect[1] ]

    for i in range(len(monitor_info_list)):
        monitor_info = monitor_info_list[i]
        if monitor_info[0][0] <= rect[0] < monitor_info[0][2] and monitor_info[0][1] <= rect[1] < monitor_info[0][3]:
            
            clnch_ini.set( "GEOMETRY", "monitor", str(i) )
            
            if rect[0]-monitor_info[0][0] <= monitor_info[0][2]-rect[2]:
                # モニター左端からの相対位置
                clnch_ini.set( "GEOMETRY", "x", str(rect[0]-monitor_info[0][0]) )
            else:
                # モニター右端からの相対位置
                clnch_ini.set( "GEOMETRY", "x", str(rect[2]-monitor_info[0][2]-1) )

            if rect[1]-monitor_info[0][1] <= monitor_info[0][3]-rect[3]:
                # モニター上端からの相対位置
                clnch_ini.set( "GEOMETRY", "y", str(rect[1]-monitor_info[0][1]) )
            else:
                # モニター下端からの相対位置
                clnch_ini.set( "GEOMETRY", "y", str(rect[3]-monitor_info[0][3]-1) )
            
            break    

    clnch_msgbox.popMessageBox( main_window, clnch_msgbox.MSGBOX_TYPE_OK, "ウインドウ位置の保存完了", "ウインドウ位置を保存しました。" )

def _configTopMost( main_window ):

    items = []

    items.append( ( "通常", "0" ) )
    items.append( ( "最前面", "1" ) )
    items.append( ( "最前面のなかの最前面", "2" ) )

    topmost = clnch_ini.get( "GEOMETRY", "topmost", "0" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==topmost :
            initial_select = i
            break

    result = clnch_listwindow.popMenu( main_window, 40, 16, "ウインドウの最前面表示", items, initial_select )
    if result<0 : return

    clnch_ini.set( "GEOMETRY", "topmost", items[result][1] )
    main_window.updateTopMost()

def _configDirectorySeparator( main_window ):

    items = []

    items.append( ( "スラッシュ       : / ",  "slash" ) )
    items.append( ( "バックスラッシュ : \\ ", "backslash" ) )

    directory_separator = clnch_ini.get( "MISC", "directory_separator", "backslash" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==directory_separator:
            initial_select = i
            break

    result = clnch_listwindow.popMenu( main_window, 40, 16, "ディレクトリ区切り文字", items, initial_select )
    if result<0 : return

    clnch_ini.set( "MISC", "directory_separator", items[result][1] )

    if items[result][1]=="slash":
        ckit.setPathSlash(True)
    else:
        ckit.setPathSlash(False)

def _configKeyMap( main_window ):

    items = []

    items.append( ( "101キーボード", "101" ) )
    items.append( ( "106キーボード", "106" ) )

    default_keymap = clnch_ini.get( "MISC", "default_keymap", "106" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==default_keymap:
            initial_select = i
            break

    result = clnch_listwindow.popMenu( main_window, 40, 16, "キー割り当て", items, initial_select )
    if result<0 : return

    clnch_ini.set( "MISC", "default_keymap", items[result][1] )

    main_window.configure()

def _configAutoComplete( main_window ):

    items = []

    items.append( ( "自動補完しない", "0" ) )
    items.append( ( "自動補完する",   "1" ) )

    auto_complete = clnch_ini.get( "MISC", "auto_complete", "1" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==auto_complete:
            initial_select = i
            break

    result = clnch_listwindow.popMenu( main_window, 40, 16, "自動補完", items, initial_select )
    if result<0 : return

    clnch_ini.set( "MISC", "auto_complete", items[result][1] )

def _configHotKeyAssign( main_window ):

    RESULT_CANCEL = 0
    RESULT_OK     = 1

    class HotKeyWindow( ckit.Window ):

        def __init__( self, x, y, parent_window, show=True ):

            ckit.Window.__init__(
                self,
                x=x,
                y=y,
                width=29,
                height=2,
                origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
                parent_window=parent_window,
                show=show,
                bg_color = ckit.getColor("bg"),
                cursor0_color = ckit.getColor("cursor0"),
                cursor1_color = ckit.getColor("cursor1"),
                resizable = False,
                title = "ホットキー",
                minimizebox = False,
                maximizebox = False,
                cursor = True,
                close_handler = self.onClose,
                keydown_handler = self.onKeyDown,
                )

            self.setCursorPos( -1, -1 )

            self.result = RESULT_CANCEL

            activate_vk = clnch_ini.getint( "HOTKEY", "activate_vk", 0 )
            activate_mod = clnch_ini.getint( "HOTKEY", "activate_mod", 0 )

            self.activate_hotkey = ckit.HotKeyWidget( self, 0, 0, self.width(), 1, activate_vk, activate_mod )

            self.plane_statusbar = ckit.ThemePlane3x3( self, 'bar.png', 2 )
            client_rect = self.getClientRect()
            tmp, statusbar_top = self.charToClient( 0, self.height()-1 )
            self.plane_statusbar.setPosSize( 0, statusbar_top, client_rect[2]-0, client_rect[3]-statusbar_top )
            self.status_bar = clnch_statusbar.StatusBar()
            self.status_bar_layer = clnch_statusbar.SimpleStatusBarLayer()
            self.status_bar.registerLayer(self.status_bar_layer)

            self.updateStatusBar()

            self.paint()

        def onClose(self):
            self.result = RESULT_CANCEL
            self.quit()

        def onEnter(self):
            self.result = RESULT_OK
            self.quit()

        def onKeyDown( self, vk, mod ):
            if mod==0 and vk==VK_ESCAPE:
                self.result = RESULT_CANCEL
                self.quit()
            elif mod==0 and vk==VK_RETURN:
                self.result = RESULT_OK
                self.quit()
            else:
                self.activate_hotkey.onKeyDown( vk, mod )

        def updateStatusBar(self):
            self.status_bar_layer.setMessage("Return:決定  Esc:キャンセル")

        def paint(self):
            self.activate_hotkey.enableCursor(True)
            self.activate_hotkey.paint()

            self.status_bar.paint( self, 0, self.height()-1, self.width(), 1 )

        def getResult(self):
            if self.result:
                return [ self.activate_hotkey.getValue() ]
            else:
                return None


    pos = main_window.centerOfWindowInPixel()
    hotkey_window = HotKeyWindow( pos[0], pos[1], main_window, show=False )
    clnch_misc.adjustWindowPosition( main_window, hotkey_window, default_up=False )
    hotkey_window.show(True)
    main_window.enable(False)
    hotkey_window.messageLoop()
    result = hotkey_window.getResult()
    main_window.enable(True)
    main_window.activate()
    hotkey_window.destroy()

    if result==None : return

    clnch_ini.set( "HOTKEY", "activate_vk", str(result[0][0]) )
    clnch_ini.set( "HOTKEY", "activate_mod", str(result[0][1]) )

    main_window.updateHotKey()

def _configHotKeyBehavior( main_window ):

    items = []

    items.append( ( "アクティブ化",    "activate" ) )
    items.append( ( "トグル",          "toggle" ) )

    hotkey_behavior = clnch_ini.get( "MISC", "hotkey_behavior", "activate" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==hotkey_behavior :
            initial_select = i
            break

    result = clnch_listwindow.popMenu( main_window, 40, 16, "ホットキー動作設定", items, initial_select )
    if result<0 : return

    clnch_ini.set( "MISC", "hotkey_behavior", items[result][1] )
    main_window.updateHotKey()


def _editConfigFile( main_window ):
    info = ckit.CommandInfo()
    info.args = [ main_window.config_filename ]
    main_window.command.Edit(info)
    return False

def _reloadConfigFile( main_window ):
    main_window.configure()
    print( "設定スクリプトをリロードしました.\n" )
    return False

def _configAppearance( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "テーマ", _configTheme ) )
        items.append( ( "フォント名", _configFontName ) )
        items.append( ( "フォントサイズ", _configFontSize ) )
        items.append( ( "最小の横幅", _configMinWidth ) )
        items.append( ( "最大の横幅", _configMaxWidth ) )
        items.append( ( "表示位置の保存", _configPosition ) )
        items.append( ( "最前面に表示", _configTopMost ) )
        items.append( ( "ディレクトリ区切り文字", _configDirectorySeparator ) )

        select = clnch_listwindow.popMenu( main_window, 40, 16, "表示オプション", items, select )
        if select<0 : return

        loop_continue = items[select][1]( main_window )
        if loop_continue==False:
            return False

def _configInput( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "キー割り当て", _configKeyMap ) )
        items.append( ( "自動補完", _configAutoComplete ) )

        select = clnch_listwindow.popMenu( main_window, 40, 16, "入力オプション", items, select )
        if select<0 : return

        items[select][1]( main_window )

def _configHotKey( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "ホットキー割り当て", _configHotKeyAssign ) )
        items.append( ( "ホットキー動作設定", _configHotKeyBehavior ) )

        select = clnch_listwindow.popMenu( main_window, 40, 16, "ホットキー設定", items, select )
        if select<0 : return

        items[select][1]( main_window )

def _configInactive( main_window ):

    items = []

    items.append( ( "空欄",        "empty" ) )
    items.append( ( "時計",        "clock" ) )
    items.append( ( "非表示",      "hide" ) )

    inactive_behavior = clnch_ini.get( "MISC", "inactive_behavior", "clock" )

    initial_select = 0
    for i in range(len(items)):
        if items[i][1]==inactive_behavior :
            initial_select = i
            break

    result = clnch_listwindow.popMenu( main_window, 40, 16, "非アクティブ時の動作", items, initial_select )
    if result<0 : return

    clnch_ini.set( "MISC", "inactive_behavior", items[result][1] )
    main_window.updateInactiveBehavior()

def doConfigMenu( main_window ):

    select = 0
    
    while True:

        items = []

        items.append( ( "表示オプション",       _configAppearance ) )
        items.append( ( "入力オプション",       _configInput ) )
        items.append( ( "ホットキー設定",       _configHotKey ) )
        items.append( ( "非アクティブ時の動作", _configInactive ) )
        items.append( ( "config.py を編集",     _editConfigFile ) )
        items.append( ( "config.py をリロード", _reloadConfigFile ) )

        select = clnch_listwindow.popMenu( main_window, 40, 16, "設定メニュー", items, select )
        if select<0 : return

        loop_continue = items[select][1]( main_window )
        if loop_continue==False:
            return
