'''
Automation view
===============

The main class here is :class:`MyAutomationView`. It's a view that can be seen on the 
screen, alongside the control and signal views.

This view includes an automation list (:class:`AutomationListView`) and some 
buttons below.
AutomationListView implements a ListView, using a list adapter and an
args converter.
Each item in the list is actually a dialog for selecting and setting parameters
in the selected action. The dialog is shown on the screen by
:class:`AutomationItemView` and data is saved in :class:`AutomationItem`. 

AutomationItemView is a composite list item that includes (left to right):
- A button that shows the index number of that item in the list (1,2,3,etc.).
- A Spinner to let the user choose an action.
- A panel to hold the chosen action's parameters.

AutomationItem simply holds a list of possible actions (to populate the
spinner in AutomationItemView and a reference to the chosed action (with its
parameters).

:class:`Action` represents a runnable action, with its parameters. It has a
on_start method that holds the code that should be run for that action, and
a on_stop method, to be run when the user aborted the action. These are to be
implemented by sub-classes, such as :class:`ActionRunSequenceFile`. 

'''

from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, AliasProperty, NumericProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ListProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.event import EventDispatcher
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from instrumentino.cfg import *
from instrumentino.screens import MyView
from instrumentino.screens.list_widgets import CompositeListItemMember, \
    ListItemNormalLabel, ListItemSpinnerWithOnChoiceEvent
from instrumentino.variables import Variable, AnalogVariablePercentage, \
    AnalogVariableView, VariablesListView, AnalogVariableDurationInSeconds, \
    PathVariable
from kivy.uix.listview import CompositeListItem, ListItemButton, ListView
from instrumentino.popups import FileDialogPopup, SaveFileDialogPopup, \
    LoadFileDialogPopup, NotificationPopup
from kivy.uix.popup import Popup
import pickle
import ntpath


class AutomationItemView(CompositeListItemMember, CompositeListItem):
    '''A widget for an automation item
    '''

    list = ObjectProperty()
    '''The list in which this item resides
    '''

    index = NumericProperty()
    '''The index for this item
    '''

    def __init__(self, **kwargs):
        self.index = kwargs['index']
        data = kwargs['data']
        self.list = kwargs['list']

        # TODO: I don't think it would work well if we have two action with the same name. Check and get it to work.

        # Set the height according to the number of parameters we need to show
        kwargs['height'] = kwargs['height'] * max(1, len(data.chosen_action.parameters))

        # Set the sub-widgets
        cls_dicts = [{'cls': ListItemButton,
                      'kwargs': {'text': '{}'.format(self.index + 1)}},
                     {'cls': ListItemSpinnerWithOnChoiceEvent,
                      'kwargs': {'values': [c().name for c in data.action_classes],
                                 'text': data.chosen_action.name,
                                 'on_choice_callback': self.on_user_choice}},  # TODO: act upon the user's choice
                     {'cls': VariablesListView,
                      'kwargs': {'variables': data.chosen_action.parameters,
                                 'text': ''}
                      },
                     ]
        kwargs['cls_dicts'] = cls_dicts
        super(AutomationItemView, self).__init__(**kwargs)

    def on_user_choice(self, text, last_text):
        '''The user chose an option in the spinner
        '''
        if text != last_text:
            self.list.refresh_item(self.index, text)


class AutomationItem(EventDispatcher):
    '''A class for holding the data of an automation item
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
        self.chosen_action = self.chosen_action or self.action_classes[0]()


class AutomationListView(ListView):
    '''A list of automation items.
    '''

    def __init__(self, **kwargs):
        args_converter = lambda index, data: {'data': data,
                                              'list': self,
                                              'height': 30,
                                              'size_hint_y': None, }

        kwargs['adapter'] = ListAdapter(data=[],
                                        args_converter=args_converter,
                                        selection_mode='multiple',
                                        allow_empty_selection=True,
                                        cls=AutomationItemView)

        super(AutomationListView, self).__init__(**kwargs)

    def get_items(self):
        return self.adapter.data

    def add_item(self, action=None):
        '''Add an item to the list
        '''
        self.adapter.data.append(AutomationItem(action_classes=self.action_classes, chosen_action=action))
        self._trigger_reset_populate()

    def remove_item(self):
        '''Remove selected items from the list
        '''
        indices = set(item.parent.index for item in self.adapter.selection)
        new_list = [item for i, item in enumerate(self.adapter.data) if i not in indices]
        self.adapter.data = new_list

        self._trigger_reset_populate()

    def remove_all_items(self):
        '''Remove all items from the list
        '''
        self.adapter.data = []
        self._trigger_reset_populate()

    def run_all(self):
        '''Run all items in the list
        '''

        for item in self.adapter.data:
            item.chosen_action.on_start()

    def refresh_item(self, index, chosen_action_name):
        '''The user chose a new action in one of the list items so this item needs to be rebuilt
        '''
        chosen_action_class = [cls for cls in self.action_classes if cls().name == chosen_action_name][0]
        self.adapter.data[index] = AutomationItem(action_classes=self.action_classes,
                                                  chosen_action=chosen_action_class())
        self._trigger_reset_populate()


class MyAutomationView(BoxLayout, MyView):
    '''The Automation view allows the user to create and run lists of actions (called sequences).
    '''

    action_classes = ListProperty()
    '''The possible action classes
    '''

    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['action_classes'], kwargs)

        super(MyAutomationView, self).__init__(**kwargs)

    def on_load(self):
        '''Load a file
        '''
        LoadFileDialogPopup(on_file_choice_callback=self.load_sequence_file).open()

    def on_save(self):
        '''Save a file
        '''
        SaveFileDialogPopup(on_file_choice_callback=self.save_sequence_file).open()

    def load_sequence_file(self, filepath):
        '''Load a sequence file to the automation list
        '''
        try:
            # Read the file
            input = open(filepath, 'rb')
            actions_data = pickle.load(input)
            input.close()

            # Remove all items and add the read items
            self.run_items_list.remove_all_items()
            for data in actions_data:
                action = data['class'](pickled_data=data)
                self.run_items_list.add_item(action)

        except:
            NotificationPopup(text='Error opening file').open()

    def save_sequence_file(self, filepath):
        '''Save the automation list's content to a file
        '''
        try:
            output = open(filepath, 'wb')
            actions_data = [item.chosen_action.serialize() for item in self.run_items_list.get_items()]
            pickle.dump(actions_data, output, pickle.HIGHEST_PROTOCOL)
            output.close()
        except:
            NotificationPopup(text='Error saving file').open()

        NotificationPopup(text='File saved').open()


class Action(EventDispatcher):
    '''An action to be performed in the system
    '''

    name = StringProperty()
    '''The action's name on the screen
    '''

    parameters = ListProperty()
    '''The parameters needed for this action
    '''

    on_start = ObjectProperty()
    '''The code to be executed for this action
    '''

    on_stop = ObjectProperty()
    '''The code to be executed when the action is stopped
    '''

    def __init__(self, **kwargs):
        super(Action, self).__init__(**kwargs)

        # Support initiating an action from pickled data
        if 'pickled_data' in kwargs:
            try:
                self.unserialize(kwargs['pickled_data'])
            except:
                NotificationPopup(text='Error reading file').open()

        check_for_necessary_attributes(self, ['on_start'], kwargs)
        self.name = self.name or create_default_name(self, use_index=False)

        # Automatically populate the parameters' list by collecting all of the "Variable" instances we have.
        self.parameters = get_instances_in_object(self, Variable, kwargs)

    def serialize(self):
        '''Return a dictionary of the important data that needs to be pickled.
        This is done to avoid trying to pickle the whole class, which is a
        problem for EventDispatcher subclasses.
        '''

        # Store the name and the class type
        data_dict = {'name': self.name, 'class': type(self), 'parameters': {}}

        # Store the parameters
        for p in self.parameters:
            data_dict['parameters'][p.name] = {'type': type(p),
                                               'value': p.value}

        return data_dict

    def unserialize(self, pickled_data):
        '''Init an action from pickled data
        '''
        # Set name
        self.name = pickled_data['name']

        # Set parameter values
        params_data = pickled_data['parameters']
        for param_name in params_data.keys():
            param = params_data[param_name]['type'](name=param_name, value=params_data[param_name]['value'])
            setattr(self, param_name, param)


class ActionRunSequenceFile(Action):
    '''An action that runs the actions stored in an action-list file (called a sequence file)
    '''

    name = 'Run file'

    def __init__(self, **kwargs):
        self.path = PathVariable(file_filters=['*.seq'])

        super(ActionRunSequenceFile, self).__init__(**kwargs)

        # Define the path variable. This can only be done when the app is running.
        self.path.base_path = App.get_running_app().get_instrument_path()

    def on_start(self):
        '''Load a saved sequence file and run it
        '''
        # TODO: implement
        print('running file...')
