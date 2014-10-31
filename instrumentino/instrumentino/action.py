from __future__ import division
__author__ = 'yoelk'

from instrumentino import cfg
import wx
import time
import datetime
from executable_listctrl import RunnableItem

class SysActionParam(object):
    '''
    An action's parameter
    
    Sub-classes should maintain of self.maskedTextCtrl and implement:
    SetTextCtrl(parent) - Set the text controls for the parameter's value
    Get()               - Get the value from the text control
    '''
    def __init__(self, name, units='', value=''):
        self.name = name
        self.units = units
        self.value = value
        self.maskedTextCtrl = None
        
    def onKeyPress(self, event):
        '''
        Update the parameter's value when changed in panel
        '''
        self.value = self.maskedTextCtrl.GetValue()
        event.Skip()
        
    def __getstate__(self):
        '''
        Copy the object's state from self.__dict__ which contains
        all our instance attributes. Always use the dict.copy()
        method to avoid modifying the original state.
        '''
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        if 'maskedTextCtrl' in state:
            del state['maskedTextCtrl']
        return state


class SysActionParamInt(SysActionParam):
    '''
    An action's integer parameter
    '''
    def __init__(self, name, theRange, units='', value=0):
        SysActionParam.__init__(self, name, units, str(value))
        self.range = theRange
        
    def SetTextCtrl(self, parent):
        '''
        Set the text controls for the parameter's value
        '''
        self.maskedTextCtrl = wx.lib.masked.NumCtrl(parent, -1, self.value, 
                                             integerWidth=cfg.numIntegerPartWidth,
                                             fractionWidth=0,
                                             min=self.range[0],
                                             max=self.range[1])
        self.maskedTextCtrl.Bind(wx.EVT_KEY_UP, self.onKeyPress)
        return self.maskedTextCtrl
        
    def Get(self):
        '''
        Get the value from the text control
        '''
        return int(self.value)


class SysActionParamFloat(SysActionParam):
    '''
    An action's float parameter
    '''
    def __init__(self, sysVarAnalog=None, range=[0,0], name='', units='', value=0):
        if sysVarAnalog == None:            
            theName = name
            theRange = range
            theUnits = units
        else:
            theName = name if name != '' else sysVarAnalog.name
            theRange = range if range != [0,0] else sysVarAnalog.range
            theUnits = units if units != '' else sysVarAnalog.units
        
        SysActionParam.__init__(self, theName, theUnits, str(value))
        self.range = theRange
        
    def SetTextCtrl(self, parent):
        '''
        Set the text controls for the parameter's value
        '''
        self.maskedTextCtrl = wx.lib.masked.NumCtrl(parent, -1, self.value,
                                             integerWidth=cfg.numIntegerPartWidth,
                                             fractionWidth=cfg.numFractionPartWidth,
                                             min=self.range[0],
                                             max=self.range[1])
        self.maskedTextCtrl.Bind(wx.EVT_KEY_UP, self.onKeyPress)
        return self.maskedTextCtrl
        
    def Get(self):
        '''
        Get the value from the text control
        '''
        return float(self.value)


class SysActionParamTime(SysActionParam):
    '''
    An action's time parameter
    '''
    def __init__(self, name='Time', value='00:00:00.000'):
        SysActionParam.__init__(self, name, 'h:m:s.ms', value)
        
    def SetTextCtrl(self, parent):
        '''
        Set the text controls for the parameter's value
        '''
        self.maskedTextCtrl = wx.lib.masked.TextCtrl(parent, -1, '',
                                                     mask="##:##:##.###",
                                                     formatcodes='DF!',
                                                     defaultValue=str(self.value))
        self.maskedTextCtrl.Bind(wx.EVT_KEY_UP, self.onKeyPress)
        return self.maskedTextCtrl
        
    def Get(self):
        '''
        Get the value from the text control
        '''
        timeValue = time.strptime(self.value.split('.')[0], '%H:%M:%S')
        hours = timeValue.tm_hour
        minutes = timeValue.tm_min
        seconds = timeValue.tm_sec if len(self.value.split('.')) < 2 else timeValue.tm_sec + int(self.value.split('.')[1]) / 1000
        return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()


class SysAction(RunnableItem):
    '''
    A runnale action
    
    Sub-classes should implement:
    Command() - Run the command
    '''
    def __init__(self, name, params=()):
        self.name = name
        self.params = params
        self.paramsPanel = None
        self.commandFinished = False
        
    def __repr__(self):
        '''
        Return a printed representation for the action
        '''
        retVal = 'sysAction:\r' + 'name: ' + self.name + '\rparams:'
        for param in self.params:
            retVal += ' ' + param.name + '=' + str(param.value)
        return retVal
    
    def SetParamsPanel(self, parent):
        '''
        Set the parameters' panel
        '''
        paramsPanel = wx.Panel(parent)
        sizer = wx.GridSizer(0,2)
        for param in self.params:
            unitsStr = ' (' + param.units + ')' if param.units != '' else ''
            sizer.Add(wx.StaticText(paramsPanel, -1, param.name + unitsStr + ': '))
            sizer.Add(param.SetTextCtrl(paramsPanel), flag=wx.EXPAND)
        paramsPanel.SetSizer(sizer)
        
        return paramsPanel
    
    def Run(self, Log=True):
        '''
        Run the action
        '''
        if Log:
            logMsg = datetime.datetime.now().strftime('%X ')
            logMsg += self.name
            for idx, param in enumerate(self.params):
                if idx == 0:
                    logMsg += ': '
                else:
                    logMsg += ', '
                logMsg += param.name + '=' + str(param.value) 
            cfg.LogFromOtherThread(logMsg)

        # Call the sub-class' command function
        self.Command()