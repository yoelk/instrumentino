from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from ..screens import MyView
import time
from kivy.app import App

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
        self.name = self.name or App.get_running_app().create_default_name(self)
        
        super(Component, self).__init__(**kwargs)
        
        # Add all of the variable widgets
        for var in self.variables:
            self.add_widget(var)

    def add_variable(self, variable):
        self.variables.append(variable)

    #def remove_variable(self): # No do as it would be odd, and difficult
    #    pass

    def remove_variables(self):
        self.clear_widgets()
        for ndx, variable in enumerate(self.variables):
            del self.variables[ndx]

    def build(self):
        '''Add here the component variables. This should be overriden by derived classes
        '''
