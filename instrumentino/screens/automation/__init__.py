from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ListProperty
from .. import MyView
from kivy.uix.widget import Widget

class MyAutomationView(TabbedPanel, MyView):
    '''The Automation view allows the user to create and run lists of actions (called methods)
    and lists of methods (sequences)
    '''
    
    actions = []
    '''The actions that the system should perform
    '''
    
    def __init__(self, **kwargs):
        super(MyAutomationView, self).__init__(**kwargs)
        
class Action(Widget):
    '''An action to be performed in the system
    '''
    
    name = StringProperty('an action')
    '''The action's name on the screen
    '''
    function = ObjectProperty(None)
    '''The code to be executed for this function
    '''
    
    def __init__(self, **kwargs):
        super(Action, self).__init__()
        if "name" in kwargs:
            self.name = kwargs["name"]
        elif "function" in kwargs:
            self.function = kwargs["function"]
        else:
            raise TypeError( "Invalid arguments to Action" )

