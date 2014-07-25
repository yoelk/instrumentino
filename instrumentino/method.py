from __future__ import division
__author__ = 'yoelk'

import wx
from wx import xrc
import copy
import sys
from instrumentino import cfg
import pickle
import wx.lib.masked as  masked
from executable_listctrl import RunnableItem, ExecutableListCtrl

class SysMethod(RunnableItem):
    '''
    Descriptor for a method file to be Run
    '''
    def __init__(self, methodFileName='', repeat=1):
        self.methodFileName = methodFileName
        self.repeat = repeat

    def setRepeatPanel(self, parent):
        '''
        Set and return the repeat panel 
        '''
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(parent)
        panel.SetSizer(sizer)
        self.maskedTextCtrl = masked.NumCtrl(panel,
                                             value=self.repeat,
                                             integerWidth=cfg.numIntegerPartWidth,
                                             fractionWidth=0,
                                             min=0)
        self.maskedTextCtrl.Bind(wx.EVT_KEY_UP, self.onKeyPress)
        sizer.Add(self.maskedTextCtrl, 0, wx.EXPAND)
        return panel
        
    def onKeyPress(self, event):
        '''
        Update the repeat value when changed in panel
        '''
        self.repeat = self.maskedTextCtrl.GetValue()
        event.Skip()

    def checkSystemCompatibility(self, filename):
        '''
        Check if the file was created by this system
        '''
        if filename != '':
            try:
                fp = file(filename, 'r')
                savedFile = pickle.load(fp)
                if savedFile.systemUid != cfg.systemUid:
                    filename = ''
                    errDlg = wx.MessageDialog(cfg.mainFrame, 'File incompatible with this system',
                                              'Error',
                                              wx.OK | wx.ICON_ERROR)
                    errDlg.ShowModal()
                    errDlg.Destroy()
                    return False
                    
            except (IOError, EOFError):
                errDlg = wx.MessageDialog(cfg.mainFrame, 'Error loading the file',
                                          'Error',
                                          wx.OK | wx.ICON_ERROR)
                errDlg.ShowModal()
                errDlg.Destroy()
                return False
                
            fp.close()
            return True
        else:    
            return True

    def onPathChanged(self, evt):
        '''
        Update the file name when changed in panel
        '''
        filename = evt.GetString()
        if self.checkSystemCompatibility(filename):
            self.methodFileName = filename
        else:
            evt.GetEventObject().SetValue('')
                 
    def Run(self):
        '''
        Run the method
        '''        
        fp = file(self.methodFileName, 'r')
        savedFile = pickle.load(fp)
        actions = savedFile.list
        cfg.LogFromOtherThread('--- ' + self.methodFileName + ' ---')
        for idx in range(self.repeat):
            if self.repeat > 1:
                cfg.LogFromOtherThread('Run no. ' + str(idx + 1))
            for action in actions:
                action.Run()
                if cfg.userStopped:
                    return
                
    def __getstate__(self):
        '''
        Copy the object's state from self.__dict__ which contains
        all our instance attributes. Always use the dict.copy()
        method to avoid modifying the original state.
        '''
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state['maskedTextCtrl']
        return state


class ActionsListCtrl(ExecutableListCtrl):
    '''
    A list of actions to be Run
    '''
    def __init__(self, parent, availableActions, actions=[]):
        self.availableActions = availableActions
        self.availableActionsDict = {action.name: action for action in self.availableActions}
        ExecutableListCtrl.__init__(self, parent, xrc.XRCCTRL(parent, 'actionsListPanel'), {1: 'Action', 2: 'Parameters'}, '--- Run method ---', actions) 
   
    def getDefaultDataItem(self):
        '''
        Return an empty action item
        '''
        return copy.deepcopy(self.availableActions[0]) if len(self.availableActions) > 0 else None 
     
    def getFirstColumnWidget(self, panel, listDataItem):
        '''
        Return the widget for the first column (a choice in this case)
        '''
        choice = wx.Choice(panel, -1, choices=[availableAction.name for availableAction in self.availableActions])
        choice.SetStringSelection(listDataItem.name)
        choice.Bind(wx.EVT_CHOICE, self.onActionChange)
        return choice 
     
    def setOtherColumns(self, index, listDataItem):
        '''
        Set the other columns' content
        '''
        item = self.list.GetItem(index, self.columnNameToNum['Parameters'])
        item.SetWindow(listDataItem.SetParamsPanel(self.list), expand=True)
        self.list.SetItem(item)
     
    def onActionChange(self, event):
        '''
        Change the action when changed in the panel
        '''
        action = copy.deepcopy(self.availableActionsDict[event.GetString()])
        index = int(event.GetEventObject().GetParent().GetName()) - 1
        self.list.GetItemData(index).pop()
        self.list.GetItemData(index).append(action)
        self.setOtherColumns(index, action)
        self.listUpdate()
