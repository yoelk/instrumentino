from __future__ import division
__author__ = 'yoelk'
from datetime import datetime
import wx
from wx import xrc
from instrumentino.comp import SysVarAnalog, SysVarDigital
from instrumentino import cfg
from itertools import cycle
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, SecondLocator,\
    AutoDateFormatter, AutoDateLocator

class Data():
    '''
    A class to describe collected data
    '''
    def __init__(self):
        self.data = []

class AnalogData(Data):
    '''
    A class to describe collected analog data
    '''
    def __init__(self, yRange):
        Data.__init__(self)
        self.yRange = yRange

class LogGraphPanel(wx.Panel):
    '''
    A panel with a log graph
    adapted from examples by Eli Bendersky (eliben@gmail.com)
    '''
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

        # set figure
        self.dpi = 100
        self.figure, self.axes = plt.subplots()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        
        self.axes.set_xlabel('time', fontsize=12)
        self.axes.set_ylabel('percent (%) - dashed line for negative values', fontsize=12)
        self.axes.set_ybound(0,100)
        self.axes.xaxis_date()
        self.axes.get_xaxis().set_ticks([])
        self.axes.set_axis_bgcolor('white')
        
        self.figure.canvas.mpl_connect('pick_event', self.OnPick)

        # Show on screen
        self.controllersHBox = wx.BoxSizer(wx.HORIZONTAL)
        self.controllersHBox.Add(self.cb_freeze, 0)
        self.controllersHBox.AddSpacer(30)
        self.controllersHBox.Add(self.slider_label, 0)
        self.controllersHBox.Add(self.slider_zoom, 1)
        self.controllersHBox.Add(self.toolbar, 0, wx.EXPAND | wx.ALIGN_LEFT)
                
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.EXPAND | wx.GROW | wx.ALL)
        self.vbox.Add(self.controllersHBox, 0, wx.EXPAND)
                
        # fit all to screen
        self.parent.GetSizer().Add(self, 1, wx.EXPAND | wx.GROW | wx.ALL)
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)
                
        # order data sources
        self.lastTime = None
        self.time = []
        self.realAnalogData = {}
        self.plottedAnalogData = {}
        self.digitalData = {}
        self.allRealData = {}
        self.plottedLines = {}
        variableNamesOnLegend = []
        colors = ['b', 'g', 'r', 'c', 'm', 'b', 'y']
        colorCycler = cycle(colors)
        lineWidths = [1]*len(colors)+[2]*len(colors)+[4]*len(colors)
        lineWidthCycler = cycle(lineWidths)
        for comp in self.sysComps:
            for var in comp.vars.values():
                if not var.showInSignalLog:
                    continue
                
                name = var.FullName()
                if isinstance(var, SysVarAnalog):
                    variableNamesOnLegend += [name]
                    self.realAnalogData[name] = AnalogData(var.range)
                    color = next(colorCycler)
                    lineWidth = next(lineWidthCycler)
                    if var.showInSignalLog:
                        nameOnLegend = name + ' [' + str(var.range[0]) + ',' + str(var.range[1]) + ']'
                        graphVisible = True
                    else:
                        nameOnLegend = None
                        graphVisible = False
                    if not self.hasBipolarRange(name):
                        self.plottedAnalogData[name] = AnalogData(var.range)
                        self.plottedLines[name] = self.axes.plot(self.time, self.plottedAnalogData[name].data,
                                                                 '-', lw=lineWidth, color=color, label=nameOnLegend, visible=graphVisible)[0]
                            
                    else:
                        # split this variable to two unipolar variables for the sake of plotting
                        self.plottedAnalogData[name+'_POS'] = AnalogData([0,var.range[1]])
                        self.plottedAnalogData[name+'_NEG'] = AnalogData([var.range[0],0])
                        
                        self.plottedLines[name+'_POS'] = self.axes.plot(self.time, self.plottedAnalogData[name+'_POS'].data,
                                                                        '-', lw=lineWidth, color=color, label=nameOnLegend, visible=graphVisible)[0]
                        self.plottedLines[name+'_NEG'] = self.axes.plot(self.time, self.plottedAnalogData[name+'_NEG'].data,
                                                                        '--', lw=lineWidth, color=color, visible=graphVisible)[0]
                    
                # digital data isn't plotted
                if isinstance(var, SysVarDigital):
                    self.digitalData[name] = Data()
                
        self.allRealData.update(self.realAnalogData)
        self.allRealData.update(self.digitalData)
        
        # finalize legend
        self.axes.set_ybound(0,100)
        leg = self.axes.legend(loc='upper left', fancybox=True, shadow=True)
        leg.get_frame().set_alpha(0.4)
        self.lineLegendDict = {}
        for legline, lineName in zip(leg.get_lines(), variableNamesOnLegend):
            legline.set_picker(5)  # 5 pts tolerance
            self.lineLegendDict[legline] = lineName
        
        self.lineLegendDictReverseDict = {v: k for k, v in self.lineLegendDict.items()}

    def HideVariableFromLog(self, name):
        if not self.hasBipolarRange(name):
            plottedLines = [self.plottedLines[name]]
        else:
            plottedLines = [self.plottedLines[name+'_POS'],
                            self.plottedLines[name+'_NEG']]
            
        vis = not plottedLines[0].get_visible()
        for line in plottedLines:
            line.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines
        # have been toggled
        legendLine = self.lineLegendDictReverseDict[name]
        if vis:
            legendLine.set_alpha(1.0)
        else:
            legendLine.set_alpha(0.2)
        self.figure.canvas.draw()

    def OnPick(self, event):
        # on the pick event, find the orig line corresponding to the
        # legend proxy line, and toggle the visibility
        legendLine = event.artist
        name = self.lineLegendDict[legendLine]
        self.HideVariableFromLog(name)
        

    def hasBipolarRange(self, name):
        return self.realAnalogData[name].yRange[0] * self.realAnalogData[name].yRange[1] < 0

    def NormalizePositiveValue(self, value, yRange):
        # unipolar range [X, Y] or [-X, -Y]
        relevantEdge = yRange[0] if yRange[0] >= 0 else yRange[1]
        return abs(value - relevantEdge) / abs(yRange[1] - yRange[0]) * 100
        
    def AddData(self, name, value):
        # keep all data arrays the same length. the time array should be updated last
        if len(self.allRealData[name].data) <= len(self.time):
            if value == None:
                value = self.allRealData[name].data[-1] if len(self.allRealData[name].data) > 0 else 0
                
            self.allRealData[name].data += [value]
            if name in self.realAnalogData.keys():
                if not self.hasBipolarRange(name):
                    normVal = self.NormalizePositiveValue(value, self.plottedAnalogData[name].yRange)
                    self.plottedAnalogData[name].data += [normVal]
                else:
                    normPosVal = self.NormalizePositiveValue(value, self.plottedAnalogData[name+'_POS'].yRange)
                    normNegVal = self.NormalizePositiveValue(value, self.plottedAnalogData[name+'_NEG'].yRange)
                    self.plottedAnalogData[name+'_POS'].data += [normPosVal if value>=0 else None]
                    self.plottedAnalogData[name+'_NEG'].data += [normNegVal if value<0 else None]
            
    def FinishUpdate(self):
        self.time += [datetime.now()]

        # write a header with variable names
        if len(self.time) == 1:
            cfg.signalsLogFile.write('time,' + str(self.allRealData.keys())[1:-1] + '\r')
            
        # update the signals' file once in a while
        if len(self.time) % self.dataWriteBulk == 0:
            for idx in range(-1*self.dataWriteBulk,0):
                cfg.signalsLogFile.write(str(self.time[idx].strftime('%H:%M:%S.%f')) + ',' + str([v.data[idx] for v in self.allRealData.values()])[1:-1] + '\r')
                        
        # only show the graph when there's at least 2 data points
        if len(self.time) < 2:
            return
        self.Redraw(len(self.time) == 2)

    def StopUpdates(self):
        for idx in range(-1*(len(self.time) % self.dataWriteBulk),0):
            cfg.signalsLogFile.write(str(self.time[idx].strftime('%H:%M:%S.%f')) + ',' + str([v.data[idx] for v in self.allRealData.values()])[1:-1] + '\r')
            
        plt.close()
    
    def Redraw(self, firstTime=False):
        """ Redraws the figure
        """
            
        if not self.cb_freeze.IsChecked():
            self.axes.set_xbound(lower=self.time[max(0,len(self.time)-int(self.slider_zoom.GetValue() * 60 * cfg.app.updateFrequency))],
                                                 upper=self.time[-1])
        
        for name in self.plottedAnalogData.keys():
            self.plottedLines[name].set_ydata(np.append(self.plottedLines[name].get_ydata(), self.plottedAnalogData[name].data[-1]))
            self.plottedLines[name].set_xdata(np.append(self.plottedLines[name].get_xdata(), self.time[-1]))

        if firstTime:
            self.axes.get_xaxis().set_major_formatter(DateFormatter('%H:%M'))
            self.axes.get_xaxis().set_major_locator(MinuteLocator())
            self.axes.set_ybound(0,100)
                        
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
