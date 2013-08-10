import io
import configparser

import pyauto

#-------------------------------------------------------------------------

class IpcData:

    options = [ "execute=", "text=", "selection=", "position=", ]

    def __init__( self, data=None ):

        self.ini = configparser.RawConfigParser()
        self.num_execute = 0
        
        if data:
            fd = io.StringIO(data)
            self.ini.readfp(fd)
            self.num_execute = self._countOption( "EXECUTE", "item" )

    def getValue(self):
        fd = io.StringIO("")
        self.ini.write(fd)
        return fd.getvalue().strip()

    def trySetOption( self, option, value ):
    
        if option=="--execute":
            self._addSection("EXECUTE")
            self.ini.set( "EXECUTE", "item%d" % self.num_execute, value )
            self.num_execute += 1
            return True
        
        elif option=="--text":
            self._addSection("COMMANDLINE")
            self.ini.set( "COMMANDLINE", "text", value )
            return True
        
        elif option=="--selection":
            self._addSection("COMMANDLINE")
            self.ini.set( "COMMANDLINE", "selection", value )
            return True
        
        elif option=="--position":
            self._addSection("COMMANDLINE")
            self.ini.set( "COMMANDLINE", "position", value )
            return True
        
        return False
            
    def _addSection( self, section ):            
        try:
            self.ini.add_section(section)
        except configparser.DuplicateSectionError:
            pass

    def _countOption( self, section, option ):
        count = 0
        while True:
            try:
                self.ini.get( section, "%s%d" % (option, count) )
            except ( configparser.NoOptionError, configparser.NoSectionError ):
                break
            count += 1
        return count

    def _getOptionList( self, section, option ):
        items = []
        count = 0
        while True:
            try:
                items.append( self.ini.get( section, "%s%d" % (option, count) ) )
            except ( configparser.NoOptionError, configparser.NoSectionError ):
                break
            count += 1
        return items

    def getExecuteList(self):
        return self._getOptionList( "EXECUTE", "item" )

    def execute( self, main_window ):

        class CommandLine:
            def __init__(self):
                pass
            def setText(self,text):
                pass
            def selectAll(self):
                pass
            def appendHistory(self,newentry):
                pass
            def quit(self):
                pass
        
        commandline = CommandLine()
        
        for text in self._getOptionList( "EXECUTE", "item" ):
            for commandline_function in main_window.commandline_list:
                if commandline_function.onEnter( commandline, text, 0 ):
                    break

    def commandLine( self, main_window ):
        
        text = None
        selection = None
        str_position = ""
        position = None

        try:
            text = self.ini.get( "COMMANDLINE", "text" )
        except ( configparser.NoOptionError, configparser.NoSectionError ):
            pass

        try:
            selection = self.ini.get( "COMMANDLINE", "selection" )
        except ( configparser.NoOptionError, configparser.NoSectionError ):
            pass

        try:
            str_position = self.ini.get( "COMMANDLINE", "position" )
        except ( configparser.NoOptionError, configparser.NoSectionError ):
            pass

        if str_position:
            try:
                position = eval(str_position)
                position_x_ratio = position[0] / 100.0
                position_y_ratio = position[1] / 100.0
            except:
                print( 'ERROR : invalid position description "%s".' % (str_position,) )
                return

        if not text and not selection and not position:
            return

        if text==None:
            text=""

        # 選択位置決定
        command_len = text.find(";")
        if command_len<0:
            command_len = len(text)
        
        if selection==None:
            selection="5"

        if selection=="0":
            selection = [ 0, 0 ]
        elif selection=="1":
            selection = [ 0, command_len ]
        elif selection=="2":
            selection = [ command_len, command_len ]
        elif selection=="3":
            selection = [ command_len+1, command_len+1 ]
        elif selection=="4":
            selection = [ command_len+1, len(text) ]
        elif selection=="5":
            selection = [ len(text), len(text) ]
        elif selection=="A":
            selection = [ 0, len(text) ]
        else:
            print( 'ERROR : unknown selection description "%s".' % (selection,) )
            selection = [ 0, 0 ]
        
        # 位置移動
        if position!=None:
        
            clnch_wnd = pyauto.Window.fromHWND( main_window.getHWND() )
            clnch_rect = clnch_wnd.getRect()
        
            fg_wnd = pyauto.Window.getForeground()
            fg_rect = fg_wnd.getRect()
            
            x = fg_rect[0] + ( ( fg_rect[2] - fg_rect[0] ) - ( clnch_rect[2]-clnch_rect[0] ) ) * position_x_ratio
            y = fg_rect[1] + ( ( fg_rect[3] - fg_rect[1] ) - ( clnch_rect[3]-clnch_rect[1] ) ) * position_y_ratio
            
            main_window.setPosSize( int(x), int(y), main_window.width(), main_window.height(), 0 )
        
        # アクティブ化
        wnd = pyauto.Window.fromHWND(main_window.getHWND())
        wnd.restore()
        last_active_wnd = wnd.getLastActivePopup()
        last_active_wnd.setForeground(True)
        if last_active_wnd.isEnabled():
            last_active_wnd.setActive()

        # ローカルなメッセージループ
        main_window.activeMessageLoop( text=text, selection=selection )

        # 位置戻す
        main_window.resetPos()


#-------------------------------------------------------------------------
