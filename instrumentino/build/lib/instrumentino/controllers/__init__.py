from __future__ import division
from instrumentino.util import SerialUtil
__author__ = 'yoelk'

from instrumentino import cfg
import serial
import wx

class InstrumentinoController(object):
    '''
    base class for instrumentino compatible controllers
    '''
    
    def __init__(self, name):
        '''
        init
        '''
        self.name = name
        self.online = False
        
    def __str__(self):
        return self.name + " is on port %s" %(self.serial.port)

    def OnMenuConnect(self, event):
        '''
        Select a comm port to connect to
        '''
        dlg = wx.SingleChoiceDialog(
                cfg.mainFrame, 'Select the serial port', 'Connect ' + self.name,
                SerialUtil().getSerialPortsList(),
                wx.CHOICEDLG_STYLE
                )

        if dlg.ShowModal() == wx.ID_OK:
            self.online = self.Connect(dlg.GetStringSelection())
            cfg.UpdateControlsFromOtherThread()
            return self.online

        dlg.Destroy()

    def Connect(self, port):
        '''
        Connect to the controller. To be implemented by subclass.
        Returns - True (for succesful connection) or False
        '''
        pass
    
    def Close(self):
        '''
        Close the connection to the controller. To be implemented by subclass.
        '''
        pass