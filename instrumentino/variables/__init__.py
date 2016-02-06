from __future__ import division
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty, OptionProperty, BooleanProperty
import time
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from instrumentino.cfg import *
import re
from kivy.uix.textinput import TextInput

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
    
    user_is_editing = BooleanProperty(False)
    '''Is the user currently editing the variable's value.
    This attribute should be updated by sub-classes.
    '''
    
    def __init__(self, **kwargs):
        super(Variable, self).__init__(**kwargs)
        
        # Let the channels keep a reference to us
        if self.channel_in:
            self.channel_in.variable = self
            
        if self.channel_out:
            self.channel_out.variable = self
            
    def percentage_to_text(self, data_point):
        '''Incoming data is received from the input channel as a percentage.
        It needs to be translated to the variable's units and be presented as text on the screen.
        Return the percentage, translated to the variable's units, as text.
        
        Sub-classes should implement that
        '''
        pass
    
    def text_to_percentage(self, user_input):
        '''Translate a data_point from the variable's units to a percentage in its range.
        Return the user_input, translated to percentage.
        
        Sub-classes should implement that
        '''
        pass

    def user_entered_value(self, text):
        '''When the user sets the variable's value, act upon it and write it to the controller.
        '''
        if self.channel_out:
            self.channel_out.write(self.text_to_percentage(text))

    def new_data_arrived(self, new_data_point):
        '''When new data arrived, we should update the variable's widget.
        '''
        
        # Don't update the text while the user is editing
        if not self.user_is_editing:
            self.value_display.text = self.percentage_to_text(new_data_point)
        

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
        check_for_necessary_attributes(self, ['range', 'units'], kwargs)
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
        
    def percentage_to_text(self, data_point):
        '''Return the percentage, translated to the variable's units, as text.
        '''
        return '{:2.2f}'.format(self.lower_limit + (data_point / 100 * self.upper_limit))
    
    def text_to_percentage(self, user_input):
        '''Return the user_input, translated to percentage.
        '''
        return (float(user_input) - self.lower_limit) / (self.upper_limit - self.lower_limit) * 100


class AnalogVariablePercentage(AnalogVariableUnipolar):
    '''An analog variable for percentage values
    '''

    range = [0, 100]
    units = '%'
    '''Set necessary attributes.
    '''
    
    def __init__(self, **kwargs):
        super(AnalogVariablePercentage, self).__init__(**kwargs)
        
        
class DigitalVariable(Variable):
    '''A digital variable
    '''

    options = ListProperty()
    '''The list of possible values, ordered from lowest to highest.
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['options'], kwargs)
        super(DigitalVariable, self).__init__(**kwargs)
        
    def percentage_to_text(self, data_point):
        '''Return the percentage, translated to the variable's units, as text.
        '''
        index = int(data_point / 100 * (len(self.options) - 1))
        return self.options[index]

    def text_to_percentage(self, user_input):
        '''Return the user_input, translated to percentage.
        '''
        return self.options.index(user_input) / (len(self.options) - 1) * 100


class DigitalVariableOnOff(DigitalVariable):
    '''An On/Off digital variable.
    '''
    
    options = ['off', 'on']
    '''Set necessary attributes.
    '''
    
    def __init__(self, **kwargs):
        
        super(DigitalVariableOnOff, self).__init__(**kwargs)


class FloatInput(TextInput):
    '''A TextInput widget that allows only floating points numbers to be enterd.
    '''

    pattern = re.compile('[^0-9]')
    
    def insert_text(self, substring, from_undo=False):
        pattern = self.pattern
        if '.' in self.text:
            s = re.sub(pattern, '', substring)
        else:
            s = '.'.join([re.sub(pattern, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)
    
    
class SpinnerWithOnChoiceEvent(Spinner):
    '''A spinner with an additional event, that fires when the user chose an option.
    This is necessary to differentiate between text changes done by the user and changes done programatically.
    '''
    
    def __init__(self, **kwargs):
        super(SpinnerWithOnChoiceEvent, self).__init__(**kwargs)

        # Register the event        
        self.register_event_type('on_choice')
        
    def _on_dropdown_select(self, instance, data, *largs):
        '''Override this method to create the event.
        '''
        # Fire the event.
        self.dispatch('on_choice', data)
        
        # Call the parent method
        super(SpinnerWithOnChoiceEvent, self)._on_dropdown_select(instance, data, *largs)
        
    def on_choice(self, *args):
        '''A default handler for the on_choice event
        '''
        pass