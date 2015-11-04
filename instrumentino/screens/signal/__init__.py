from __future__ import division
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, ObjectProperty, BoundedNumericProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from instrumentino import Graph, MeshLinePlot
import random
from instrumentino.variables import AnalogVariable, DigitalVariable
import itertools
from kivy.utils import get_color_from_hex as rgb
from instrumentino.libs.garden.graph import SmoothLinePlot
from math import sin, cos, pi
import numpy as np
import time
from instrumentino.screens import MyView

class MyGraph(Graph):
    pass

class MySignalView(BoxLayout, MyView):
    '''The Signal view presents the relevant experimental data graphically, and lets the user interact with it.
    '''
    # TODO: Handle cases in which the system clock was changed during operation.
    # In such cases, ignore the time change and notify the user when the clock was changed.
    # Also tell the user that from that point on the timestamp are not correct and it's better to restart the system.
    
    variables = ListProperty()
    '''The variables in the system.
    '''
    
    analog_variables = ListProperty()
    '''The analog variables in the system.
    '''
    
    digital_variables = ListProperty()
    '''The digital variables in the system.
    '''
    
    plots = ListProperty()
    '''The plotted lines.
    '''
    
    colors = itertools.cycle([rgb('7dac9f'), rgb('dc7062'), rgb('66a8d4'), rgb('e5b060')])
    '''Possible graph colors.    
    '''

    graph = MyGraph()
    '''The plotting area.
    '''
    
    screen_update_frequency = BoundedNumericProperty(20, min=1)
    '''How often is the graph updated. 20 Hz seems fast enough for the human eye.
    '''
    
    freeze_graph = BooleanProperty(False)
    '''In freeze mode, we don't show the user newly acquired data in order to browse older data. 
    '''
    
    seconds_to_show = BoundedNumericProperty(10, min=0)
    '''How many seconds of data are to be displayed.
    '''
    
    max_sampling_rate = NumericProperty()
    '''The maximal sampling rate between all of the channels
    '''
    
    def __init__(self, **kwargs):
        super(MySignalView, self).__init__(**kwargs)
        components = kwargs.get('components', [])
        
        # Init the plotting area
        self.graph.ymin = 0
        self.graph.ymax = 100
        
        # Populate variables' list with variables that have an input channel
        for comp in components:
            self.variables.extend([var for var in comp.variables if var.channel_in])
            
        self.analog_variables = [var for var in self.variables if isinstance(var, AnalogVariable)]
        self.digital_variables = [var for var in self.variables if isinstance(var, DigitalVariable)]
        
        for var in self.analog_variables:
            # Keep mutual references for bidirectional access.
            var.plot = SmoothLinePlot(color=next(self.colors))
            var.plot.variable = var
            self.plots.append(var.plot)
            self.max_sampling_rate = max(self.max_sampling_rate, var.channel_in.sampling_rate)

        for plot in self.plots:
            self.graph.add_plot(plot)
        
        # Periodically update signal view
        Clock.schedule_interval(self.update_screen, 1/self.screen_update_frequency)
        
    def update_screen(self, dt):
        '''Update the graph with new data
        '''
        # Update the time axis if necessary.
        if not self.freeze_graph:
            self.graph.xmax = time.time()
            self.graph.xmin = self.graph.xmax - self.seconds_to_show
        
        # TODO: for now the x data is given in whole seconds. it should be possible to zoom in and out.
        # TODO: support showing more than one data block
        for plot in self.plots:
            plot.points = plot.variable.channel_in.get_graph_series(self.graph.xmin, self.graph.xmax, self.max_sampling_rate)