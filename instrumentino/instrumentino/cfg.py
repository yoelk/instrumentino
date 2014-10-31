from __future__ import division
from datetime import datetime
import time
import os
from pkg_resources import resource_filename
import wx
import threading

__author__ = 'yoelk'

'''
Instrumentino configuration variables
'''
# The way we show numbers
numIntegerPartWidth = 4
numFractionPartWidth = 3
numStringFormat = '{:' + str(numIntegerPartWidth) + '.' + str(numFractionPartWidth) + 'f}' 

# Files handeled
methodWildcard = 'Method file (*.mtd)|*.mtd'
sequenceWildcard = 'Sequence file (*.seq)|*.seq'

# Events handeled by the main window
EVT_LOG_UPDATE = wx.NewId()
EVT_UPDATE_CONTROLS = wx.NewId()
EVT_POP_MESSAGE = wx.NewId()

app = None
mainFrame = None
logTextCtrl = None
logGraph = None
commandsLogFile = None
signalsLogFile = None
systemUid = None

controllers = []
userStopped = False

def InitVariables(arguApp):
    '''
    init system variables
    '''
    global app
    app = arguApp
    
    global mainFrame
    mainFrame = arguApp.mainFrame
    
    global logTextCtrl
    logTextCtrl = wx.xrc.XRCCTRL(arguApp.mainFrame, 'logTextCtrl')
    logTextCtrl.SetEditable(False)
    
    global logGraph
    logGraph = arguApp.logGraph
    
    global timeNow
    timeNow = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
    
    global commandsLogFile
    commandsLogFile = open(LogPath(timeNow + '.txt'), 'w')
    
    global signalsLogFile
    signalsLogFile = open(LogPath(timeNow + '.csv'), 'w')
    
    global systemUid
    systemUid = arguApp.system.GetSystemUid()

def AddControllerIfNeeded(controllerClass):
    '''
    add a controller to the needed controllers list, only if it doesn't exist already
    '''
    global controllers
    for c in controllers:
        if isinstance(c, controllerClass):
            return
        
    # if reached here, add an object of the given class
    controllers += [controllerClass()]

def Close():
    global controllers
    for c in controllers:
        c.Close()
    
def AllOnline():
    '''
    check if all controllers are online
    '''
    global controllers
    for c in controllers:
        if not c.online:
            return False
        
    # if reached here and list isn't empty all are online
    return (len(controllers) > 0)

def IsCompOnline(sysComp):
    '''
    check if the controller of a component is online
    '''
    global controllers
    for c in controllers:
        if isinstance(c, sysComp.controllerClass):
            return c.online
        
    # if reached here, it's not online
    return False

def GetController(controllerClass):
    '''
    return the active controller instance of this class
    '''
    global controllers
    for c in controllers:
        if isinstance(c, controllerClass):
            return c
        
    # if reached here, no controller exists
    return None

def ResourcePath(relativePath=''):
    '''
    Get the resource path
    '''
    
#         """ Get absolute path to resource, works for dev and for PyInstaller """
#         try:
#             # PyInstaller creates a temp folder and stores path in _MEIPASS
#             basePath = sys._MEIPASS
#         except Exception:
#             basePath = os.path.dirname(resource_filename('instrumentino.resources', 'main.xrc'))
    basePath = os.path.dirname(resource_filename('instrumentino.resources', 'main.xrc'))
    return os.path.join(basePath, relativePath)


def GetOrCreateDirectory(name):
    '''
    Enter a directory and create it if needed
    '''
    path = name + '/'
        
    try:
        os.mkdir(path)
    except:
        pass
    
    return path

def UserFilesPath(relativePath=''):
    '''
    Get the user directory
    '''
    return GetOrCreateDirectory('user') + relativePath

def LogPath(relativePath=''):
    '''
    Get the log directory
    '''
    return GetOrCreateDirectory('log') + relativePath
    
def Log(text):
    '''
    Log an event
    '''
    global logTextCtrl
    global commandsLogFile
    
    if logTextCtrl != None:
        logTextCtrl.WriteText(text + '\r')
    if commandsLogFile != None:
        commandsLogFile.write(text + '\r')
        
def LogFromOtherThread(text, critical=False):
    '''
    Log an event while running a method/sequence
    '''
    global mainFrame
    wx.PostEvent(mainFrame, ResultEvent(EVT_LOG_UPDATE, (text, critical)))

def UpdateControlsFromOtherThread(runningOperation=False):
    '''
    Update the control buttons while running a method/sequence
    '''
    global mainFrame
    wx.PostEvent(mainFrame, ResultEvent(EVT_UPDATE_CONTROLS, runningOperation))

def Sleep(seconds):
    '''
    Sleep, and wake up when user pressed the stop button
    '''
    time.sleep(seconds%1)
    end = time.time() + int(seconds)
    while time.time() <= end: 
        if userStopped:
            return
        
def WaitForUser(text=''):
    '''
    Wait for the user to press a button
    '''
    e = threading.Event()
    wx.PostEvent(mainFrame, ResultEvent(EVT_POP_MESSAGE, (text, e)))
    time.sleep(3)
    e.wait()
    
class ResultEvent(wx.PyEvent):
    '''
    Simple event to carry arbitrary result data.
    '''
    def __init__(self, eventType, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(eventType)
        self.data = data