import ckit
from ckit.ckit_const import *

import clnch_misc
from clnch_resource import *

#--------------------------------------------------------------------

class StatusBarLayer:

    def __init__( self, priority ):
        self.priority = priority

    def paint( self, window, x, y, width, height ):
        attr = ckit.Attribute( fg=ckit.getColor("bar_fg") )
        window.putString( x, y, width, height, attr, " " * width )


class SimpleStatusBarLayer(StatusBarLayer):

    def __init__( self, priority=-1, message="" ):
        StatusBarLayer.__init__( self, priority )
        self.message = message
        self.error = False

    def setMessage( self, message, error=False ):
        self.message = message
        self.error = error

    def paint( self, window, x, y, width, height ):
        s = " %s" % ( self.message )
        s = ckit.adjustStringWidth( window, s, width-1 )
        if self.error:
            attr = ckit.Attribute(fg=ckit.getColor("bar_error_fg"))
        else:
            attr = ckit.Attribute( fg=ckit.getColor("bar_fg") )
        window.putString( x, y, width, height, attr, s )


class StatusBar:

    def __init__(self):
        self.layer_list = []

    def registerLayer( self, layer ):
        self.layer_list.append(layer)
        self.layer_list.sort( key = lambda layer: layer.priority )

    def unregisterLayer( self, layer ):
        self.layer_list.remove(layer)

    def isActiveLayer( self, layer ):
        if len(self.layer_list)>0:
            active_layer = self.layer_list[0]
        else:
            active_layer = None
        return ( layer == active_layer )

    def paint( self, window, x, y, width, height ):
        if len(self.layer_list)>0:
            self.layer_list[0].paint( window, x, y, width, height )
        else:
            attr = ckit.Attribute( fg=ckit.getColor("bar_fg") )
            window.putString( x, y, width, height, attr, " " * width )
