from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty, OptionProperty
import time
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner

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

class AnalogVariable(Variable):
    '''An analog variable
    '''

    upper_limit = NumericProperty(100)
    '''The upper limit this variable accepts
    '''
    
    lower_limit = NumericProperty(0)
    '''The lower limit this variable accepts
    '''
    
    units = StringProperty('%')
    '''The units of this variable
    '''

    def __init__(self, **kwargs):
        super(AnalogVariable, self).__init__(**kwargs)
        
        # Let the user define the limits as a range.
        the_range = kwargs.get('range', None)
        if the_range:
            self.upper_limit = the_range[1]
            self.lower_limit = the_range[0]

class DigitalVariable(Variable):
    '''A digital variable
    '''

    options_dict = DictProperty({'???': None})
    '''Translate between the options the user sees and the actual values used with the data channels.
    '''
    
    def __init__(self, **kwargs):
        super(DigitalVariable, self).__init__(**kwargs)

class DigitalVariableOnOff(DigitalVariable):
    '''An On/Off digital variable.
    '''
    
    def __init__(self, **kwargs):
        options_dict = {'On': 'on',
                        'Off': 'off'}
        kwargs['options_dict'] = options_dict
        
        super(DigitalVariableOnOff, self).__init__(**kwargs)

