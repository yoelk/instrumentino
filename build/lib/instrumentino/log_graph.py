from __future__ import division
__author__ = 'yoelk'
from datetime import datetime
import wx
from wx import xrc
from instrumentino.comp import SysVarAnalog, SysVarDigital
from instrumentino import cfg

import matplotlib
from matplotlib.dates import DateFormatter, MinuteLocator, SecondLocator,\
    AutoDateFormatter, AutoDateLocator
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib import pyplot as plt
import pylab as pl
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

class LogGraphPanel(wx.Panel):
    '''
    A panel with a log graph
    adapted from examples by Eli Bendersky (eliben@gmail.com)
    '''
    
    maxShownAxes = 4
    
    def __init__(self, parent, sysComps):
        '''
        Creates the main panel with all the controls on it
        '''
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.sysComps = sysComps
        self.dataWriteBulk = 10

        # add controls
        self.cb_freeze = wx.CheckBox(self, -1, "Freeze")
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_freeze, self.cb_freeze)
        self.slider_label = wx.StaticText(self, -1, "Zoom (min): ")
        self.slider_zoom = wx.Slider(self, -1, value=1, minValue=1, maxValue=60, style=wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_zoom.SetTickFreq(10, 1)
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.on_slider_width, self.slider_zoom)
        
        # set main plot
        self.dpi = 100
        self.axisSeparation = 45
        self.mainAxes = host_subplot(111, axes_class=AA.Axes)
        pl.gca().axes.get_yaxis().set_ticks([])
        self.mainAxes.xaxis_date()
        self.canvas = FigCanvas(self, -1, pl.gcf())
        self.toolbar = NavigationToolbar(self.canvas)

        # set individual data lines
        self.lastTime = None
        self.time = []
        self.analogData = {}
        self.analogPlotData = {}
        self.yRange = {}
        self.digitalData = {}
        self.allData = {}
        self.analogAxes = {}
        plotNum = 0
        for comp in self.sysComps:
            for var in comp.vars.values():
                name = var.FullName()
                if isinstance(var, SysVarAnalog):
                    self.analogData[name] = []
                    self.yRange[name] = var.range
                    self.analogAxes[name] = self.mainAxes.twinx()
                    self.analogAxes[name].axis["right"] = self.analogAxes[name].get_grid_helper().new_fixed_axis(loc="right",
                                                                                                                 axes=self.analogAxes[name],
                                                                                                                 offset=(plotNum*self.axisSeparation, 0))
                    plotNum += 1
                    
                if isinstance(var, SysVarDigital):
                    self.digitalData[name] = []
                
        self.allData.update(self.analogData)
        self.allData.update(self.digitalData)
        
        # modify the main plot
        plt.subplots_adjust(right=1-(0.085*min(self.maxShownAxes, len(self.analogData))))
        self.mainAxes.set_axis_bgcolor('white')
        pl.setp(self.mainAxes.get_xticklabels(), fontsize=8)
        pl.setp(self.mainAxes.get_yticklabels(), fontsize=8)
        
        # Show on screen
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.cb_freeze, 0)
        self.hbox.AddSpacer(30)
        self.hbox.Add(self.slider_label, 0)
        self.hbox.Add(self.slider_zoom, 1)
        self.hbox.Add(self.toolbar, 0, wx.EXPAND | wx.ALIGN_LEFT)
                
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.EXPAND | wx.GROW | wx.ALL)
        self.vbox.Add(self.hbox, 0, wx.EXPAND)
                
        # fit all to screen
        self.parent.GetSizer().Add(self, 1, wx.EXPAND | wx.GROW | wx.ALL)
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
    def AddData(self, name, value):
        # keep all data arrays the same length. the time array should be updated last
        if len(self.allData[name]) <= len(self.time):
            if value == None:
                value = self.allData[name][-1] if len(self.allData[name]) > 0 else 0
                
            self.allData[name] += [value]
            
    def FinishUpdate(self):
        self.time += [datetime.now()]

        # write a header with variable names
        if len(self.time) == 1:
            cfg.signalsLogFile.write('time,' + str(self.allData.keys())[1:-1] + '\r')
            
        # update the signals' file once in a while
        if len(self.time) % self.dataWriteBulk == 0:
            for idx in range(-1*self.dataWriteBulk,0):
                cfg.signalsLogFile.write(str(self.time[idx].strftime('%H:%M:%S.%f')) + ',' + str([v[idx] for v in self.allData.values()])[1:-1] + '\r')
                        
        # only show the graph when there's at least 2 data points
        if len(self.time) < 2:
            return
        self.Redraw(len(self.time) == 2)

    def StopUpdates(self):
        for idx in range(-1*(len(self.time) % self.dataWriteBulk),0):
            cfg.signalsLogFile.write(str(self.time[idx].strftime('%H:%M:%S.%f')) + ',' + str([v[idx] for v in self.allData.values()])[1:-1] + '\r')
            
        # close extra plotting window
        pl.close()
    
    def Redraw(self, firstTime=False):
        """ Redraws the figure
        """
        if firstTime:
            self.mainAxes.get_xaxis().set_major_formatter(DateFormatter('%H:%M'))
            self.mainAxes.get_xaxis().set_major_locator(MinuteLocator())
        
        for name in self.analogData.keys():
            if firstTime:
                self.analogPlotData[name] = self.analogAxes[name].plot(self.time, self.analogData[name], linewidth=1)[0]
                
                self.analogAxes[name].axis["right"].label.set_color(self.analogPlotData[name].get_color())
                self.analogAxes[name].axis["right"].toggle(all=True)
                self.analogAxes[name].set_ylabel(name)
            
            if not self.cb_freeze.IsChecked():
                self.analogAxes[name].set_xbound(lower=self.time[max(0,len(self.time)-int(self.slider_zoom.GetValue() * 60 * cfg.app.updateFrequency))],
                                                 upper=self.time[-1])
                self.analogAxes[name].set_ybound(lower=self.yRange[name][0],
                                                 upper=self.yRange[name][1])
                
            self.analogPlotData[name].set_xdata(self.time)
            self.analogPlotData[name].set_ydata(self.analogData[name])
        
        pl.setp(self.mainAxes.get_xticklabels(), visible=True)
        
        self.canvas.draw()
    
    def on_cb_freeze(self, event):
        self.Redraw()
    
    def on_slider_width(self, event):
        self.Redraw()

##############################
class SimpleFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.panel = LogGraphPanel(self, [])

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = SimpleFrame()
    app.frame.Show()
    app.MainLoop()
