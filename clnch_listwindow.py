import sys
import os

import ckit
from ckit.ckit_const import *

import clnch_isearch
import clnch_statusbar
import clnch_misc

## @addtogroup listwindow リストウインドウ機能
## @{

#--------------------------------------------------------------------

## リストウインドウ
#
#  各種のリスト形式ウインドウを実現しているクラスです。
#  
#  設定ファイル config.py の configure_ListWindow に渡される window 引数は、ListWindow クラスのオブジェクトです。
#
class ListWindow( ckit.Window ):

    def __init__( self, x, y, min_width, min_height, max_width, max_height, parent_window, show=True, title="", items=[], initial_select=0, onekey_search=True, onekey_decide=False, return_modkey=False, keydown_hook=None, statusbar_handler=None ):

        self.active = False

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=5,
            height=5,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            show = False,
            resizable = False,
            title = title,
            minimizebox = False,
            maximizebox = False,
            activate_handler = self.onActivate,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        max_item_width = 0
        for item in items:
            if isinstance(item,list) or isinstance(item,tuple):
                item = item[0]
            item_width = self.getStringWidth(item)
            if item_width>max_item_width:
                max_item_width=item_width

        window_width = max_item_width
        window_height = len(items)
        
        if statusbar_handler:
            window_height += 1
        
        window_width = min(window_width,max_width)
        window_height = min(window_height,max_height)

        window_width = max(window_width,min_width)
        window_height = max(window_height,min_height)

        self.setPosSize(
            x=x,
            y=y,
            width=window_width,
            height=window_height,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER
            )
        self.show(show)

        self.command = ckit.CommandMap(self)

        self.title = title
        self.items = items
        self.scroll_info = ckit.ScrollInfo()
        self.select = initial_select
        self.result_mod = 0
        self.onekey_search = onekey_search
        self.onekey_decide = onekey_decide
        self.return_modkey = return_modkey
        self.keydown_hook = keydown_hook
        self.statusbar_handler = statusbar_handler

        self.status_bar = None
        self.status_bar_layer = None
        self.plane_statusbar = None

        self.isearch = None
        self.plane_statusbar = None
        
        if statusbar_handler:
            self.status_bar = clnch_statusbar.StatusBar()
            self.status_bar_layer = clnch_statusbar.SimpleStatusBarLayer()
            self.status_bar.registerLayer(self.status_bar_layer)

            self.plane_statusbar = ckit.ThemePlane3x3( self, 'bar.png' )
            client_rect = self.getClientRect()
            pos1 = self.charToClient( 0, self.height()-1 )
            char_w, char_h = self.getCharSize()
            self.plane_statusbar.setPosSize( pos1[0]-char_w//2, pos1[1], self.width()*char_w+char_w, client_rect[3]-pos1[1] )
            self.plane_statusbar.show(True)

            self.plane_statusbar = ckit.ThemePlane3x3( self, 'isearch.png', 1 )
            self.plane_statusbar.setPosSize( pos1[0]-char_w//2, pos1[1], self.width()*char_w+char_w, client_rect[3]-pos1[1] )
            self.plane_statusbar.show(False)

        self.scroll_info.makeVisible( self.select, self.itemsHeight() )
        
        self.configure()
        
        self.paint()

    ## 設定を読み込む
    #
    #  キーマップなどをリセットした上で、config,py の configure_ListWindow() を呼び出します。
    #
    def configure(self):
        self.keymap = ckit.Keymap()
        self.keymap[ "Up" ] = self.command.CursorUp
        self.keymap[ "Down" ] = self.command.CursorDown
        self.keymap[ "PageUp" ] = self.command.CursorPageUp
        self.keymap[ "PageDown" ] = self.command.CursorPageDown
        self.keymap[ "Return" ] = self.command.Enter
        self.keymap[ "Escape" ] = self.command.Cancel
        if not self.onekey_search:
            self.keymap[ "F" ] = self.command.IncrementalSearch
        ckit.callConfigFunc("configure_ListWindow",self)

    ## リストの項目を１つ削除する
    #
    #  @param self  -
    #  @param index 削除する項目のインデックス
    #
    def remove( self, index ):
        
        del self.items[index]
        
        if self.select > index:
            self.select -= 1
        
        if not len(self.items):
            self.select = -1
            self.quit()
            return

        if self.select<0 : self.select=0
        if self.select>len(self.items)-1 : self.select=len(self.items)-1

        self.paint()

    def onActivate(self,active):
        self.active = active
        self.paint()

    def onClose(self):
        self.quit()

    def onKeyDown( self, vk, mod ):

        if self.keydown_hook:
            if self.keydown_hook( vk, mod ):
                return True

        try:
            func = self.keymap.table[ ckit.KeyEvent(vk,mod) ]
        except KeyError:
            return

        self.result_mod = mod
        func( ckit.CommandInfo() )

        return True

    def onChar( self, ch, mod ):

        if self.onekey_search:
        
            if 0x20<=ch<0x100:
                if not len(self.items): return

                found = []
                
                for i in range( self.select+1, len(self.items) ):

                    item = self.items[i]
                    if isinstance(item,list) or isinstance(item,tuple):
                        item = item[0]

                    if item[0].upper()==chr(ch).upper():
                        found.append(i)
                        if len(found)>=2 : break

                if len(found)<2 :
                    for i in range( self.select+1 ):

                        item = self.items[i]
                        if isinstance(item,list) or isinstance(item,tuple):
                            item = item[0]

                        if item[0].upper()==chr(ch).upper():
                            found.append(i)
                            if len(found)>=2 : break

                if found:
                    if self.onekey_decide and len(found)==1:
                        self.select = found[0]
                        self.result_mod = mod
                        self.quit()
                    else:
                        self.select = found[0]
                        self.scroll_info.makeVisible( self.select, self.itemsHeight() )
                        self.paint()

        else:
            
            if self.isearch:

                if ch==ord('\b'):
                    isearch_newvalue = self.isearch.isearch_value[:-1]
                elif ch==ord(' '):
                    return
                else:
                    isearch_newvalue = self.isearch.isearch_value + chr(ch)

                accept = False

                item = self.items[self.select]
                if isinstance(item,list) or isinstance(item,tuple):
                    item = item[0]
            
                if self.isearch.fnmatch( item, isearch_newvalue ):
                    accept = True
                else:
                
                    if self.isearch.isearch_type=="inaccurate":
                        isearch_type_list = [ "strict", "partial", "inaccurate" ]
                    else:
                        isearch_type_list = [ "strict", "partial", "migemo" ]
                
                    last_type_index = isearch_type_list.index(self.isearch.isearch_type)
                    for isearch_type_index in range(last_type_index+1):
                        for i in range( len(self.items) ):
                        
                            item = self.items[i]
                            if isinstance(item,list) or isinstance(item,tuple):
                                item = item[0]
                        
                            if self.isearch.fnmatch( item, isearch_newvalue, isearch_type_list[isearch_type_index] ):
                                self.select = i
                                self.scroll_info.makeVisible( self.select, self.itemsHeight() )
                                accept = True
                                break
                        if accept: break
        
                if accept:
                    self.isearch.isearch_value = isearch_newvalue
                    self.paint()


    def itemsHeight(self):
        if self.status_bar:
            return self.height()-1
        else:
            return self.height()

    def paint(self):

        x=0
        y=0
        width=self.width()
        height=self.itemsHeight()

        attribute_normal = ckit.Attribute( fg=ckit.getColor("fg") )
        attribute_normal_selected = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg") )
        
        for i in range(height):
            index = self.scroll_info.pos+i
            if index < len(self.items):

                item = self.items[index]
                if isinstance(item,list) or isinstance(item,tuple):
                    item = item[0]

                if self.active and self.select==index:
                    attr=attribute_normal_selected
                else:
                    attr=attribute_normal
                self.putString( x, y+i, width, 1, attr, " " * width )
                self.putString( x, y+i, width, 1, attr, item )
            else:
                self.putString( x, y+i, width, 1, attribute_normal, " " * width )

        if self.status_bar:
            if self.isearch:
                attr = ckit.Attribute( fg=ckit.getColor("fg") )
                s = " Search : %s_" % ( self.isearch.isearch_value )
                s = ckit.adjustStringWidth(self,s,width-1)
                self.putString( 0, self.height()-1, width-1, 1, attr, s )
            else:
                self.status_bar_layer.setMessage( self.statusbar_handler( width, self.select ) )
                self.status_bar.paint( self, 0, self.height()-1, width, 1 )
        else:
            if self.isearch:
                s = " Search : %s_" % ( self.isearch.isearch_value )
                self.setTitle(s)
            else:
                self.setTitle(self.title)

    def getResult(self):
        if self.return_modkey:
            return self.select, self.result_mod
        else:
            return self.select

    ## リストウインドウをキャンセルして閉じる
    def cancel(self):
        self.select = -1
        self.quit()

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

    ## カーソルを1つ上に移動させる
    def command_CursorUp( self, info ):
        self.select -= 1
        if self.select<0 : self.select=0
        self.scroll_info.makeVisible( self.select, self.itemsHeight() )
        self.paint()

    ## カーソルを1つ下に移動させる
    def command_CursorDown( self, info ):
        self.select += 1
        if self.select>len(self.items)-1 : self.select=len(self.items)-1
        self.scroll_info.makeVisible( self.select, self.itemsHeight() )
        self.paint()

    ## 1ページ上方向にカーソルを移動させる
    def command_CursorPageUp( self, info ):
        if self.isearch:
            return
        if self.select>self.scroll_info.pos :
            self.select = self.scroll_info.pos
        else:
            self.select -= self.itemsHeight()
            if self.select<0 : self.select=0
            self.scroll_info.makeVisible( self.select, self.itemsHeight() )
        self.paint()

    ## 1ページ下方向にカーソルを移動させる
    def command_CursorPageDown( self, info ):
        if self.isearch:
            return
        if self.select<self.scroll_info.pos+self.itemsHeight()-1:
            self.select = self.scroll_info.pos+self.itemsHeight()-1
        else:
            self.select += self.itemsHeight()
        if self.select>len(self.items)-1 : self.select=len(self.items)-1
        self.scroll_info.makeVisible( self.select, self.itemsHeight() )
        self.paint()

    ## 決定する
    def command_Enter( self, info ):
        self.quit()

    ## キャンセルする
    def command_Cancel( self, info ):
        self.cancel()

    ## インクリメンタルサーチを行う
    def command_IncrementalSearch( self, info ):
        
        def finish():
            if self.plane_statusbar:
                self.plane_statusbar.show(False)
            self.isearch = None
            self.keydown_hook = self.keydown_hook_old
            self.scroll_info.makeVisible( self.select, self.itemsHeight() )
            self.paint()

        def getString(i):
            item = self.items[i]
            if isinstance(item,list) or isinstance(item,tuple):
                item = item[0]
            return item    

        def cursorUp():
            self.select = self.isearch.cursorUp( getString, len(self.items), self.select, self.scroll_info.pos, self.itemsHeight() )
            self.scroll_info.makeVisible( self.select, self.itemsHeight() )
            self.paint()

        def cursorDown():
            self.select = self.isearch.cursorDown( getString, len(self.items), self.select, self.scroll_info.pos, self.itemsHeight() )
            self.scroll_info.makeVisible( self.select, self.itemsHeight() )
            self.paint()

        def cursorPageUp():
            self.select = self.isearch.cursorPageUp( getString, len(self.items), self.select, self.scroll_info.pos, self.itemsHeight() )
            self.scroll_info.makeVisible( self.select, self.itemsHeight() )
            self.paint()

        def cursorPageDown():
            self.select = self.isearch.cursorPageDown( getString, len(self.items), self.select, self.scroll_info.pos, self.itemsHeight() )
            self.scroll_info.makeVisible( self.select, self.itemsHeight() )
            self.paint()

        def onKeyDown( vk, mod ):

            if vk==VK_RETURN:
                finish()
            elif vk==VK_ESCAPE:
                finish()
            elif vk==VK_UP:
                cursorUp()
            elif vk==VK_DOWN:
                cursorDown()
            elif vk==VK_PRIOR:
                cursorPageUp()
            elif vk==VK_NEXT:
                cursorPageDown()

            return True
    
        self.removeKeyMessage()

        self.isearch = clnch_isearch.IncrementalSearch()
        self.keydown_hook_old = self.keydown_hook
        self.keydown_hook = onKeyDown
        if self.plane_statusbar:
            self.plane_statusbar.show(True)
        self.scroll_info.makeVisible( self.select, self.itemsHeight() )
        self.paint()

## ポップアップメニューを表示する
#
#  @param main_window       MainWindowオブジェクト
#  @param max_width         メニューウインドウの最大幅 (文字数単位)
#  @param max_height        メニューウインドウの最大高さ (文字数単位)
#  @param title             メニューウインドウのタイトルバーに表示する文字列
#  @param items             メニューに表示するアイテムのリスト
#  @param initial_select    初期選択位置
#  @param onekey_search     文字入力で項目の先頭文字を検索するか
#  @param onekey_decide     先頭文字の検索で候補が1つだけだったとき即時決定するか
#  @param return_modkey     メニューが閉じたときに押されていたモディファイアキーを取得するか
#  @param keydown_hook      キー入力イベントのフック
#  @param statusbar_handler ステータスバーに表示する文字列を返すハンドラ
#
#  @return                  引数 return_modkey が False の場合は結果値 (選択されたアイテムのインデックスか、キャンセルされた場合は-1)、引数 return_modkey が True の場合は ( 結果値, モディファイアキーの状態 ) を返す。
#
#  引数 items には、( 表示名, ... ) 形式のアイテムをリストに格納して渡します。[ ... ] の部分には、どのようなデータが入ってもかまいません。
#
#  onekey_search に True を渡したときは、キー入力で項目の先頭文字を検索します。onekey_search に False を渡したときは、F キーでインクリメンタルサーチが開始します。
#
#  statusbar_handler にハンドラを渡したときは、ステータスバーが表示されます。
#
#  インクリメンタルサーチの検索パターンは、ステータスバーが有効な場合はステータスバーに表示され、ステータスバーが無効な場合はタイトルバーに表示されます。
#
def popMenu( main_window, max_width=None, max_height=None, title="", items=[], initial_select=0, onekey_search=True, onekey_decide=False, return_modkey=False, keydown_hook=None, statusbar_handler=None ):
    pos = main_window.centerOfWindowInPixel()
    list_window = ListWindow( pos[0], pos[1], 5, 1, max_width, max_height, main_window, False, title, items, initial_select=initial_select, onekey_search=onekey_search, onekey_decide=onekey_decide, return_modkey=return_modkey, keydown_hook=keydown_hook, statusbar_handler=statusbar_handler )
    clnch_misc.adjustWindowPosition( main_window, list_window, default_up=False )
    list_window.show(True)
    main_window.enable(False)
    list_window.messageLoop()
    result = list_window.getResult()
    main_window.enable(True)
    main_window.activate()
    list_window.destroy()
    return result

## @} listwindow
