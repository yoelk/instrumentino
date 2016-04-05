from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ListProperty
from instrumentino.screens import MyView
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from instrumentino.cfg import *
from instrumentino.variables import Variable
from kivy.uix.listview import ListItemButton, ListView, CompositeListItem,\
    SelectableView, ListItemReprMixin
from kivy.event import EventDispatcher
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class CompositeListItemMember(EventDispatcher):
    '''Implements the necessary methods for widgets in a composite list item.
    '''
    
    def select_from_composite(self, *args):
        pass
 
    def deselect_from_composite(self, *args):
        pass


class CompositeListItemMemberWithSelection(ListItemReprMixin, CompositeListItemMember, SelectableView):
    '''A selectable view that responds to on on_touch_down.
    Subclass widgets will respond for selection in a composite list item. 
    '''

    def select(self, *args):
        if isinstance(self.parent, CompositeListItem):
            self.parent.select_from_child(self, *args)
 
    def deselect(self, *args):
        if isinstance(self.parent, CompositeListItem):
            self.parent.deselect_from_child(self, *args)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.select()
        else:
            self.deselect()
        return super(CompositeListItemMemberWithSelection, self).on_touch_down(touch)


class ListItemSingleLineTextInput(CompositeListItemMember, TextInput):
    '''A single line text input for usage in a composite list item.
    '''

    multiline = False
    '''Allow only a single line
    '''

    def __init__(self, **kwargs):
        super(ListItemSingleLineTextInput, self).__init__(**kwargs)


class ListItemNormalLabel(CompositeListItemMember, Label):
    '''A normal label for usage in a composite list item.
    '''

    def __init__(self, **kwargs):
        super(ListItemNormalLabel, self).__init__(**kwargs)


class ListItemSpinner(CompositeListItemMember, SelectableView, Spinner):
    '''A spinner for usage in a composite list item.
    '''

    def __init__(self, **kwargs):
        super(ListItemSpinner, self).__init__(**kwargs)


class AutomationItemParameterView(CompositeListItemMember, CompositeListItem):
    '''A widget for an automation item parameter
    '''
    
    parameter = ObjectProperty()
    '''The parameter we need to show 
    '''
    
    def __init__(self, **kwargs):
        # Set the sub-widgets
        cls_dicts = [{'cls': ListItemNormalLabel,
                      'kwargs': {'text': 'time'} },
                     {'cls': ListItemSingleLineTextInput,
                      'kwargs': {'text': '00:00:00'} },
                     ]
        kwargs['cls_dicts']=cls_dicts
        super(AutomationItemParameterView, self).__init__(**kwargs)


class AutomationItemParametersListView(CompositeListItemMember, CompositeListItem):
    '''A widget for an automation item parameters list
    '''
    
    action = ObjectProperty()
    '''The action for which we need to show parameters
    '''
    
    def __init__(self, **kwargs):
        # Set the sub-widgets
        cls_dicts = [{'cls': AutomationItemParameterView,
                      'kwargs': {'parameter': 'XXX'} },
                     {'cls': AutomationItemParameterView,
                      'kwargs': {'parameter': 'XXX'} },
                     ]
        kwargs['cls_dicts']=cls_dicts
        kwargs['orientation']='vertical'
        super(AutomationItemParametersListView, self).__init__(**kwargs)


class AutomationItemView(CompositeListItemMember, CompositeListItem):
    '''A widget for an automation item
    '''
    
    def __init__(self, **kwargs):
        index = kwargs['index']
        data = kwargs['data']
        
        #TODO: I don't think it would work well if we have two action with the same name. Check and get it to work. 
        
        # Set the sub-widgets
        cls_dicts = [{'cls': ListItemButton,
                      'kwargs': {'text': '{}'.format(index+1)} },
                     {'cls': ListItemSpinner,
                      'kwargs': {'values': [c().name for c in data.action_classes],
                                 'text': data.chosen_action.name} },
                     {'cls': AutomationItemParameterView,
                      },
                     ]
        kwargs['cls_dicts']=cls_dicts
        super(AutomationItemView, self).__init__(**kwargs)


class AutomationItemData(EventDispatcher):
    '''A class for holding the data of an automation item
    '''
    
    action_classes = ListProperty()
    '''The possible action classes
    '''
    
    chosen_action = ObjectProperty()
    '''The currently chosen action
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['action_classes'], kwargs)
        self.chosen_action = self.chosen_action or self.action_classes[0]()
        
        super(AutomationItemData, self).__init__(**kwargs)


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
        self.name = self.name or create_default_name(self, use_index=False)
        
        # Automatically populate the arguments' list by collecting all of the "Variable" instances we have.
        self.arguments = get_attributes_of_type(self, Variable, kwargs)
        
        super(Action, self).__init__(**kwargs)
        

class ActionRunFile(EventDispatcher):
    '''An action that runs the actions stored in an action-list file
    '''
    
    name = 'Run file'
    
    arguments = ListProperty()

    def on_start(self):
        '''Load an action-list file and run it
        '''
        #TODO: implement
        print 'running file...'
        

class AutomationList(ListView):
    '''A list of automation items.
    '''
    
    items = ListProperty()
    '''The current items in the automation list
    '''
    
    def __init__(self, **kwargs):
        args_converter = lambda index, data: {'data':data,
                                              'height': 30,
                                              'size_hint_y': None,}

        kwargs['adapter'] = ListAdapter(data=self.items,
                                        args_converter=args_converter,
                                        selection_mode='multiple',
                                        allow_empty_selection=True,
                                        cls=AutomationItemView)
        
        super(AutomationList, self).__init__(**kwargs)


class MyAutomationView(BoxLayout, MyView):
    '''The Automation view allows the user to create and run lists of actions (called methods).
    '''
    
    action_classes = ListProperty()
    '''The possible action classes
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['action_classes'], kwargs)
        
        super(MyAutomationView, self).__init__(**kwargs)
        
    def add_item(self):
        '''Add an item to the list
        '''
        self.run_items.adapter.data.append(AutomationItemData(action_classes=self.action_classes))
        self.run_items._trigger_reset_populate()
    
    def remove_item(self):
        '''Remove selected items from the list
        '''
        indices = set(item.parent.index for item in self.run_items.adapter.selection)
        new_list = [i for j, i in enumerate(self.run_items.adapter.data) if j not in indices]
        self.run_items.adapter.data = new_list
        
        self.run_items._trigger_reset_populate()
    
    def run_all(self):
        '''Run all items in the list
        '''
        pass