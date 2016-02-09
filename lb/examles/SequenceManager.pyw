import main.main
reload( main.main )
from main.main import *
import main.interface
reload( main.interface )
from main.interface import *
from main.Debug import *
import tabs.archive as archive
import tabs.sequence as sequence
import tabs.tractor as tractor
reload( archive ) 
reload( sequence )
reload( tractor )
DEBUG = 1
Debug.ENABLE = False

import getpass, pickle
from PyQt4 import QtGui, QtCore, QtNetwork

class Window( QtGui.QDialog ):
    
    """
    Create and control main window. 
    """
    
    PROJECT = None
    
    def __init__( self, filename=None, tab=0 ):
        """
        Initialize options.
        :filename - Input file name.
        """
        super( Window, self ).__init__( None, flags=QtCore.Qt.WindowMinimizeButtonHint|QtCore.Qt.WindowMaximizeButtonHint )
        self.FILE = filename
        self.TAB = tab
        #Create main layout.
        self._layout = QtGui.QVBoxLayout()
        self._layout.setSpacing( 0 )
        self._layout.setContentsMargins( 3,3,3,3 )
        self.bar = QtGui.QMenuBar( self )
        self._layout.addWidget( self.bar )
        self.setLayout( self._layout )
        self.isloaded = False
        #Create tray icon.
        self.tray = QtGui.QSystemTrayIcon( self )
        icontray = os.path.join( os.path.dirname(sys.modules[__name__].__file__ ), "icons/tray.png" )
        icon = QtGui.QIcon( icontray )
        self.tray.setIcon( icon )
        self.tray.setVisible( True )
        self.trayMenu = QtGui.QMenu( "Options" )
        self.showTrayAction = QtGui.QAction( "Show", self )
        self.showTrayAction.setStatusTip( "Show application" )
        self.showTrayAction.triggered.connect( self.showApplication )
        self.trayMenu.addAction( self.showTrayAction )
        self.exitTrayAction = QtGui.QAction( "Exit", self )
        self.exitTrayAction.setStatusTip( "Exit from application" )
        self.exitTrayAction.triggered.connect( self.exitFromApplication )
        self.trayMenu.addAction( self.exitTrayAction )
        defaultStyle( self.trayMenu )
        self.tray.setContextMenu( self.trayMenu )
        self.tray.activated.connect( self.trayActivated )
        #Apply default styling options.
        self.setWindowTitle( "Scene manager" )
        
    def load( self ):
        """
        Deferred window loading.
        """
        if self.isloaded is False:
            print "Window.load()"
            self.CTX = WindowCTX( filename=self.FILE, tab=self.TAB )
            self._layout.addWidget( self.CTX )
            self.CTX.load()
            self.options = QtGui.QMenu( "Options" )
            self.options.setTearOffEnabled( True )
            self.bar.addMenu( self.options )
            self.minimizedStart = QtGui.QAction( "Start minimized", self )
            self.minimizedStart.setStatusTip( "Start in minimized window." )
            self.minimizedStart.setCheckable( True )
            self.minimizedStart.setChecked( False )
            self.minimizedStart.triggered.connect( self.updateSettings )
            self.options.addAction( self.minimizedStart )
            self.alwaysOnTop = QtGui.QAction( "Always on top", self )
            self.alwaysOnTop.setStatusTip( "Make window staying always on top." )
            self.alwaysOnTop.setCheckable( True )
            self.alwaysOnTop.setChecked( False )
            self.alwaysOnTop.triggered.connect( self.updateSettings )
            self.options.addAction( self.alwaysOnTop )
            self.minimizeToTray = QtGui.QAction( "Minimize to tray", self )
            self.minimizeToTray.setStatusTip( "Minimize to tray on minimize action." )
            self.minimizeToTray.setCheckable( True )
            self.minimizeToTray.setChecked( False )
            self.minimizeToTray.triggered.connect( self.updateSettings )
            self.options.addAction( self.minimizeToTray )
            self.autoRunWithOS = QtGui.QAction( "Autorun with os", self )
            self.autoRunWithOS.setStatusTip( "Automatic run on system startup." )
            self.autoRunWithOS.setCheckable( True )
            self.autoRunWithOS.setChecked( False )
            self.autoRunWithOS.triggered.connect( self.updateSettings )
            self.options.addAction( self.autoRunWithOS )
            self.exitApplicationAction = QtGui.QAction( "Exit", self )
            self.exitApplicationAction.setStatusTip( "Exit from application" )
            self.exitApplicationAction.triggered.connect( self.exitFromApplication )
            self.options.addAction( self.exitApplicationAction )
            defaultStyle( self.options )
            self.isloaded = True
        self.readSettings()
        
    def trayActivated( self, reason ):
        """
        Handle tray icon activated.
        :reason - Input reason.
        """
        if self.minimizeToTray.isChecked() is True:
            if reason == QtGui.QSystemTrayIcon.DoubleClick:
                if self.isHidden():
                    self.show()
                    return
                elif self.windowState() & QtCore.Qt.WindowMinimized:
                    self.setWindowState( QtCore.Qt.WindowNoState )
                    return
                else:
                    self.hide()
                    return
        if self.windowState() & QtCore.Qt.WindowMinimized:
            self.setWindowState( QtCore.Qt.WindowNoState )
            return
                    
    def changeEvent( self, event ):
        """
        Handle change window events.
        """
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.minimizeToTray.isChecked() is True:
                if self.windowState() & QtCore.Qt.WindowMinimized:
                    event.ignore()
                    self.hide()
                    return
        super( Window, self ).changeEvent( event )
        
    def showEvent( self, event ):
        """
        Handle show events.
        """
        if self.isHidden():
            self.show()
        super( Window, self ).showEvent( event )
        
    def showApplication( self ):
        """
        Show application.
        """
        if self.isHidden():
            self.show()
        if self.windowState() & QtCore.Qt.WindowMinimized:
            self.setWindowState( QtCore.Qt.WindowNoState )
        
    def closeEvent( self, event ):
        """
        Handle close event.
        :event - Input event.
        """
        if self.minimizeToTray.isChecked() is False:
            self.writeSettings()
            self.tray.setVisible( False )
            event.accept()
            sys.exit()
        else:
            event.ignore()
            self.hide()
            self.tray.showMessage( "Sequence manager", "Running in the background." )
        
    def exitFromApplication( self ):
        """
        Close application.
        """
        self.writeSettings()
        self.tray.setVisible( False )
        sys.exit()
        
    def writeSettings( self ):
        """
        Write interface options on close event.
        """
        #Open settings.
        settings = QtCore.QSettings( "Melnitsa Soft", "Yago" )
        settings.beginGroup( "SceneManagerWindow" )
        #Write settings.
        state = settings.value( "", self.windowState())
        if state != 2:
            settings.setValue( "MainWindowPosition", self.pos())
            settings.setValue( "MainWindowSize", self.size())
        settings.setValue( "MainWindowState", self.windowState())
        stat = 0
        if self.minimizedStart.isChecked(): stat = 1
        settings.setValue( "minimizedStart", stat )
        stat = 0
        if self.alwaysOnTop.isChecked(): stat = 1
        settings.setValue( "alwaysOnTop", stat )
        stat = 0
        if self.minimizeToTray.isChecked(): stat = 1
        settings.setValue( "minimizeToTray", stat )
        stat = 0
        if self.autoRunWithOS.isChecked(): stat = 1
        settings.setValue( "autoRunWithOS", stat )
        #Close settings.
        settings.endGroup()
        #Write settings for child window.
        self.CTX.writeSettings()
        
    def readSettings( self ):
        """
        Read interface options on loading.
        """
        #Open settings.
        settings = QtCore.QSettings( "Melnitsa Soft", "Yago" )
        settings.beginGroup( "SceneManagerWindow" )
        #Read settings.
        state = settings.value( "MainWindowState", QtCore.QState())
        position = settings.value( "MainWindowPosition", QtCore.QPoint( 200, 200 ))
        size = settings.value( "MainWindowSize", QtCore.QSize( 1004, 598 ))
        size = size.toSize()
        position = position.toPoint()
        self.resize( size )
        self.move( position )
        if state == 2:
            self.setWindowState( QtCore.Qt.WindowMaximized )
        elif state == 1:
            self.setWindowState( QtCore.Qt.WindowMinimized )
        stat = settings.value( "minimizedStart", "1" ).toInt()
        if stat[0] == 0: self.minimizedStart.setChecked( False )
        else: self.minimizedStart.setChecked( True )
        stat = settings.value( "alwaysOnTop", "1" ).toInt()
        if stat[0] == 0: self.alwaysOnTop.setChecked( False )
        else: self.alwaysOnTop.setChecked( True )
        stat = settings.value( "minimizeToTray", "1" ).toInt()
        if stat[0] == 0: self.minimizeToTray.setChecked( False )
        else: self.minimizeToTray.setChecked( True )
        stat = settings.value( "autoRunWithOS", "1" ).toInt()
        if stat[0] == 0: self.autoRunWithOS.setChecked( False )
        else: self.autoRunWithOS.setChecked( True )
        #Close settings.
        settings.endGroup()
        if self.minimizedStart.isChecked():
            self.setWindowState( self.windowState() | QtCore.Qt.WindowMinimized ) 
        self.updateSettings()
        
    def updateSettings( self ):
        """
        Update settings.
        """
        print "Update options."
        if self.alwaysOnTop.isChecked():
            self.setWindowFlags( self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint )
            self.show()
        else:
            self.setWindowFlags( self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint )
            self.show()
        
class WindowCTX( QtGui.QMainWindow ):
    
    def __init__( self, filename=None, tab=0 ):
        """
        Initialize window options.
        :filename - Input file name.
        """
        super( WindowCTX, self ).__init__()
        self.FILE = filename
        self.TAB = tab
        #Create main layout.
        self.main = QtGui.QWidget()
        self._layout = QtGui.QVBoxLayout()
        self._layout.setSpacing( 0 )
        self._layout.setContentsMargins( 3,3,3,3 )
        self.main.setLayout( self._layout )
        self.setCentralWidget( self.main )
        self.TABS = []
        self.isloaded = False
    
    def load( self ):
        """
        Deferred window loading.
        """
        if self.isloaded is False:
            print "WindowCTX.load()"
            #Create tab widget for choosing.
            self.tabs = QtGui.QTabWidget()
            self.tabs.setFocusPolicy( QtCore.Qt.ClickFocus )
            self.tabs.setContentsMargins( 0, 0, 0, 0 )
            self._layout.addWidget( self.tabs )
            #Create widgets for applying.
            self.SRW = sequence.Window( self.FILE, parent=self )
            self.ASW = archive.Window( self.FILE, parent=self )
            self.TRW = tractor.Window( self.FILE, parent=self )
            self.TABS = [ self.SRW, self.ASW, self.TRW ]
            #Add window into tabs.
            self.tabs.addTab( self.SRW, "Sequences" )
            self.tabs.addTab( self.ASW, "Scenes" )
            self.tabs.addTab( self.TRW, "Tractor" )
            self.tabs.currentChanged.connect( self.tab )
            #Help interface.
            self.progressBar = QtGui.QProgressBar()
            self.progressBar.setStatusTip( "Progress bar." )
            self.progressBar.setMaximumWidth( 128 )
            statusbar = QtGui.QStatusBar()
            statusbar.addPermanentWidget( self.progressBar )
            self.setStatusBar( statusbar )
            self.statusBar().showMessage( "Initialized..." )
            #Mark window as loaded.
            self.tabs.setCurrentIndex( self.TAB )
            self.tab( self.TAB )
            self.isloaded = True
        self.readSettings()
        
    def tab( self, index ):
        """
        Deferred tab loading.
        """
        self.TABS[index].load()
        
    def writeSettings( self ):
        """
        Write interface options on close event.
        """
        #Open settings.
        settings = QtCore.QSettings( "Melnitsa Soft", "Yago" )
        settings.beginGroup( "SceneManagerWindowCTX" )
        #Write settings.
        #Write tab settings.
        #Close settings.
        settings.endGroup()
        for tab in self.TABS:
            tab.writeSettings()
        
    def readSettings( self ):
        """
        Read interface options on loading.
        """
        #Open settings.
        settings = QtCore.QSettings( "Melnitsa Soft", "Yago" )
        settings.beginGroup( "SceneManagerWindowCTX" )
        #Read settings.
        #Close settings.
        settings.endGroup()
            
    def showTooltipOnStatusBar( self, string ):
        """
        Show requested tool tip on status bar view.
        :string - Input tool tip string.
        """
        self.statusBar().showMessage( string )

class QSceneMangerApplication( QtGui.QApplication ):
    
    """
    Access to control single tone application.
    """
    
    timeout = 1000
 
    def __init__( self, args, application_id=None ):
        """
        Initialize application options.
        """
        super( QSceneMangerApplication, self ).__init__( args )
        self.WIDGET = None
        self.socketFilename = unicode( os.path.expanduser( "~/.ipc_%s" % self.generateIpcID()))
        self.sharedMemory = QtCore.QSharedMemory()
        self.sharedMemory.setKey( self.socketFilename )
        if self.sharedMemory.attach():
            self.isRunning = True
            self.sendMessage( args )
            exit()
            return
        self.isRunning = False
        if not self.sharedMemory.create( 1 ):
            Debug.log( "Failed to create unique application instance." )
        #Start local server.
        self.server = QtNetwork.QLocalServer( self )
        # connect signal for incoming connections
        self.connect( self.server, QtCore.SIGNAL( "newConnection()" ), self.receiveMessage )
        #If socket file exists, delete it.
        if os.path.exists( self.socketFilename ):
            os.remove( self.socketFilename )
        #listen.
        self.server.listen( self.socketFilename )
 
    def __del__( self ):
        """
        Delete method.
        """
        self.sharedMemory.detach()
        if not self.isRunning:
            if os.path.exists(self.socketFilename):
                os.remove(self.socketFilename)
 
    def generateIpcID( self, channel=None ):
        if channel is None:
            channel = os.path.basename(sys.argv[0])
        return "%s_%s" % ( channel, getpass.getuser())
 
    def sendMessage( self, message ):
        """
        Send message.
        """
        if not self.isRunning:
            raise Exception("Client cannot connect to IPC server. Not running.")
        socket = QtNetwork.QLocalSocket(self)
        socket.connectToServer(self.socketFilename, QtCore.QIODevice.WriteOnly)
        if not socket.waitForConnected(self.timeout):
            raise Exception(str(socket.errorString()))
        socket.write(pickle.dumps(message))
        if not socket.waitForBytesWritten(self.timeout):
            raise Exception(str(socket.errorString()))
        socket.disconnectFromServer()
 
    def receiveMessage( self ):
        """
        Receieve message.
        """
        socket = self.server.nextPendingConnection()
        if not socket.waitForReadyRead( self.timeout ):
            print >>sys.stderr, socket.errorString()
            return
        byteArray = socket.readAll()
        self.handleMessage( pickle.loads( str( byteArray )))
        
    def setWindowAsMain( self, widget ):
        """
        Set widget as main widget.
        """
        self.WIDGET = widget
 
    def handleMessage( self, message ):
        """
        Handle message.
        """
        if self.WIDGET:
            self.WIDGET.showApplication()
            self.WIDGET.CTX.statusBar().showMessage( "Recieved message:" + " ".join( message ) )
        
def getApplication( path=None ):
    app = QSceneMangerApplication( sys.argv )
    app.setStyle( "plastique" )
    window = Window( path )
    app.setWindowAsMain( window )
    window.load()
    defaultStyle( window )
    window.show()
    sys.exit(app.exec_())
    return app, window

def getWindow( path=None ):
    window = Window( path )
    QtCore.QSharedMemory()
    window.load()
    defaultStyle( window )
    window.show()
    return window  

if DEBUG == 0:
    print "args:", sys.argv
    if len( sys.argv ) > 1:
        app, window = getApplication( path=sys.argv[1] )
    else:
        app, window = getApplication()
else:
    path = "//RENDERSERVER/Project/UrfinJuse/scenes/ep08/ep08sc51/renderman/ep08sc51_fon_light_batch_0/"    
    app, window = getApplication( path )      