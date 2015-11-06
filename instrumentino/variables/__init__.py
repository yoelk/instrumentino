from __future__ import division
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty, OptionProperty
import time
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from instrumentino.cfg import *

class Variable(BoxLayout):
    '''An experimental variable, that is controlled/measured by hardware controllers connected to Instrumentino.
    Each variable has data channels that take care of reading/writing.
    Subclasses are responsible of screen presentation of the variable.
    '''

    name = StringProperty('a variable')
    '''The variable's name on the screen
    '''
    
    channel_in = ObjectProperty(None)
    '''The input channel
    '''
    
    channel_out = ObjectProperty(None)
    '''The output channel
    '''
    
    def __init__(self, **kwargs):
        super(Variable, self).__init__(**kwargs)
        
        # Let the channels keep a reference to us
        if set(['channel_in']) <= set(kwargs):
            self.channel_in.variable = self
            
        if set(['channel_out']) <= set(kwargs):
            self.channel_out.variable = self
            
    def percentage_to_variable_units(self, data_point):
        '''Incoming data is received from the input channel as a percentage.
        It needs to be translated to the variable's units.
        Return the translated data_point.
        
        Sub-classes should implement that
        '''
        pass
    
    def new_data_arrived(self, new_data_point):
        '''When new data arrived, we should update the variable's widget.
        '''
        self.value_display.text = str(self.percentage_to_variable_units(new_data_point))
        

class AnalogVariable(Variable):
    '''An analog variable
    '''

    upper_limit = NumericProperty()
    '''The upper limit this variable accepts
    '''
    
    lower_limit = NumericProperty()
    '''The lower limit this variable accepts
    '''
    
    units = StringProperty()
    '''The units of this variable
    '''

    def __init__(self, **kwargs):
        if not set(['range', 'units']) <= set(kwargs): raise MissingKwargsError()
        
        super(AnalogVariable, self).__init__(**kwargs)
        
        # Let the user define the limits as a range.
        the_range = kwargs.get('range', None)
        if the_range:
            self.upper_limit = the_range[1]
            self.lower_limit = the_range[0]


class AnalogVariableUnipolar(AnalogVariable):
    '''An analog variable for unipolar values
    '''

    def __init__(self, **kwargs):
        super(AnalogVariableUnipolar, self).__init__(**kwargs)
        
        # Check the range
        if self.upper_limit * self.lower_limit < 0: raise ValueError('Range should be unipolar')
        
    def percentage_to_variable_units(self, data_point):
        '''Return the data_point, translated to the variable's units.
        '''
        return self.lower_limit + (data_point / 100 * self.upper_limit)


class AnalogVariablePercentage(AnalogVariableUnipolar):
    '''An analog variable for percentage values
    '''

    def __init__(self, **kwargs):
        kwargs['range'] = [0, 100]
        kwargs['units'] = '%'        
        super(AnalogVariablePercentage, self).__init__(**kwargs)
        
        
class DigitalVariable(Variable):
    '''A digital variable
    '''

    options = ListProperty()
    '''The list of possible values, ordered from lowest to highest.
    '''
    
    def __init__(self, **kwargs):
        # Check initializers
        if not set(['options']) <= set(kwargs): raise MissingKwargsError()
        
        super(DigitalVariable, self).__init__(**kwargs)
        
    def percentage_to_variable_units(self, data_point):
        '''Return the data_point, translated to the variable's units.
        '''
        index = int(data_point / 100 * (len(self.options) - 1))
        return self.options[index]

class DigitalVariableOnOff(DigitalVariable):
    '''An On/Off digital variable.
    '''
    
    def __init__(self, **kwargs):
        kwargs['options'] = ['on', 'off']
        
        super(DigitalVariableOnOff, self).__init__(**kwargs)

