from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ListProperty
from .. import MyView
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from instrumentino.cfg import *
from instrumentino.variables import Variable

class MyAutomationView(BoxLayout, MyView):
    '''The Automation view allows the user to create and run lists of actions (called methods)
    and lists of methods (sequences)
    '''
    
    actions = []
    '''The actions that the system should perform
    '''
    
    def __init__(self, **kwargs):
        super(MyAutomationView, self).__init__(**kwargs)
        self.run_items.item_strings = self.actions
        del self.run_items.adapter.data[:]
        self.run_items.adapter.data.extend(self.actions)
        self.run_items._trigger_reset_populate()

        
class Action(Widget):
    '''An action to be performed in the system
    '''
    
    name = StringProperty()
    '''The action's name on the screen
    '''
    
    arguments = ListProperty()
    '''The arguments needed for this action
    '''

    on_start = ObjectProperty()
    '''The code to be executed for this action
    '''
    
    on_stop = ObjectProperty()
    '''The code to be executed when the action is stopped
    '''
    
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['on_start'], kwargs)
        self.name = self.name or App.get_running_app().create_default_name(self)
        
        # Automatically populate the arguments' list by collecting all of the "Variable" instances we have.
        self.arguments = get_attributes_of_type(self, Variable, kwargs)
        
        super(Action, self).__init__(**kwargs)