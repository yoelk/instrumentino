'''
Variables
=========

A :class:`Variable` is a widget for showing and setting data on the screen.
The values of variables are serialized by turning them to a percentage.
Percentages are used for communication values between variables and channels.
Variable values are displayed on the screen by converting them into text.
Access to a variable's value in python is given by the :attr:`value`
attribute (variable.value). This returns the native value for this variable
(e.g. the chosen text in a spinner or the value within the variable's range
for an analog variable). The textual representation of a variable's value may
also be accessed by the :attr:`text` attribute (variable.text).

This is implemented in each of the sub-classes separately.
There are 3 principle types of variables:
- :class:`AnalogVariable`
    Handles analog data, represented by a :class:`TextInput`.
    Only this variable may have units.
- :class:`DigitalVariable`
    Handles digital data, represented by a :class:`Spinner`.
- custom structured variables
    Handle data that needs to be presented in a custom structured way.
    An example is :class:`TimeVariable` which represents the time in a
    :class:`TextInput` in the following way: 00:00:00.00
    (hours:minutes:seconds.miliseconds). The native serial value for this
    variable is the number of seconds.

'''

from __future__ import division
import re
import time
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty, OptionProperty, BooleanProperty, AliasProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.event import EventDispatcher
from kivy.uix.listview import CompositeListItem
from instrumentino.cfg import *
from instrumentino.screens.list_widgets import CompositeListItemMember, ListItemNormalLabel,\
    ListItemVariableFloatInput, SubclassedCompositeListItem, ListItemSpinnerWithOnChoiceEvent,\
    ListItemVariableDurationInput, ListItemVariableSpinnerWithOnChoiceEvent

class VariableView(CompositeListItemMember, SubclassedCompositeListItem):
    '''A widget for a basic variable.
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['variable'], kwargs)
        
        # Set the sub-widgets
        added_cls_dicts = [{'cls': ListItemNormalLabel,
                            'kwargs': {'text': self.variable.name} },
                           ]
        self.add_cls_dicts(added_cls_dicts, kwargs)
        super(VariableView, self).__init__(**kwargs)


class VariablesListView(CompositeListItemMember, CompositeListItem):
    '''A widget for showing a list of variables
    '''
    
    def __init__(self, **kwargs):
        variables = kwargs['variables']
        
        # Add a view for each parameter
        cls_dicts = []
        for var in variables:
            cls_dicts += [{'cls': var.view_class,
                          'kwargs': {'variable': var} },
                         ]
        kwargs['cls_dicts']=cls_dicts
        kwargs['orientation']='vertical'
        super(VariablesListView, self).__init__(**kwargs)


class Variable(EventDispatcher):
    '''A variable widget for showing different types of variables on the screen.
    When given a channel_in argument, their value will be automatically updated by this channel.
    When given a channel_out argument, the value the user enters will be communicated out by that channel.
    
    Subclasses are responsible of screen presentation of the variable.
    '''

    view_class = ObjectProperty(VariableView)
    '''The class in charge for displaying this variable.
    Sub-classes should set this according to their needs.
    '''

    value_display_widget = ObjectProperty()
    '''The widget that displays the variable's value
    '''

    name = StringProperty()
    '''The variable's name on the screen
    '''
    
    user_is_editing = BooleanProperty(False)
    '''Is the user currently editing the variable's value.
    This attribute should be updated by sub-classes.
    '''
    
    value = ObjectProperty()
    '''The native value for this variable.
    Sub-classes should redefine this property to set its type. 
    '''

    channel_in = ObjectProperty(None)
    '''The input channel
    '''
    
    channel_out = ObjectProperty(None)
    '''The output channel
    '''

    def text_to_value(self, text):
        '''Return the native value for this variable by translating a textual input.
        It is used to receive input from the user.
        Default is a simple cast to the variable's value's type.
        '''
        return type(self.value)(text)
    
    def value_to_text(self, value):
        '''Return the textual representation of the variable's value.
        It is used to display the variable's value on the screen.
        Default is a simple cast to text.
        '''
        return str(value)

    def percentage_to_value(self, percentage):
        '''Return the native value for this variable by translating a percentage.
        Sub-classes should implement this if they want to be able to receive
        data from input channels.
        '''
        raise NotImplementedError()
    
    def value_to_percentage(self, value):
        '''Translate the variable's value into a percentage.
        Sub-classes should implement this if they want to be able to transmit
        data to output channels.
        '''
        raise NotImplementedError()

    def __init__(self, **kwargs):
        super(Variable, self).__init__(**kwargs)
        
        self.name = self.name or create_default_name(self)

        # Let the channels keep a reference to us
        if self.channel_in:
            self.channel_in.variable = self
            
        if self.channel_out:
            self.channel_out.variable = self
            

            
    def user_entered_text(self, text):
        '''When the user sets the variable's value, act upon it and write it to the controller.
        '''
        self.value = self.text_to_value(text)
        
        if self.channel_out:
            self.channel_out.write(self.value_to_percentage(self.value))


    def new_data_arrived(self, percentage):
        '''Handle incoming data from the input channel (if it exists).
        '''
        
        self.value = self.percentage_to_value(percentage)
        
        # Don't update the text while the user is editing
        if not self.user_is_editing and self.value_display_widget:
            self.value_display_widget.text = self.value_to_text(self.value)
        

class AnalogVariableView(VariableView):
    '''An extension to the basic variable widget for an analog variable.
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['variable'], kwargs)
        
        # Set the sub-widgets
        added_cls_dicts = [{'cls': ListItemNormalLabel,
                            'kwargs': {'text': '[' + str(self.variable.lower_limit) + ',' + str(self.variable.upper_limit) + ']'} },
                           {'cls': ListItemVariableFloatInput,
                            'kwargs': {'variable': self.variable} },
                           {'cls': ListItemNormalLabel,
                            'kwargs': {'text': self.variable.units} }
                           ]
        self.add_cls_dicts(added_cls_dicts, kwargs)
        super(AnalogVariableView, self).__init__(**kwargs)


class AnalogVariable(Variable):
    '''An analog variable
    '''

    view_class = ObjectProperty(AnalogVariableView)

    value = NumericProperty()
    '''The native value for this variable is a number.
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

    def value_to_text(self, value):
        '''Return the textual representation of the variable's value.
        It is used to display the variable's value on the screen.
        '''
        return '{:2.2f}'.format(value)
    
    def __init__(self, **kwargs):
        super(AnalogVariable, self).__init__(**kwargs)
        
        check_for_necessary_attributes(self, ['range', 'units'], kwargs)
        
        # Let the user define the limits as a range.
        self.upper_limit = self.range[1]
        self.lower_limit = self.range[0]
            

class AnalogVariableUnipolar(AnalogVariable):
    '''An analog variable for unipolar values
    '''

    def percentage_to_value(self, percentage):
        '''Return the native value for this variable by translating a percentage.
        '''
        return self.lower_limit + percentage / 100 * (self.upper_limit - self.lower_limit)
    
    def value_to_percentage(self, value):
        '''Translate the variable's value into a percentage.
        '''
        return (value - self.lower_limit) / (self.upper_limit - self.lower_limit) * 100
        
    def __init__(self, **kwargs):
        super(AnalogVariableUnipolar, self).__init__(**kwargs)
        
        # Check the range
        if self.upper_limit * self.lower_limit < 0: raise ValueError('Range should be unipolar')

        
class AnalogVariablePercentage(AnalogVariableUnipolar):
    '''An analog variable for percentage values
    '''

    range = [0, 100]
    units = '%'
    '''Set necessary attributes.
    '''
    
    def __init__(self, **kwargs):
        super(AnalogVariablePercentage, self).__init__(**kwargs)
        
        
class AnalogVariableDurationInSecondsView(VariableView):
    '''An extension to the basic variable widget for an analog variable.
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['variable'], kwargs)
        
        # Set the sub-widgets
        added_cls_dicts = [{'cls': ListItemVariableDurationInput,
                            'kwargs': {'variable': self.variable} },
                           ]
        self.add_cls_dicts(added_cls_dicts, kwargs)
        super(AnalogVariableDurationInSecondsView, self).__init__(**kwargs)


class AnalogVariableDurationInSeconds(Variable):
    '''A variable that represents a duration of time, measured in seconds. 
    '''
    
    view_class = ObjectProperty(AnalogVariableDurationInSecondsView)

    value = NumericProperty()
    '''The native value for this variable is a number (the number of seconds).
    '''
        
    pattern = re.compile('(..):(..):(.*)')
    '''The time is presented in the format: 00:00:00.000 (hours:minutes:seconds.milliseconds).
    '''
    
    def text_to_value(self, text):
        '''Return the native value for this variable by translating a textual input.
        It is used to receive input from the user.
        '''
        match = self.pattern.match(text)
        h = int(match.group(1))
        m = int(match.group(2))
        s = float(match.group(3))
        
        # return the number of seconds
        print str(h*60*60 + m*60 + s)
        return h*60*60 + m*60 + s
    
    def value_to_text(self, value):
        '''Return the textual representation of the variable's value.
        It is used to display the variable's value on the screen.
        '''
        m, s = divmod(value, 60)
        h, m = divmod(m, 60)
        return '{:02d}:{:02d}:{:06.3f}'.format(h, m, s)

    def __init__(self, **kwargs):
        super(AnalogVariableDurationInSeconds, self).__init__(**kwargs)
        
        if not 'value' in kwargs:
            kwargs['value'] = 0


class DigitalVariableView(VariableView):
    '''An extension to the basic variable widget for a digital variable.
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['variable'], kwargs)
        
        # Set the sub-widgets
        added_cls_dicts = [{'cls': ListItemVariableSpinnerWithOnChoiceEvent,
                            'kwargs': {'variable': self.variable} }
                           ]
        self.add_cls_dicts(added_cls_dicts, kwargs)
        super(DigitalVariableView, self).__init__(**kwargs)


class DigitalVariable(Variable):
    '''A digital variable
    '''

    view_class = ObjectProperty(DigitalVariableView)

    options = ListProperty()
    '''The list of possible values, ordered from lowest to highest.
    '''
    
    def percentage_to_value(self, percentage):
        '''Return the native value for this variable by translating a percentage.
        '''
        index = int(percentage / 100 * (len(self.options) - 1))
        return self.options[index]
    
    def value_to_percentage(self, value):
        '''Translate the variable's value into a percentage.
        '''
        return self.options.index(value) / (len(self.options) - 1) * 100
        
    def __init__(self, **kwargs):
        super(DigitalVariable, self).__init__(**kwargs)
        
        check_for_necessary_attributes(self, ['options'], kwargs)
        

class DigitalVariableOnOff(DigitalVariable):
    '''An On/Off digital variable.
    '''
    
    options = ['off', 'on']
    '''Set necessary attributes.
    '''
    
    def __init__(self, **kwargs):
        
        super(DigitalVariableOnOff, self).__init__(**kwargs)