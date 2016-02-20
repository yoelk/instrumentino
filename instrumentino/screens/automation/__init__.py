from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ListProperty
from .. import MyView
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from instrumentino.cfg import *
from instrumentino.variables import Variable
from kivy.uix.listview import ListItemButton
from kivy.event import EventDispatcher

class MyAutomationView(BoxLayout, MyView):
    '''The Automation view allows the user to create and run lists of actions (called methods)
    and lists of methods (sequences)
    '''
    
    action_classes = ListProperty()
    '''The possible action classes
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['action_classes'], kwargs)
        
        super(MyAutomationView, self).__init__(**kwargs)

        self.run_items.item_strings = ['1','2','3']
        del self.run_items.adapter.data[:]
        self.run_items.adapter.data.extend(['1','2','3'])
        self.run_items._trigger_reset_populate()


class AutomationItem(ListItemButton):
    '''A widget to choose and enter information for a chosen automation item
    '''
    
    action_classes = ListProperty()
    '''The possible action classes
    '''
    
    chosen_action = ObjectProperty()
    '''The currently chosen action
    '''
    
    def __init__(self, **kwargs):
        super(AutomationItem, self).__init__(**kwargs)
        
        check_for_necessary_attributes(self, ['action_classes'], kwargs)
                
        # By default, choose the first defined action class
        self.chosen_action = self.chosen_action or self.action_classes[0]()

class Action(EventDispatcher):
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