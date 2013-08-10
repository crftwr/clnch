import ckit
from ckit.ckit_const import *

import clnch_misc

#--------------------------------------------------------------------

COMMANDWINDOW_RESULT_CANCEL = 0
COMMANDWINDOW_RESULT_OK     = 1

#--------------------------------------------------------------------

class CommandWindow( ckit.Window ):

    FOCUS_NAME = 0
    FOCUS_FILE = 1
    FOCUS_PARAM = 2
    FOCUS_DIRECTORY = 3

    def __init__( self, x, y, parent_window, name, file, param, directory ):

        ckit.Window.__init__(
            self,
            x=x,
            y=y,
            width=80,
            height=9,
            origin= ORIGIN_X_CENTER | ORIGIN_Y_CENTER,
            parent_window=parent_window,
            bg_color = ckit.getColor("bg"),
            cursor0_color = ckit.getColor("cursor0"),
            cursor1_color = ckit.getColor("cursor1"),
            show = False,
            resizable = False,
            title = "Command",
            minimizebox = False,
            maximizebox = False,
            cursor = True,
            close_handler = self.onClose,
            keydown_handler = self.onKeyDown,
            char_handler = self.onChar,
            )

        self.setCursorPos( -1, -1 )

        self.focus = CommandWindow.FOCUS_NAME
        self.result = COMMANDWINDOW_RESULT_CANCEL

        self.name_edit      = ckit.EditWidget( self, 16, 1, self.width()-18, 1, name, [ 0, len(name) ] )
        self.file_edit      = ckit.EditWidget( self, 16, 3, self.width()-18, 1, file, [ 0, len(file) ] )
        self.param_edit     = ckit.EditWidget( self, 16, 5, self.width()-18, 1, param, [ 0, len(param) ] )
        self.directory_edit = ckit.EditWidget( self, 16, 7, self.width()-18, 1, directory, [ 0, len(directory) ] )

        self.paint()

    def onClose(self):
        self.result = COMMANDWINDOW_RESULT_CANCEL
        self.quit()

    def onEnter(self):
        self.result = COMMANDWINDOW_RESULT_OK
        self.quit()

    def onKeyDown( self, vk, mod ):
    
        if vk==VK_UP or (vk==VK_TAB and mod==MODKEY_SHIFT):
            if self.focus==CommandWindow.FOCUS_FILE:
                self.focus=CommandWindow.FOCUS_NAME
            elif self.focus==CommandWindow.FOCUS_PARAM:
                self.focus=CommandWindow.FOCUS_FILE
            elif self.focus==CommandWindow.FOCUS_DIRECTORY:
                self.focus=CommandWindow.FOCUS_PARAM
            self.paint()

        elif vk==VK_DOWN or vk==VK_TAB:
            if self.focus==CommandWindow.FOCUS_NAME:
                self.focus=CommandWindow.FOCUS_FILE
            elif self.focus==CommandWindow.FOCUS_FILE:
                self.focus=CommandWindow.FOCUS_PARAM
            elif self.focus==CommandWindow.FOCUS_PARAM:
                self.focus=CommandWindow.FOCUS_DIRECTORY
            self.paint()

        elif vk==VK_RETURN:
            self.onEnter()

        elif vk==VK_ESCAPE:
            self.onClose()

        else:
            if self.focus==CommandWindow.FOCUS_NAME:
                self.name_edit.onKeyDown( vk, mod )
            elif self.focus==CommandWindow.FOCUS_FILE:
                self.file_edit.onKeyDown( vk, mod )
            elif self.focus==CommandWindow.FOCUS_PARAM:
                self.param_edit.onKeyDown( vk, mod )
            elif self.focus==CommandWindow.FOCUS_DIRECTORY:
                self.directory_edit.onKeyDown( vk, mod )

    def onChar( self, ch, mod ):
        if self.focus==CommandWindow.FOCUS_NAME:
            self.name_edit.onChar( ch, mod )
        elif self.focus==CommandWindow.FOCUS_FILE:
            self.file_edit.onChar( ch, mod )
        elif self.focus==CommandWindow.FOCUS_PARAM:
            self.param_edit.onChar( ch, mod )
        elif self.focus==CommandWindow.FOCUS_DIRECTORY:
            self.directory_edit.onChar( ch, mod )
        else:
            pass

    def paint(self):

        if self.focus==CommandWindow.FOCUS_NAME:
            attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg") )
        else:
            attr = ckit.Attribute( fg=ckit.getColor("fg") )
        self.putString( 2, 1, self.width()-2, 1, attr, "名前" )

        self.name_edit.enableCursor(self.focus==CommandWindow.FOCUS_NAME)
        self.name_edit.paint()


        if self.focus==CommandWindow.FOCUS_FILE:
            attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg") )
        else:
            attr = ckit.Attribute( fg=ckit.getColor("fg") )
        self.putString( 2, 3, self.width()-2, 1, attr, "ファイル" )

        self.file_edit.enableCursor(self.focus==CommandWindow.FOCUS_FILE)
        self.file_edit.paint()


        if self.focus==CommandWindow.FOCUS_PARAM:
            attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg") )
        else:
            attr = ckit.Attribute( fg=ckit.getColor("fg") )
        self.putString( 2, 5, self.width()-2, 1, attr, "パラメタ" )

        self.param_edit.enableCursor(self.focus==CommandWindow.FOCUS_PARAM)
        self.param_edit.paint()


        if self.focus==CommandWindow.FOCUS_DIRECTORY:
            attr = ckit.Attribute( fg=ckit.getColor("select_fg"), bg=ckit.getColor("select_bg") )
        else:
            attr = ckit.Attribute( fg=ckit.getColor("fg") )
        self.putString( 2, 7, self.width()-2, 1, attr, "ディレクトリ" )

        self.directory_edit.enableCursor(self.focus==CommandWindow.FOCUS_DIRECTORY)
        self.directory_edit.paint()

    def getResult(self):
        if self.result:
            return [ self.name_edit.getText(), self.file_edit.getText(), self.param_edit.getText(), self.directory_edit.getText() ]
        else:
            return None


def popCommandWindow( parent_window, name, file, param, directory ):
    pos = parent_window.centerOfWindowInPixel()
    command_window = CommandWindow( pos[0], pos[1], parent_window, name, file, param, directory )
    clnch_misc.adjustWindowPosition( parent_window, command_window, default_up=True )
    command_window.show(True)
    parent_window.enable(False)
    command_window.messageLoop()
    result = command_window.getResult()
    parent_window.enable(True)
    parent_window.activate()
    command_window.destroy()
    return result
