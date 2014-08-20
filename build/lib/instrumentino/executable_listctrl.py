from __future__ import division
__author__ = 'yoelk'

from instrumentino import cfg
import wx
from wx import xrc
from threading import Thread
import sys
import copy
from datetime import datetime
from collections import OrderedDict

from wx.lib.agw import ultimatelistctrl as ULC

class ExecutableListCtrl(object):
    '''
    A general list with add, delete and Run buttons. The same infrastructure for the actions' list and the methods' list
    '''
    def __init__(self, parent, panel, columnNumToName, runStartString, listDataItems=[]):
        self.columnNumToName = OrderedDict([(0, '#')] + columnNumToName.items())
        self.columnNameToNum = {v: k for k, v in self.columnNumToName.items()}
        self.runStartString = runStartString
        self.panel = panel
        self.runButton = (xrc.XRCCTRL(parent, 'runButton'))
        self.addButton = (xrc.XRCCTRL(parent, 'addButton'))
        self.removeButton = (xrc.XRCCTRL(parent, 'removeButton'))
        self.list = ULC.UltimateListCtrl(self.panel, agwStyle=wx.LC_REPORT 
                                         | wx.LC_VRULES
                                         | wx.LC_HRULES
                                         | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT
                                         | ULC.ULC_SINGLE_SEL)
        self.panel.GetSizer().Add(self.list, 1, wx.EXPAND|wx.ALL|wx.GROW)
        for idx, name in self.columnNumToName.items():
            columnInfo = ULC.UltimateListItem()
            columnInfo._mask = wx.LIST_MASK_TEXT
            columnInfo._text = name
            self.list.InsertColumnInfo(idx, columnInfo)
        
        if len(listDataItems) == 0:
            listDataItems = [self.getDefaultDataItem(),]
        self.populateList(listDataItems)
        self.listUpdate()
        
        parent.Bind(wx.EVT_BUTTON, self.onAddButton, id=xrc.XRCID('addButton'))
        parent.Bind(wx.EVT_BUTTON, self.onRemoveButton, id=xrc.XRCID('removeButton'))
        parent.Bind(wx.EVT_BUTTON, self.onRunButton, id=xrc.XRCID('runButton'))
        self.list.Bind(ULC.EVT_LIST_KEY_DOWN, self.onKeyPress)       

    def populateList(self, listDataItems):
        '''
        Populate the list with items. Delete old ones.
        '''
        self.list.Freeze()
        # Clear old list        
        item = self.list.GetNextItem(-1)
        while item != -1:
            self.removeListDataItem(item)
            item = self.list.GetNextItem(-1)
        
        # Add all elements
        for _, listDataItem in enumerate(listDataItems):
            self.addListDataItem(listDataItem)
                        
        self.list.Thaw()
        self.listUpdate()

    def listUpdate(self):
        '''
        Refresh the list on screen
        '''
        for idx in self.columnNumToName.keys():
            self.list.SetColumnWidth(idx, wx.LIST_AUTOSIZE)
        
        self.list.Update()
        self.panel.Refresh()

    def addListDataItem(self, listDataItem=None):
        '''
        Add a list item
        '''
        if listDataItem == None:
            listDataItem = self.getDefaultDataItem()
        if listDataItem == None:
            return
         
        insertIndex = self.list.GetFirstSelected() if self.list.GetFirstSelected() != -1 else sys.maxint
        index = self.list.InsertStringItem(insertIndex, '')
        self.list.SetStringItem(index, 0, str(index + 1))
        for col in self.columnNumToName.keys()[1:]:
            self.list.SetStringItem(index, col, '')
         
        item = self.list.GetItem(index, 1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(self.list)
        panel.SetSizer(sizer)
        panel.SetName(str(index + 1))
        sizer.Add(self.getFirstColumnWidget(panel, listDataItem), flag=wx.EXPAND)
        item.SetWindow(panel, expand=True)
        self.list.SetItem(item)
        self.list.SetItemData(index, [listDataItem,])
        
        self.setOtherColumns(index, listDataItem)
        
        self.listUpdate()
        self.updateListIndices()
     
    def removeListDataItem(self, index):
        '''
        Remove a list item
        '''
        if index != -1:
            self.list.Freeze()
            self.list.DeleteItem(index)
            
            self.updateListIndices()
            
            self.list.Thaw()
            self.listUpdate()
    
    def updateListIndices(self):
        '''
        Update the indices in the first column. Used when an item is deleted from the middle.
        '''
        index = self.list.GetNextItem(-1)
        if self.list.GetNextItem(index) != -1:
            while index != -1:
                self.list.SetStringItem(index, 0, str(index + 1))
                self.list.GetItemWindow(index, 1).SetName(str(index + 1))
                index = self.list.GetNextItem(index)
    
    def onAddButton(self, evt):
        '''
        User pressed the add button
        '''
        self.addListDataItem()
        
    def onRemoveButton(self, evt):
        '''
        User pressed the remove button
        '''
        self.removeListDataItem(self.list.GetFirstSelected())
    
    def onRunButton(self, evt):
        '''
        User pressed the Run button
        '''
        worker = RunListThread(self.list, self.runStartString)
        worker.start()
    
    def onKeyPress(self, event):
        '''
        User pressed a key while in the list area
        '''
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            self.removeListDataItem(self.list.GetFirstSelected())
        if keycode == ord('+'):
            self.addListDataItem()
        event.Skip()
        
    def getDataItemsList(self):
        '''
        Return the list's items
        '''
        listDataItems = []
        item = self.list.GetNextItem(-1)
        while item != -1:
            listDataItems.append(self.list.GetItemData(item)[0])
            item = self.list.GetNextItem(item)
            
        return listDataItems
    
    def getDefaultDataItem(self):
        '''
        Return an empty item. To be implemented by subclass.
        '''
        pass
     
    def getFirstColumnWidget(self, panel, listDataItem):
        '''
        Return the widget for the first column. To be implemented by subclass.
        '''
        pass
     
    def setOtherColumns(self, index, action):
        '''
        Set the other columns' content. To be implemented by subclass.
        '''
        pass
        

class RunnableItem(object):
    '''
    An item that can be Run (like an action or a method file)
    '''
    def Run(self):
        '''
        Run. To be implemented by subclass.
        '''
        pass

        
class RunListThread(Thread):
    '''
    Thread class that executes the items in a list
    '''
    def __init__(self, theList, runStartString='*** Run start ***'):
        Thread.__init__(self)
        self.runStartString = runStartString
        self.list = theList
 
    def getDataItemsAndItems(self):
        '''
        Return a double list of items and data items
        '''
        dataItemsAndItems = []
        item = self.list.GetNextItem(-1)
        while item != -1:
            dataItemsAndItems.append((self.list.GetItemData(item)[0], item))
            item = self.list.GetNextItem(item)
            
        return dataItemsAndItems
    
    def run(self):
        '''
        Run the list's items
        '''
        cfg.UpdateControlsFromOtherThread(True)
        cfg.LogFromOtherThread(self.runStartString)
        dataItemsAndItems = self.getDataItemsAndItems()
        for dataItem, item in dataItemsAndItems:
            self.list.Select(item, False)
            
        for dataItem, item in dataItemsAndItems:
            self.list.Select(item, True)
            dataItem.Run()
            if cfg.userStopped:
                cfg.userStopped = False
                break
            self.list.Select(item, False)
        
        cfg.UpdateControlsFromOtherThread(False)
        cfg.LogFromOtherThread('')