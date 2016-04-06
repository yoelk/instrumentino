from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from instrumentino.screens import MyView
import time
from kivy.app import App
from instrumentino.cfg import *
from instrumentino.variables import AnalogVariablePercentage,\
    DigitalVariableOnOff

class Component(BoxLayout):
    '''An Instrumentino component, hosting variables.
    '''
    
    name = StringProperty()
    '''The variable's name on the screen
    '''
    
    variables = ListProperty([])
    '''The list of variables in the component
    '''
    
    def __init__(self, **kwargs):
        # Set a default name
        self.name = self.name or create_default_name(self)
        
        super(Component, self).__init__(**kwargs)
        
        # Add all of the variable widgets
        for var in self.variables:
            self.add_widget(var)

    def add_variable(self, variable):
        self.variables.append(variable)

    def build(self):
        '''Add here the component variables. This should be overriden by derived classes
        '''


class AnalogVariables(Component):
    '''An array of analog input variables
    '''
    
    def __init__(self, **kwargs):
        ch_class = kwargs.get('ch_class', None)
        controller = kwargs.get('controller', None)
        channels_numbers = kwargs.get('channels_numbers', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        for i in channels_numbers:
            ch_in = ch_class(controller=controller, number=i, sampling_rate=sampling_rate)
            self.add_variable(AnalogVariablePercentage(name='Analog '+str(i), channel_in=ch_in))
        
        super(AnalogVariables, self).__init__(**kwargs)


class DigitalVariables(Component):
    '''An array of digital input/output variables
    '''
    
    def __init__(self, **kwargs):
        ch_class = kwargs.get('ch_class', None)
        controller = kwargs.get('controller', None)
        channels_numbers = kwargs.get('channels_numbers', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        for i in channels_numbers:
            ch = ch_class(controller=controller, number=i, sampling_rate=sampling_rate)
            self.add_variable(DigitalVariableOnOff(name='Digital '+str(i), channel_in=ch, channel_out=ch))

        super(DigitalVariables, self).__init__(**kwargs)
