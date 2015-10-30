from kivy.uix.gridlayout import GridLayout
from kivy.properties import ListProperty
from .. import MyView
from kivy.uix.boxlayout import BoxLayout

class MyControlView(GridLayout, MyView):
    '''The Control view allows the user to manually control and monitor all of the system's components individually
    '''
    
    components = ListProperty()
    '''The hardware components to be controlled
    '''
    
    def __init__(self, **kwargs):
        super(MyControlView, self).__init__(**kwargs)
        
        # Populate components
        for comp in self.components:
            self.add_widget(comp)
            
        # Add a place holder in case the components can't fill the screen vertically
        # This is nicer than stretching the component widgets vertically
        self.add_widget(BoxLayout())