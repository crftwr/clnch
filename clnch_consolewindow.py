import os
import sys
import threading
from PIL import Image

import pyauto

import ckit
from ckit.ckit_const import *

import clnch_misc
import clnch_ini
import clnch_resource

#--------------------------------------------------------------------
# ログ

class Log:

    def __init__(self):
        self.lock = threading.Lock()
        self.log = [""]
        self.last_line_terminated = False

    def write(self,s):
        self.lock.acquire()
        try:
            while True:
                return_pos = s.find("\n")
                if return_pos < 0 : break
                if self.last_line_terminated:
                    self.log.append("")
                self.log[-1] += s[:return_pos]
                s = s[return_pos+1:]
                self.last_line_terminated = True
            if len(s)>0 :
                if self.last_line_terminated:
                    self.log.append("")
                self.log[-1] += s
                self.last_line_terminated = False
            if len(self.log)>1000:
                self.log = self.log[-1000:]
        finally:
            self.lock.release()

    def numLines(self):
        return len(self.log)

    def getLine(self,lineno):
        try:
            return self.log[lineno]
        except IndexError:
            return ""

#--------------------------------------------------------------------
# コンソールウインドウ

class ConsoleWindow(ckit.TextWindow):
    
    def __init__( self, parent_window, debug=False ):
    
        self.initialized = False
        
        self.loadState()
        
        self.parent_window = parent_window
        
        self.active = False

        ckit.TextWindow.__init__(
            self,
            x = self.window_normal_x,
            y = self.window_normal_y,
            width = self.window_normal_width,
            height = self.window_normal_height,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            border_size = 2,
            title_bar = True,
            title = clnch_resource.clnch_appname,
            show = False,
            activate_handler = self._onActivate,
            close_handler = self._onClose,
            move_handler = self._onMove,
            size_handler = self._onSize,
            keydown_handler = self._onKeyDown,
            #char_handler = self._onChar,

            lbuttondown_handler = self._onLeftButtonDown,
            lbuttonup_handler = self._onLeftButtonUp,
            mbuttondown_handler = self._onMiddleButtonDown,
            mbuttonup_handler = self._onMiddleButtonUp,
            rbuttondown_handler = self._onRightButtonDown,
            rbuttonup_handler = self._onRightButtonUp,
            lbuttondoubleclick_handler = self._onLeftButtonDoubleClick,
            mousemove_handler = self._onMouseMove,
            mousewheel_handler= self._onMouseWheel,
            )

        self.plane_scrollbar0 = ckit.ThemePlane3x3( self, 'scrollbar0.png', 2 )
        self.plane_scrollbar1 = ckit.ThemePlane3x3( self, 'scrollbar1.png', 1 )

        self.debug = debug

        self.log = Log()
        self.scroll_info = ckit.ScrollInfo()
        
        self.mouse_click_info = None
        self.selection = [ [ 0, 0 ], [ 0, 0 ] ]
        
        self.auto_show = False
        self.auto_show_required = False
        self.setTimer( self.onTimerAutoShow, 10 )

        self.initialized = True
    
        self.paint()

    #--------------------------------------------------------------------------
    # 自動表示／非表示
    
    def show( self, show, activate=True ):
        clnch_misc.adjustWindowPosition( self.parent_window, self, default_up=True )
        ckit.TextWindow.show( self, show, activate )

    def setAutoShow( self, auto_show ):
        self.auto_show = auto_show
        
    def onTimerAutoShow(self):
        if self.auto_show_required:
            self.auto_show_required = False
            self.show(True,False)

    #--------------------------------------------------------------------------
    # 領域
    
    def rectText(self):
        return [ 0, 0, self.width()-2, self.height() ]

    def rectScrollbar(self):
        return [ self.width()-2, 0, 2, self.height() ]

    #--------------------------------------------------------------------------
    # イベントハンドラ

    def _onActivate( self, active ):
        self.active = active

    def _onClose(self):
        self.show(False)

    def _onMove( self, x, y ):

        if not self.isMaximized() and not self.isMinimized():
            self.window_normal_x = x
            self.window_normal_y = y

    def _onSize( self, width, height ):

        if not self.isMaximized() and not self.isMinimized():
            self.window_normal_width = width
            self.window_normal_height = height

        self.paint()

    def _onKeyDown( self, vk, mod ):
        
        if vk==VK_ESCAPE and mod==0:
            self.show(False)

        elif vk==VK_UP and mod==0:
            self._scroll(-1)
            self.paint()

        elif vk==VK_DOWN and mod==0:
            self._scroll(1)
            self.paint()

        elif ( vk==VK_PRIOR or vk==VK_LEFT ) and mod==0:
            rect = self.rectText()
            self._scroll( -(rect[3]-rect[1]) )
            self.paint()

        elif ( vk==VK_NEXT or vk==VK_RIGHT ) and mod==0:
            rect = self.rectText()
            self._scroll( rect[3]-rect[1] )
            self.paint()

        elif vk==VK_F1 and mod==0:
            def jobHelp(job_item):
                help_path = os.path.join( ckit.getAppExePath(), 'doc\\index.html' )
                pyauto.shellExecute( None, help_path, "", "" )

            def jobHelpFinished(job_item):
                print( "Helpを開きました" )
                print( "" )
            
            job_item = ckit.JobItem( jobHelp, jobHelpFinished )
            ckit.JobQueue.defaultQueue().enqueue(job_item)

    def _mousePosToCharPos( self, x, y ):
        client_rect = self.getClientRect()
        offset_x, offset_y = self.charToClient( 0, 0 )
        char_w, char_h = self.getCharSize()
        char_x = (x-offset_x) // char_w
        char_y = (y-offset_y) // char_h
        return char_x, char_y

    def _mousePosToLogPos( self, x, y ):
        char_x, char_y = self._mousePosToCharPos(x,y)

        char_x = max(char_x,0)
        char_x = min(char_x,self.width())

        if char_y < 0:
            char_x = 0
            char_y = 0

        if char_y > self.height():
            char_x = self.width()
            char_y = self.height()

        lineno = self.scroll_info.pos+char_y

        s = self.log.getLine(lineno)
        
        w = 0
        char_index = 0
        for char_index in range(len(s)):
            w += self.getStringWidth(s[char_index])
            if w > char_x : break
        else:
            char_index = len(s)
        
        return lineno, char_index

    def _copySelectedRegion(self):
        
        joint_text = ""
        
        selection_left, selection_right = self.selection 
        if selection_left > selection_right:
            selection_left, selection_right = selection_right, selection_left

        i = selection_left[0]
        while i<=selection_right[0] and i<self.log.numLines():
        
            s = self.log.getLine(i)

            if i==selection_left[0]:
                left = selection_left[1]
            else:
                left = 0

            if i==selection_right[0]:
                right = selection_right[1]
            else:
                right = len(s)
            
            joint_text += s[left:right]
            
            if i!=selection_right[0]:
                joint_text += "\r\n"
            
            i += 1    
        
        if joint_text:
            ckit.setClipboardText(joint_text)

    def _onLeftButtonDown( self, x, y, mod ):

        lineno, char_index = self._mousePosToLogPos(x,y)
        
        self.mouse_click_info = [ False, x, y, lineno, char_index ]
        self.setCapture()

        self.selection = [
            [ lineno, char_index ],
            [ lineno, char_index ]
            ]
        self.paint()    

    def _onLeftButtonUp( self, x, y, mod ):
        self.mouse_click_info = None
        self.releaseCapture()
        self._copySelectedRegion()

    def _onMiddleButtonDown( self, x, y, mod ):
        self.mouse_click_info = None

    def _onMiddleButtonUp( self, x, y, mod ):
        self.mouse_click_info = None

    def _onRightButtonDown( self, x, y, mod ):
        self.mouse_click_info = None

    def _onRightButtonUp( self, x, y, mod ):
        self.mouse_click_info = None

    def _wordbreak( self, s, pos, step ):

        word_break_chars1 = "\"!@#$%^&*()+|~-=\`[]{};:',./<>?"
        word_break_chars2 = " \t"

        while True:
            if pos<=0 : return 0
            if pos>=len(s) : return len(s)

            if s[pos-1] in word_break_chars1:
                left_char_type = 1
            elif s[pos-1] in word_break_chars2:
                left_char_type = 2
            else:
                left_char_type = 0

            if s[pos] in word_break_chars1:
                right_char_type = 1
            elif s[pos] in word_break_chars2:
                right_char_type = 2
            else:
                right_char_type = 0

            if left_char_type!=0:
                if right_char_type==0:
                    return pos

            pos += step

    def _onLeftButtonDoubleClick( self, x, y, mod ):

        lineno, char_index = self._mousePosToLogPos(x,y)
        
        s = self.log.getLine(lineno)

        left = max( self._wordbreak( s, char_index, -1 ), 0 )
        right = min( self._wordbreak( s, char_index+1, +1 ), len(s) )

        self.mouse_click_info = [ True, x, y, lineno, left, lineno, right ]
        self.setCapture()

        self.selection = [
            [ lineno, left ],
            [ lineno, right ]
            ]
            
        self.paint()    

    def _onMouseMove( self, x, y, mod ):
    
        if self.mouse_click_info:
        
            char_x, char_y = self._mousePosToCharPos(x,y)

            if char_y < 0:
                self._scroll(-1)
            elif char_y >= self.height():
                self._scroll(1)

            lineno, char_index = self._mousePosToLogPos(x,y)

            double_click = self.mouse_click_info[0]
            if double_click:
                
                s = self.log.getLine(lineno)
                
                if [ lineno, char_index ] > self.selection[0]:
                    right = min( self._wordbreak( s, char_index+1, +1 ), len(s) )
                    self.selection[0] = self.mouse_click_info[3:5]
                    self.selection[1] = [ lineno, right ]
                else:    
                    left = max( self._wordbreak( s, char_index, -1 ), 0 )
                    self.selection[0] = self.mouse_click_info[5:7]
                    self.selection[1] = [ lineno, left ]
            
            else:
                self.selection[1] = [ lineno, char_index ]

            self.paint()

    def _scroll( self, delta ):
        self.scroll_info.pos += delta
        self.scroll_info.pos = min( self.scroll_info.pos, self.log.numLines()-self.height() )
        self.scroll_info.pos = max( self.scroll_info.pos, 0 )

    def _onMouseWheel( self, x, y, wheel, mod ):

        while wheel>0:
            self._scroll(-1)
            wheel-=1
        while wheel<0:
            self._scroll(+1)
            wheel+=1

        self.paint()

    #--------------------------------------------------------------------------
    # 標準出力の置き換え

    def registerStdio(self):
    
        def writeCommon(s):
            make_visible = False
            if self.log.numLines()-1 < self.scroll_info.pos + self.height():
                make_visible = True
        
            self.log.write(s)

            if make_visible:
                self.scroll_info.makeVisible( self.log.numLines()-1, self.height() )

            self.paint()
            
        class Stdout:
            def write( writer_self, s ):
                writeCommon(s)
                if self.auto_show:
                    self.auto_show_required = True
                
        class Stderr:
            def write( writer_self, s ):
                writeCommon(s)
                if self.auto_show:
                    self.auto_show_required = True

        if not self.debug:
            sys.stdout = Stdout()
            sys.stderr = Stderr()

    def unregisterStdio(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    #--------------------------------------------------------------------------

    def updateFont(self):
        self.setFontFromFontObject( self.parent_window.getFont() )
        window_rect = self.getWindowRect()
        self.setPosSize( window_rect[0], window_rect[1], self.width(), self.height(), 0 )

    def updateColor(self):
        self.setBGColor( ckit.getColor("bg") )
        self.setCursorColor( ckit.getColor("cursor0"), ckit.getColor("cursor1") )
        self.paint()

    #--------------------------------------------------------------------------
    # 描画

    def paint(self):
    
        # テキスト
        if 1:
            x, y, width, height = self.rectText()
    
            attr = ckit.Attribute( fg=ckit.getColor("fg") )
            attr_selected = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg") )
        
            selection_left, selection_right = self.selection 
            if selection_left > selection_right:
                selection_left, selection_right = selection_right, selection_left
        
            for i in range(height):

                if self.scroll_info.pos+i < self.log.numLines():
            
                    if selection_left[0] <= self.scroll_info.pos+i <= selection_right[0]:
                    
                        s = self.log.getLine( self.scroll_info.pos + i )
                    
                        if selection_left[0]==self.scroll_info.pos+i:
                            left = selection_left[1]
                        else:
                            left = 0

                        if selection_right[0]==self.scroll_info.pos+i:
                            right = selection_right[1]
                        else:
                            right = len(s)
                    
                        s = [ s[0:left], s[left:right], s[right:len(s)] ]
                    
                        line_x = x

                        self.putString( line_x, y+i, width-line_x, 1, attr, s[0] )
                        line_x += self.getStringWidth(s[0])

                        self.putString( line_x, y+i, width-line_x, 1, attr_selected, s[1] )
                        line_x += self.getStringWidth(s[1])
                    
                        self.putString( line_x, y+i, width-line_x, 1, attr, s[2] )
                        line_x += self.getStringWidth(s[2])

                        self.putString( line_x, y+i, width-line_x, 1, attr, " " * (width-line_x) )
                    
                    else:
                        s = self.log.getLine( self.scroll_info.pos + i )
                        self.putString( x, y+i, width, 1, attr, s )
                        w = self.getStringWidth(s)
                        space_x = x + w
                        space_width = width - w
                        self.putString( space_x, y+i, space_width, 1, attr, " " * space_width )
                else:
                    self.putString( x, y+i, width, 1, attr, " " * width )

        # スクロールバー
        if 1:
            x, y, width, height = self.rectScrollbar()

            for i in range(height):
                self.putString( x, y+i, width, 1, attr, " " * width )

            client_rect = self.getClientRect()
            scrollbar_left, tmp = self.charToClient( self.width()-2, 0 )
            
            scrollbar0_rect = [ scrollbar_left, 0, client_rect[2]-scrollbar_left, client_rect[3]-0 ]
            
            scrollbar1_height = client_rect[3] * self.height() // self.log.numLines()
            scrollbar1_height = min( scrollbar1_height, client_rect[3] )
            scrollbar1_height = max( scrollbar1_height, 12 )
            
            scrollbar1_pos = (client_rect[3]-scrollbar1_height) * self.scroll_info.pos // max((self.log.numLines()-self.height()),1)
            
            scrollbar1_rect = [ scrollbar_left, scrollbar1_pos, client_rect[2]-scrollbar_left, scrollbar1_height ]

            self.plane_scrollbar0.setPosSize( *scrollbar0_rect )
            self.plane_scrollbar1.setPosSize( *scrollbar1_rect )

    #--------------------------------------------------------------------------
    # 状態の保存と復帰

    def loadState(self):
        self.window_normal_x = clnch_ini.getint( "CONSOLE", "x", 0 )
        self.window_normal_y = clnch_ini.getint( "CONSOLE", "y", 0 )
        self.window_normal_width = clnch_ini.getint( "CONSOLE", "width", 80 )
        self.window_normal_height = clnch_ini.getint( "CONSOLE", "height", 32 )
    
    def saveState(self):
        clnch_ini.set( "CONSOLE", "x", str(self.window_normal_x) )
        clnch_ini.set( "CONSOLE", "y", str(self.window_normal_y) )
        clnch_ini.set( "CONSOLE", "width", str(self.window_normal_width) )
        clnch_ini.set( "CONSOLE", "height", str(self.window_normal_height) )

    #--------------------------------------------------------------------------
    # ログのクリア

    def clearLog(self):
        self.log = Log()
        self.scroll_info = ckit.ScrollInfo()
        self.mouse_click_info = None
        self.selection = [ [ 0, 0 ], [ 0, 0 ] ]
        self.paint()

        