from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from instrumentino.screens import MyView
from instrumentino.screens.list_widgets import CompositeListItemMember, ListItemNormalLabel
import time
from kivy.app import App
from instrumentino.cfg import *
from instrumentino.variables import AnalogVariablePercentage,\
    DigitalVariableOnOff, Variable, VariablesListView
from kivy.uix.listview import CompositeListItem, ListView
from kivy.adapters.listadapter import ListAdapter

class ComponentView(CompositeListItemMember, CompositeListItem):
    '''A widget for a component
    '''
    
    def __init__(self, **kwargs):
        data = kwargs['data']

        # Set the height according to the number of parameters we need to show (+ 1 for the component name)
        kwargs['height'] = kwargs['height'] * (1 + len(data.variables))
        
        # Set the sub-widgets
        cls_dicts = [{'cls': ListItemNormalLabel,
                      'kwargs': {'text': data.name} },
                     {'cls': VariablesListView,
                      'kwargs': {'variables': data.variables,
                                 'text':''} }
                      ]
        kwargs['cls_dicts']=cls_dicts
        super(ComponentView, self).__init__(**kwargs)


class ComponentsListView(ListView):
    '''A list of automation items.
    '''
    
    items = ListProperty()
    '''The current items in the components list
    '''
    
    def __init__(self, **kwargs):
        args_converter = lambda index, data: {'data':data,
                                              'height': 30,
                                              'size_hint_y': None,}

        kwargs['adapter'] = ListAdapter(data=self.items,
                                        args_converter=args_converter,
                                        selection_mode='none',
                                        allow_empty_selection=True,
                                        cls=ComponentView)
        
        super(ComponentsListView, self).__init__(**kwargs)


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

        # Automatically populate the variables' list by collecting all of the Variable instances we have.
        self.variables = get_attributes_of_type(self, Variable, kwargs)
                
        super(Component, self).__init__(**kwargs)
        
    def build(self):
        '''Add here the component variables. This should be overriden by derived classes
        '''
        # TOD: WTF is this?


class AnalogVariables(Component):
    '''An array of analog input variables
    '''
    
    def __init__(self, **kwargs):
        ch_class = kwargs.get('ch_class', None)
        controller = kwargs.get('controller', None)
        channels_numbers = kwargs.get('channels_numbers', None)
        sampling_rate = kwargs.get('sampling_rate', None)

        self.variables = []
        for i in channels_numbers:
            ch_in = ch_class(controller=controller, number=i, sampling_rate=sampling_rate)
            self.variables.append(AnalogVariablePercentage(name='Analog '+str(i), channel_in=ch_in))
        
        super(AnalogVariables, self).__init__(**kwargs)


class DigitalVariables(Component):
    '''An array of digital input/output variables
    '''
    
    def __init__(self, **kwargs):
        ch_class = kwargs.get('ch_class', None)
        controller = kwargs.get('controller', None)
        channels_numbers = kwargs.get('channels_numbers', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        self.variables = []
        for i in channels_numbers:
            ch = ch_class(controller=controller, number=i, sampling_rate=sampling_rate)
            self.variables.append(DigitalVariableOnOff(name='Digital '+str(i), channel_in=ch, channel_out=ch))

        super(DigitalVariables, self).__init__(**kwargs)
