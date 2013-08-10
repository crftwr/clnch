import os
import ctypes

import ckit

import clnch_misc
import clnch_statusbar
import clnch_ini

#--------------------------------------------------------------------

class SongMCI:

    def __init__( self, filename ):
        self.filename = filename
        ret = ctypes.windll.winmm.mciSendStringW( 'open "%s" alias %d' % ( self.filename, id(self) ), None, 0, None )
        ret = ctypes.windll.winmm.mciSendStringW( 'set %d time format milliseconds' % ( id(self), ), None, 0, None )

    def __del__(self):
        self.close()

    def play(self):
        ret = ctypes.windll.winmm.mciSendStringW( 'play %d' % ( id(self), ), None, 0, None )

    def isPlaying(self):
        buf = ctypes.create_unicode_buffer(32)
        ret = ctypes.windll.winmm.mciSendStringW( 'status %d mode' % ( id(self), ), buf, len(buf), None )
        if buf.value == 'playing':
            return True
        else:
            return False

    def stop(self):
        ret = ctypes.windll.winmm.mciSendStringW( 'stop %d' % ( id(self), ), None, 0, None )

    def seek( self, pos ):
        value = int( pos * 1000 )
        if self.isPlaying():
            ret = ctypes.windll.winmm.mciSendStringW( 'play %d from %d' % ( id(self), value ), None, 0, None )

    def length(self):
        buf = ctypes.create_unicode_buffer(32)
        ret = ctypes.windll.winmm.mciSendStringW( 'status %d length' % ( id(self), ), buf, len(buf), None )
        if ret : return 0.0
        return int(buf.value)/1000.0

    def position(self):
        buf = ctypes.create_unicode_buffer(32)
        ret = ctypes.windll.winmm.mciSendStringW( 'status %d position' % ( id(self), ), buf, len(buf), None )
        if ret : return 0.0
        return int(buf.value)/1000.0

    def close(self):
        ret = ctypes.windll.winmm.mciSendStringW( 'close %d' % ( id(self), ), None, 0, None )


class MusicPlayer:

    def __init__( self, main_window ):

        self.main_window = main_window

        self.items = []
        self.cursor = 0

        self.song = None
        self.playing = False
        self.song_name = ""

        self.position = None
        self.length = None

        self.status_bar = MusicPlayerStatusBar(self)
        self.main_window.statusBar().registerLayer(self.status_bar)
        self.main_window.paint()

        self.main_window.setTimer( self.onTimer, 10 )
        self.main_window.setTimer( self.onTimerStatusBar, 1000 )

    def destroy(self):

        self.stop()

        self.main_window.killTimer( self.onTimer )
        self.main_window.killTimer( self.onTimerStatusBar )

        self.main_window.statusBar().unregisterLayer(self.status_bar)
        self.main_window.paint()

    def setPlayList( self, items, selection ):
        self.stop()
        self.items = items
        self.cursor = selection
        self.song_name = self.items[self.cursor]
        self.main_window.paint()

    def getPlayList(self):
        return ( self.items, self.cursor )

    def save( self, section ):
        i=0
        for item in self.items:
            clnch_ini.set( section, "playlist_%d"%(i,), item )
            i+=1

        while True:
            if not clnch_ini.remove_option( section, "playlist_%d"%(i,) ) : break
            i+=1
        
        clnch_ini.set( section, "track", str(self.cursor) )
        clnch_ini.set( section, "position", str(int(self.position)) )
        
    def load( self, section ):
        for i in range(100):
            try:
                item =ckit.normPath( clnch_ini.get( section, "playlist_%d"%(i,) ) )
                self.items.append(item)
            except:
                break
        
        self.cursor = clnch_ini.getint( section, "track", 0 )
        self.position = clnch_ini.getint( section, "position", 0 )

        self.cursor = min( self.cursor, len(self.items) )
        self.song_name = self.items[self.cursor]
        self.play()
        self.seek(self.position)
        self.pause()
        self.main_window.paint()

    def play(self):
        self.song = SongMCI( self.items[self.cursor] )
        self.song.play()
        self.playing = True

    def stop(self):
        if self.song:
            self.song.close()
        self.song = None
        self.playing = False

    def pause(self):
        if self.song:
            if self.song.isPlaying():
                self.song.stop()
                self.playing = False
            else:
                self.song.play()
                self.playing = True

    def seek(self,pos):
        if self.song:
            self.song.seek(pos)

    def advance( self, delta ):
        if self.song:
            p = self.song.position()
            t = self.song.length()
            p += delta
            p = min( p, t )
            p = max( p, 0.0 )
            self.song.seek(p)

    def prev(self):
        if self.cursor-1 >= 0:
            self.cursor -= 1
            self.song_name = self.items[self.cursor]
            self.play()
            self.main_window.paint()

    def next(self):
        if self.cursor+1 < len(self.items):
            self.cursor += 1
            self.song_name = self.items[self.cursor]
            self.play()
            self.main_window.paint()

    def select( self, sel ):
        if sel < len(self.items):
            self.cursor = sel
            self.song_name = self.items[sel]
            self.play()
            self.main_window.paint()

    def isPlaying(self):
        return self.playing

    def onTimer(self):
        if self.song:
            if not self.song.isPlaying():
                if self.playing:
                    self.next()
            self.position = self.song.position()
            self.length = self.song.length()
        else:
            self.position = None
            self.length = None

    def onTimerStatusBar(self):
        self.main_window.paint()


def _timeString(t):
    m = int( t / (60) )
    t -= m * (60)
    s = int( t )
    return "%d:%02d" % (m,s)    

class MusicPlayerStatusBar( clnch_statusbar.StatusBarLayer ):

    def __init__( self, music_player ):
        clnch_statusbar.StatusBarLayer.__init__( self, 1.0 )
        self.music_player = music_player

    def paint( self, window, x, y, width, height ):
        if self.music_player.position!=None and self.music_player.length!=None:
            right = " %s - %s " % ( _timeString(self.music_player.position), _timeString(self.music_player.length-self.music_player.position) )
        else:
            right = " "
        left = " [ Music %d/%d ] %s" % ( self.music_player.cursor+1, len(self.music_player.items), self.music_player.song_name )
        left = ckit.adjustStringWidth( window, left, width-len(right), ckit.ALIGN_LEFT, ckit.ELLIPSIS_RIGHT )
        attr = ckit.Attribute( fg=ckit.getColor("bar_fg") )
        window.putString( x, y, width, y, attr, left+right )
