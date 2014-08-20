from __future__ import division
from instrumentino.controllers.arduino.pins import AnalogPins
__author__ = 'yoelk'

import wx
from wx import xrc, lib
from wx.lib import wordwrap
import pickle
import os
from datetime import datetime
from instrumentino import cfg
from method import ActionsListCtrl
from sequence import MethodsListCtrl
from log_graph import LogGraphPanel
from instrumentino.action import SysAction, SysActionParamTime
from instrumentino.controllers.arduino import Arduino, SysVarAnalogArduinoUnipolar
from util import SerialUtil
import time
import sys

class InstrumentinoApp(wx.App):
    '''
    This class implements the application
    '''
    monitorUpdateDelayMilisec = Arduino.cacheReadDelayMilisec
    updateFrequency = 1000 / monitorUpdateDelayMilisec

    def __init__(self, system):
        self.system = system
        self.sysComps = self.system.comps
        self.sysActions = self.system.actions
        wx.App.__init__(self, False)

    def OnInit(self):
        '''
        Load the main window from the main.xrc
        '''
        self.mainXrc = wx.xrc.XmlResource(cfg.ResourcePath('main.xrc'))
        self.InitFrame()
        return True

    def InitFrame(self):
        '''
        Init the main window
        '''
        self.listButtons = []
        self.runButtons = []
        self.mainFrame = self.mainXrc.LoadFrame(None, 'mainFrame')
        self.splitter = wx.xrc.XRCCTRL(self.mainFrame, 'splitter')
        self.mainFrame.SetTitle(self.system.name)
        self.mainFrame.Bind(wx.EVT_CLOSE, self.OnClose)
        
        # log
        self.logGraph = LogGraphPanel(wx.xrc.XRCCTRL(self.mainFrame, 'logGraphPage'), self.sysComps)
        self.Connect(-1, -1, cfg.EVT_LOG_UPDATE, self.OnLogUpdate)
        
        # update framework
        cfg.InitVariables(self)
        
        # Menu
        self.mainFrame.Bind(wx.EVT_MENU, self.OnLoadSequence, id=wx.xrc.XRCID('loadSequenceMenuItem'))
        self.mainFrame.Bind(wx.EVT_MENU, self.OnSaveSequence, id=wx.xrc.XRCID('saveSequenceMenuItem'))
        self.mainFrame.Bind(wx.EVT_MENU, self.OnLoadMethod, id=wx.xrc.XRCID('loadMethodMenuItem'))
        self.mainFrame.Bind(wx.EVT_MENU, self.OnSaveMethod, id=wx.xrc.XRCID('saveMethodMenuItem'))
        self.mainFrame.Bind(wx.EVT_MENU, self.OnClose, id=wx.xrc.XRCID('quitMenuItem'))
        self.mainFrame.Bind(wx.EVT_MENU, self.OnAbout, id=wx.xrc.XRCID('aboutMenuItem'))
        
        menusDict = dict(self.mainFrame.GetMenuBar().GetMenus())
        commMenu = [key for key, value in menusDict.iteritems() if value == 'Comm'][0]
        for comp in self.sysComps:
            cfg.AddControllerIfNeeded(comp.controllerClass)
        
        for controller in cfg.controllers:
            menu = commMenu.Append(-1, controller.name, 'Connect the ' + controller.name)
            self.mainFrame.Bind(wx.EVT_MENU, controller.OnMenuConnect, menu)            
        
        # sysCompsPanel
        monitorPanel = wx.xrc.XRCCTRL(self.mainFrame, 'monitorPanel')
        self.stopButton = wx.BitmapButton(monitorPanel, -1, wx.Bitmap(cfg.ResourcePath('stopButton.png'), wx.BITMAP_TYPE_PNG))
        monitorPanel.GetSizer().Add(self.stopButton, flag=wx.BOTTOM|wx.ALIGN_CENTRE_HORIZONTAL)
        self.stopButton.Bind(wx.EVT_BUTTON, self.OnStopButton)               
                
        self.sysCompsPanel = wx.xrc.XRCCTRL(self.mainFrame, 'sysCompsPanel')
        sysCompsPanelBoxSizer = self.sysCompsPanel.GetSizer()        
        for sysComp in self.sysComps:
            panel = sysComp.CreatePanel(self.sysCompsPanel)
            if panel != None:
                sysCompsPanelBoxSizer.Add(panel)
        
        # make all sysComps fill their given area
        for sysCompPanel in sysCompsPanelBoxSizer.GetChildren():
            sysCompPanel.SetFlag(wx.GROW)
        sysCompsPanelBoxSizer.Fit(self.mainFrame)
 
        self.Connect(-1, -1, cfg.EVT_UPDATE_CONTROLS, self.OnUpdateControls)
        self.Connect(-1, -1, cfg.EVT_POP_MESSAGE, self.OnPopMessage)
        
        # Method
        self.actionsListCtrl = ActionsListCtrl(wx.xrc.XRCCTRL(self.mainFrame, 'methodPage'), self.sysActions)
        self.runButtons.append(self.actionsListCtrl.runButton)
        self.listButtons.extend([self.actionsListCtrl.list, self.actionsListCtrl.addButton, self.actionsListCtrl.removeButton])
        
        # Sequence
        self.methodsListCtrl = MethodsListCtrl(wx.xrc.XRCCTRL(self.mainFrame, 'sequencePage'))
        self.runButtons.append(self.methodsListCtrl.runButton)
        self.listButtons.extend([self.methodsListCtrl.list, self.methodsListCtrl.addButton, self.methodsListCtrl.removeButton])

        # This makes sure both pages are drawn
        notebook = wx.xrc.XRCCTRL(self.mainFrame, 'methodsAndSequences')
        notebook.SendPageChangedEvent(0,1)        
        self.mainFrame.GetSizer().Fit(self.mainFrame)        
        notebook.SendPageChangedEvent(1,0)
        
        # main frame
        self.splitter.SetSashPosition(400, True)
        self.mainFrame.GetSizer().Fit(self.mainFrame)
        self.UpdateControls()
        self.mainFrame.Show()
        
        # Monitor periodically
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.MonitorUpdate, self.timer)
        self.timer.Start(self.monitorUpdateDelayMilisec)
        
    def OnLogUpdate(self, event):
        '''
        Update log
        '''
        (text, critical) = event.data
        cfg.Log(text)
        if critical:
            dlg = wx.MessageDialog(self.mainFrame,
                               text,
                               'Error', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
    
    def OnUpdateControls(self, event):
        '''
        Update the system components' availability
        '''
        self.UpdateControls(event.data)
    
    def OnPopMessage(self, event):
        '''
        Pop a message window to the user
        '''
        (text, e) = event.data
        wx.Bell()
        dlg = wx.MessageDialog(self.mainFrame,
                               text + '\nResume operation?',
                               'Waiting for user', wx.OK|wx.ICON_QUESTION)
        dlg.ShowModal()
        dlg.Destroy()
        e.set()
    
    def UpdateControls(self, runningOperation=False):
        '''
        Update the system components frame with actual values
        '''
        for comp in self.sysComps:
            comp.Enable(cfg.IsCompOnline(comp))
        
        for button in self.listButtons:
            button.Enable(not runningOperation)

        for button in self.runButtons:
            button.Enable(cfg.AllOnline() and not runningOperation)

        self.stopButton.Enable(cfg.AllOnline() and runningOperation)
        
        cfg.logTextCtrl.Enable(cfg.AllOnline())
        cfg.logGraph.Enable(cfg.AllOnline())
    
    def OnLoadSequence(self, event):
        '''
        Load a sequence file
        '''
        self.loadFile(event, "Choose a sequence file", cfg.sequenceWildcard, self.methodsListCtrl)
    
    def OnSaveSequence(self, event):
        '''
        Save a sequence file
        '''
        self.saveFile(event, "Save sequence as ...", cfg.sequenceWildcard, '.seq', self.methodsListCtrl)
    
    def OnLoadMethod(self, event):
        '''
        Load a method file
        '''
        self.loadFile(event, "Choose a method file", cfg.methodWildcard, self.actionsListCtrl)

    def OnSaveMethod(self, event):
        '''
        Save a method file
        '''
        self.saveFile(event, "Save method as ...", cfg.methodWildcard, '.mtd', self.actionsListCtrl)
            
    def loadFile(self, event, message, wildcard, listCtrl):
        '''
        File loading helper function
        '''
        dlg = wx.FileDialog(self.mainFrame, message=message, defaultDir=cfg.UserFilesPath(),
                            defaultFile="", wildcard=wildcard,
                            style=wx.OPEN | wx.CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                filePath = dlg.GetPaths()[0]
                with open(filePath, 'r') as fp:
                    dlg.Destroy()
                    savedFile = pickle.load(fp)
                    if savedFile.systemUid == self.system.GetSystemUid():
                        listCtrl.populateList(savedFile.list)
                        cfg.LogFromOtherThread('File loaded: ' + filePath)
                    else:
                        errDlg = wx.MessageDialog(self.mainFrame, 'File incompatible with this system',
                                              'Error',
                                              wx.OK | wx.ICON_ERROR)
                        errDlg.ShowModal()
                        errDlg.Destroy()
                    
            except (IOError, EOFError):
                errDlg = wx.MessageDialog(self.mainFrame, 'Error loading the file',
                                          'Error',
                                          wx.OK | wx.ICON_ERROR)
                errDlg.ShowModal()
                errDlg.Destroy()
    
    def saveFile(self, event, message, wildcard, extension, listCtrl):
        '''
        File saving helper function
        '''
        dlg = wx.FileDialog(self.mainFrame, message=message, defaultDir=cfg.UserFilesPath(),
                            defaultFile="", wildcard=wildcard, style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                path = dlg.GetPath()
                name = os.path.splitext(path)[0]
                with open(name + extension, 'w') as fp:
                    pickle.dump(SavedFile(self.system.GetSystemUid(), listCtrl.getDataItemsList()), fp)
                    cfg.LogFromOtherThread('File saved: ' + path)
                    fp.close()
            except (IOError, EOFError):
                errDlg = wx.MessageDialog(self.mainFrame, 'Error saving the file',
                               'Error',
                               wx.OK | wx.ICON_ERROR)
                errDlg.ShowModal()
                errDlg.Destroy()
        
        dlg.Destroy()
    
    def OnClose(self, event):
        '''
        Close the application
        '''
        dlg = wx.MessageDialog(self.mainFrame,
                               "Do you really want to Close this application?",
                               "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            cfg.userStopped = True
            self.timer.Stop()
            
            if cfg.commandsLogFile != None:
                cfg.commandsLogFile.close()
            
            cfg.logGraph.StopUpdates()
            if cfg.signalsLogFile != None:
                cfg.signalsLogFile.close()
                
            cfg.Close()

            self.mainFrame.Destroy()

    def OnComm(self, controllerName, connectionSetupFunc):
        '''
        Communication setup helper function
        '''
        dlg = wx.SingleChoiceDialog(
                self.mainFrame, 'Select the serial port', 'Connect ' + controllerName,
                SerialUtil().getSerialPortsList(),
                wx.CHOICEDLG_STYLE
                )

        if dlg.ShowModal() == wx.ID_OK:
            connectionSetupFunc(dlg.GetStringSelection())

        dlg.Destroy()
                
    def OnStopButton(self, evt):
        '''
        Respond to stop button being pressed
        '''
        cfg.userStopped = True
        dlg = wx.MessageDialog(self.mainFrame, 'Operation stopped!',
                               'Notification',
                               wx.OK | wx.ICON_INFORMATION
                               )
        result = dlg.ShowModal()
        dlg.Destroy()
        
    def OnAbout(self, evt):
        '''
        Show about dialog
        '''
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = self.system.name
        info.Version = self.system.version
        info.Copyright = "2014 University of Basel"
        info.Description = wx.lib.wordwrap.wordwrap(self.system.description + '\r\nThis software is based on the instrumentino package.', 
                                    350, wx.ClientDC(self.mainFrame))
        info.WebSite = ('http://www.chemie.unibas.ch/~hauser/index.html')
        info.Developers = [ "Joel Koenka" ]

        info.License = wx.lib.wordwrap.wordwrap(
            'This software is released under GPLv3.'
            'When using Instrumentino for a scientific publication, please cite the release article:\n'+
            'http://www.sciencedirect.com/science/article/pii/S0010465514002112'+
            'Get the code at: https://github.com/yoelk/instrumentino',
            500, wx.ClientDC(self.mainFrame))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)

    def MonitorUpdate(self, event):
        '''
        Read system variables' values from controllers
        '''
        for comp in self.sysComps:
            if cfg.IsCompOnline(comp):
                comp.Update()
        
        if cfg.AllOnline():
            self.logGraph.FinishUpdate()
            

class SavedFile(object):
    '''
    Describe a system dependent saved file
    '''
    def __init__(self, systemUid, list):
        self.systemUid = systemUid
        self.list = list


class Instrument():
    '''
    an instrument parent class
    '''
    def __init__(self, comps, actions, version='1.0', name='Instrument', description='Instrument\'s description'):
        self.comps = comps
        self.actions = actions
        self.version = version
        self.name = name
        self.description = description
        
        self.StartApp()

    def GetSystemUid(self):
        '''
        Return a unique id for the instrument
        '''
        return self.name + self.version + self.description
    
    def StartApp(self):
        '''
        Run application
        '''
        app = InstrumentinoApp(self)
        app.MainLoop()
        
#################################
if __name__ == '__main__':
    Instrument((AnalogPins('pins', (SysVarAnalogArduinoUnipolar('A0',[0,5],0,None, units='V'),)),), (SysAction('an action', (SysActionParamTime(),)),), '1', 'test', 'testing')