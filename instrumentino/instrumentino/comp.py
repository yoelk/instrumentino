from __future__ import division
__author__ = 'yoelk'

from instrumentino import cfg
import wx
from wx import xrc
import wx.lib.masked as  masked
import time
from collections import OrderedDict

class SysVar(object):
    '''
    A system variable
    
    Sub-classes should implement:
    - Update()         -    Update the display panel and the log graph for this variable
    - GetFunc()        -    read the value of the variable from the hardware
    - SetFunc(value)   -    Set the value of the variable in the hardware
    - OnEdit(event)    -    called when the display panel of the variable is edited
    '''
    def __init__(self, name, controllerClass, compName='', helpLine='', editable=True, PreSetFunc=None, PostGetFunc=None):
        self.name = name
        self.compName = compName
        self.controllerClass = controllerClass
        self.helpLine = helpLine
        self.editable = editable
        self.widget = None
        self.PreSetFunc = PreSetFunc
        self.PostGetFunc = PostGetFunc

    def Get(self):
        '''
        Call the sub-class' GetFunc()
        '''
        value = self.GetFunc()
        if self.PostGetFunc != None:
            self.PostGetFunc(value)
        return value
    
    def Set(self, value):
        '''
        Call the sub-class' SetFunc()
        '''
        if self.editable:
            if self.PreSetFunc != None:
                self.PreSetFunc(value)                
            self.SetFunc(value)
            
    def Update(self):
        value = self.Get()
        self.UpdatePanel(value)
        cfg.logGraph.AddData(self.FullName(), value)
            
    def FullName(self):
        unitsStr = ' (' + self.units + ')' if hasattr(self, 'units') else ''
        compStr = self.compName + ': ' if self.compName != '' else '' 
        return compStr + self.name + unitsStr
    
    def GetController(self):
        '''
        Get the working instance of the appropriate controller
        '''
        return cfg.GetController(self.controllerClass)

class SysVarAnalog(SysVar):
    '''
    An analog variable (float), represented by a wx.TextCtrl on the display
    
    Sub-classes should implement:
    - GetFunc()        -    read the value of the variable from the hardware
    - SetFunc(value)   -    Set the value of the variable in the hardware
    '''
    def __init__(self, name, range, controllerClass, compName='', helpLine='', editable=True, units='', PreSetFunc=None, PostGetFunc=None):
        SysVar.__init__(self, name, controllerClass, compName, helpLine, editable, PreSetFunc, PostGetFunc)
        self.units = units
        self.range = range
        self.monitorTextCtrl = None
        self.editTextCtrl = None
        
    def UpdatePanel(self, value):
        '''
        Update the variable's panel with newly read data
        '''
        if self.monitorTextCtrl != None and value != None:
            self.monitorTextCtrl.ChangeValue(value)

    def OnEdit(self, event):
        '''
        Set the variable's value from the user's input
        '''
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            value = float(event.GetEventObject().GetValue())
            if self.range[0] <= value <= self.range[1]:
                self.Set(value)
        event.Skip()
        
    def CreatePanel(self, parent):
        '''
        Create a panel to represent the variable
        '''
        rows = 2 if self.editable else 1
        sizer = wx.FlexGridSizer(rows=rows, cols=2)
        panel = wx.Panel(parent)
        panel.SetSizer(sizer)
        sizer.Add(wx.StaticText(panel, label=self.name + ' (' + self.units + '):'))
        self.monitorTextCtrl = masked.NumCtrl(panel,
                                              value=0,
                                              integerWidth=cfg.numIntegerPartWidth,
                                              fractionWidth=cfg.numFractionPartWidth,
                                              min=self.range[0],
                                              max=self.range[1],
                                              style=wx.TE_CENTRE | wx.TE_READONLY) 
        sizer.Add(self.monitorTextCtrl)
        if self.editable:
            sizer.Add(wx.StaticText(panel, label='Set to:'))
            editTextCtrl = masked.NumCtrl(panel,
                                          value=0,
                                          integerWidth=cfg.numIntegerPartWidth,
                                          fractionWidth=cfg.numFractionPartWidth,
                                          min=self.range[0],
                                          max=self.range[1],
                                          style=wx.TE_CENTRE | wx.WANTS_CHARS)
            editTextCtrl.Bind(wx.EVT_KEY_DOWN, self.OnEdit)
            sizer.Add(editTextCtrl)

        return panel
            

class SysVarDigital(SysVar):
    '''
    A digital variable (multiple choice), represented by a Set of wx.RadioButtons on the display
    
    Sub-classes should implement:
    - GetFunc()        -    read the value of the variable from the hardware
    - SetFunc(value)   -    Set the value of the variable in the hardware
    '''
    def __init__(self, name, states, controllerClass, compName='', helpLine='', editable=True, PreSetFunc=None, PostGetFunc=None):
        SysVar.__init__(self, name, controllerClass, compName, helpLine, editable, PreSetFunc, PostGetFunc)
        self.radioButtons = None
        self.states = states
        
    def UpdatePanel(self, value):
        '''
        Update the variable's panel with newly read data
        '''
        if self.radioButtons != None and value != None:
            try:
                for rbName, rb in self.radioButtons.items():
                    rb.SetValue(rbName == value)
            except:
                pass
    
    def OnEdit(self, event):
        '''
        Set the variable's value from the user's input
        '''
        self.Set(event.GetEventObject().GetLabel())

    def CreatePanel(self, parent):
        '''
        Create a panel to represent the variable
        '''
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(parent)
        panel.SetSizer(sizer)
        self.radioButtons = {}
        sizer.Add(wx.StaticText(panel, label=self.name + ':'))
        for state in self.states:
            radioButton = wx.RadioButton(panel, label=state)
            sizer.Add(radioButton)
            self.radioButtons[state] = radioButton
            panel.Bind(wx.EVT_RADIOBUTTON, self.OnEdit, radioButton)

        return panel

    
class SysComp(object):
    '''
    A system component, which has variables, and is represented on the screen as a panel containing the variables' panels
    '''
    def __init__(self, name, vars, controllerClass, helpLine=''):
        self.name = name
        self.controllerClass = controllerClass
        self.helpLine = helpLine
        self.vars = OrderedDict([(var.name, var) for var in vars])
        self.panel = None
        self.online = False
        
    def CreatePanel(self, parent):
        '''
        Create a panel for the component, based on its variables
        
        Sub-classes may implement FirstTimeOnline() to do some initialization when communication is established
        '''
        vars = self.vars.values()
        if len(vars) == 0:
            return None
        
        self.panel = wx.Panel(parent)
        staticBox = wx.StaticBox(self.panel, label=self.name)
        sizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        self.panel.SetSizer(sizer)
        for var in vars[0:-1]:
            sizer.Add(var.CreatePanel(self.panel))
            sizer.Add(wx.StaticLine(self.panel), flag=wx.EXPAND)
        sizer.Add(vars[-1].CreatePanel(self.panel))

        return self.panel
    
    def Update(self):
        '''
        Update all variables
        '''
        if self.online == False:
            self.online = True
            self.FirstTimeOnline()

        if self.panel != None:
            for var in self.vars.values():
                var.Update()

    def FirstTimeOnline(self):
        '''
        Called when communication is first setup. To be implemented by subclass.
        '''
        pass
                
    def Enable(self, isEnabled):
        '''
        Enable/disable the availability of the panel on the screen
        '''
        if self.panel != None:
            self.panel.Enable(isEnabled)
            
    def GetController(self):
        '''
        Get the working instance of the appropriate controller
        '''
        return cfg.GetController(self.controllerClass)