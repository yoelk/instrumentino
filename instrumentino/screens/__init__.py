from kivy.properties import StringProperty, ListProperty, NumericProperty, DictProperty
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel
from instrumentino.libs.multichoicetogglebutton import MultichoiceToggleButton
from kivy.event import EventDispatcher
from instrumentino.cfg import *

class MyScreen(Screen):
    ''' A custom screen that allows to dynamically remove and add views
    '''
        
    part_containers = ListProperty()
    '''A list of containers in the screen, into which the possible views can be added.
    '''
    
    def empty_containers(self):
        '''Empty the containers.
        '''
        
        for container in self.part_containers:
            # Bug fix for issue #3: make sure children are always aligned with their parent
            # This is necessary when switching parents (don't know why but it is) 
            for child in container.children:
                child.pos = 0,0
                child.height = self.height
            container.clear_widgets()
        
    def add_view(self, view):
        '''add widgets to the inner parts in the right order
        '''
        
        for container in self.part_containers:
            if len(container.children) == 0:
                container.add_widget(view)
                return
        
        # If reached here, too many widgets were added (more than the number of inner parts)
        raise MyScreen.TooManyViewsException()
    
    class TooManyViewsException(RuntimeError):
        '''Throw this exception when more views have been added than the number of containers.
        '''
        
        def __init__(self):
            super(MyScreen.TooManyViewsException, self).__init__('too many views added')

class MySingleViewScreen(MyScreen):
    '''A screen that holds a single view.
    '''
    
class MyDoubleViewScreen(MyScreen):
    '''A screen that holds two views, separated by a splitter.
    '''
            
class MyTripleViewScreen(MyScreen):
    '''A screen that holds three views, separated by two splitters.
    '''

class MultipleViewManager(ScreenManager):
    '''Enables dynamically adding/removing views from the screen by pressing on toggle buttons (view choosers) in the sidebar.
    Splitters separate between concurrent views on screen.
    '''
    
    num_visible_views = NumericProperty(0)
    '''The number of currently visible views. 
    '''
    
    max_visible_views = NumericProperty(3)
    '''The maximal number of views to show on screen.
    '''
    
    view_choosers = ListProperty()
    '''The list of view choosers.
    '''
    
    views = DictProperty()
    '''A dictionary between the possible views' names and their objects.
    '''
    
    def __init__(self, **kwargs):
        super(MultipleViewManager, self).__init__(transition=FadeTransition(), **kwargs)

    def add_view(self, view):
        '''Add a possible view to the screen manager
        '''
        self.views[view.name] = view
        
        # Add a view chooser to the side-menu
        view_choosers_container = App.get_running_app().top.view_choosers_container
        chooser = ViewChooser(view_name=view.name, max_selected=self.max_visible_views)
        self.view_choosers.append(chooser) 
        view_choosers_container.add_widget(chooser)
            
    def on_start(self):
        '''Select which views are enabled on startup. 
        '''
        
        self.view_choosers[0].trigger_action(0)
        self.view_choosers[1].trigger_action(0)
        self.view_choosers[2].trigger_action(0)

    def update_screens(self, screen_name, new_state):
        '''Update the screen when a view chooser was pressed, adding/removing views accordingly.
        For the sake of simplicity, first remove all of the views and then add the ones that are enabled.
        '''
        
        if new_state == 'down':
            if self.num_visible_views < self.max_visible_views:
                self.num_visible_views += 1
        else:
            self.num_visible_views -= 1

        # remove views from all screens
        for screen in self.screens:
            screen.empty_containers()

        active_choosers = [c for c in self.view_choosers if c.state == 'down']            
        if len(active_choosers) == 1:
            self.get_screen('SingleView').add_view(self.views[active_choosers[0].view_name])
            self.current = 'SingleView'
        elif len(active_choosers) == 2:
            self.get_screen('DoubleView').add_view(self.views[active_choosers[0].view_name])
            self.get_screen('DoubleView').add_view(self.views[active_choosers[1].view_name])
            self.current = 'DoubleView'
        elif len(active_choosers) == 3:
            self.get_screen('TripleView').add_view(self.views[active_choosers[0].view_name])
            self.get_screen('TripleView').add_view(self.views[active_choosers[1].view_name])
            self.get_screen('TripleView').add_view(self.views[active_choosers[2].view_name])
            self.current = 'TripleView'

class ViewChooser(MultichoiceToggleButton):
    '''A toggle button to choose which views are visible in the screen manager.
    More than 1 may be allowed.
    '''
    
    view_name = StringProperty()
    '''The name of the view that this chooser is connected to.
    '''

class MyView(EventDispatcher):
    '''A view that can be added to the MultipleViewManager widget. 
    '''
    
    name = StringProperty('a view')
    '''The view's name, which is used to access it in a view dictionary
    '''