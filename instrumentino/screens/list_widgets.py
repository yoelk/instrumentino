import re
from kivy.properties import StringProperty, ObjectProperty
from kivy.event import EventDispatcher
from kivy.uix.listview import CompositeListItem,\
    SelectableView, ListItemReprMixin
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from instrumentino.cfg import check_for_necessary_attributes

class VariableValueDisplayWidget(EventDispatcher):
    '''A base-class for widgets that are used for displaying a variable's value.
    '''
    
    variable = ObjectProperty()
    '''The variable for which this widget is used.
    '''
    
    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['variable'], kwargs)
        super(VariableValueDisplayWidget, self).__init__(**kwargs)
        
        # Connect to the variable
        self.variable.value_display_widget = self
        
        # disable user input if needed
        self.disabled = (self.variable.channel_out == None and self.variable.channel_in != None)
        
        self.text = self.variable.value_to_text(self.variable.value)


class SubclassedCompositeListItem(CompositeListItem):
    '''This class extends CompositeListItem to add functionality for cases
    in which the parts of the view are added in the class's __init__ itself
    and some in the __init__ of its subclasses.
    '''
    
    def add_cls_dicts(self, added_cls_dicts, kwargs):
        '''Add widgets to the container.
        This is done by adding items to the cls_dicts list, because we're
        operating in a kivy list.
        Items are added from the left so that widgets that were added in parent
        classes will show first (has to do with __init__ call sequence).
        '''
        current_cls_dicts = kwargs.get('cls_dicts', [])
        kwargs['cls_dicts'] = added_cls_dicts + current_cls_dicts
        
    
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


class ListItemVariableSingleLineTextInput(VariableValueDisplayWidget, CompositeListItemMember, TextInput):
    '''A single line text input for usage in a composite list item.
    '''

    def __init__(self, **kwargs):
        super(ListItemVariableSingleLineTextInput, self).__init__(**kwargs)
        
        self.multiline = False
        self.bind(focus=self.on_user_focus)
        self.bind(on_text_validate=self.on_user_input)

    def on_user_focus(self, instance, value):
        '''Tell the variable the user is editing
        '''
        self.variable.user_is_editing = value
        
        # User stopped editing, so check what was entered
        if self.variable.user_is_editing == False:
            self.on_user_input(instance)

    def on_user_input(self, instance):
        '''Tell the variable the user has entered text
        '''                
        self.variable.user_entered_text(self.text)


class ListItemNormalLabel(CompositeListItemMember, Label):
    '''A normal label for usage in a composite list item.
    '''

    def __init__(self, **kwargs):
        super(ListItemNormalLabel, self).__init__(**kwargs)


class ListItemVariableFloatInput(ListItemVariableSingleLineTextInput):
    '''A TextInput widget that allows only floating points numbers to be enterd.
    '''

    pattern = re.compile('[^0-9]')
    '''A regular expression pattern that helps with filtering user input
    '''
    
    def insert_text(self, substring, from_undo=False):
        '''Make sure text is inserted correctly into the allowed pattern
        '''
        pattern = self.pattern
        if '.' in self.text:
            s = re.sub(pattern, '', substring)
        else:
            s = '.'.join([re.sub(pattern, '', s) for s in substring.split('.', 1)])
        return super(ListItemVariableFloatInput, self).insert_text(s, from_undo=from_undo)


class ListItemVariablePathInput(ListItemVariableSingleLineTextInput):
    '''A TextInput widget that allows the user to choose a path for file.
    '''
    
    def __init__(self, **kwargs):
        super(ListItemVariablePathInput, self).__init__(**kwargs)

    def on_user_focus(self, instance, value):
        super(ListItemVariablePathInput, self).on_user_focus(instance, value)
        f = FileChooserPopup()
        f.show_load(self.variable.base_path , self.variable.file_filters)
        
    def insert_text(self, substring, from_undo=False):
        '''Don't allow to enter any text manually
        '''
        pass


class ListItemVariableDurationInput(ListItemVariableSingleLineTextInput):
    '''A TextInput widget that allows to input a duration of time.
    The time is presented in the format: 00:00:00.000 (hours:minutes:seconds.milliseconds)
    '''

    pattern = re.compile('[^0-9]')
    '''A pattern to match everything but digits
    '''

    total_seconds_digits = 2+2+2+3
    '''The number of digits to display. 2+2+2+3 for hours+minutes+seconds+milliseconds.
    '''
    
    last_text = StringProperty()
    '''Remember the text before the current change
    '''
    
    def __init__(self, **kwargs):
        super(ListItemVariableDurationInput, self).__init__(**kwargs)
        self.last_text = self.text
 
    def cursor_advancement_in_real_text(self, cursor, digits_added):
        '''Calculate the new position of the cursor after adding a number
        of digits, considering the text format.
        '''
        separators_positions = [2,5,8]
        for _ in range(digits_added):
            # skip over separators
            if cursor in separators_positions:
                cursor += 1
            
            # advance cursor
            cursor += 1
        
        if cursor in separators_positions:
            cursor += 1
                
        return min(cursor, len(self.text)-1)
    
    def insert_text(self, substring, from_undo=False):
        '''Make sure text is inserted correctly into the allowed pattern
        The text should always have the form: '00:00:00.000'
        '''

        # Check if the user accidentally deleted some of the text
        if len(self.text) != len(self.last_text):
            cc, cr = self.cursor
            self.text = self.last_text
            self.cursor = (cc, cr)
            return

        # Only accept digits 
        pattern = self.pattern
        stripped_substring = re.sub(pattern, '', substring)
        
        # Replace the digits in the stripped text and check it doesn't contain too many digits
        cc, cr = self.cursor
        cc = self.cursor_advancement_in_real_text(cc, 0)
        new_stripped_text = re.sub(pattern, '', self.text[:cc]) + stripped_substring + re.sub(pattern, '', self.text[cc:])[len(stripped_substring):]
        new_stripped_text = new_stripped_text[:self.total_seconds_digits]
        
        # Format the text again for display
        milliseconds = new_stripped_text[-3:]
        new_stripped_text = new_stripped_text[:-3]
            
        new_formatted_text = ':'.join(re.findall('..', new_stripped_text))
        if len(milliseconds):
            new_formatted_text += '.' + milliseconds
        
        self.text = new_formatted_text
        
        # Set the cursor in the right place
        cc = self.cursor_advancement_in_real_text(cc, len(stripped_substring))
        self.cursor = (cc, cr)
        
        self.last_text = self.text 
        
    def do_backspace(self, from_undo=False, mode='bkspc'):
        '''Disable backspace.
        '''
        pass
    
    def select_text(self, start, end):
        '''Disable selection.
        '''
        pass
    
class ListItemSpinnerWithOnChoiceEvent(CompositeListItemMember, SelectableView, Spinner):
    '''A spinner with an additional event, that fires when the user chose an option.
    This is necessary to differentiate between text changes done by the user and changes done programatically.
    '''
    
    on_choice_callback = ObjectProperty()
    '''Call this function when on_choice is dispatched.
    '''
    
    def __init__(self, **kwargs):
        super(ListItemSpinnerWithOnChoiceEvent, self).__init__(**kwargs)
        
        # Register the event        
        self.register_event_type('on_choice')

    def _on_dropdown_select(self, instance, data, *largs):
        '''Override this method to create the event.
        '''
        # Fire the event.
        self.dispatch('on_choice', data)
        
        # Call the parent method
        super(ListItemSpinnerWithOnChoiceEvent, self)._on_dropdown_select(instance, data, *largs)
        
    def on_choice(self, text):
        '''A default handler for the on_choice event
        '''
        if self.on_choice_callback:
            # Send the both the new text and the old text 
            self.on_choice_callback(text, self.text)

    
class ListItemVariableSpinnerWithOnChoiceEvent(VariableValueDisplayWidget, ListItemSpinnerWithOnChoiceEvent):
    '''A spinner with a choice event that is used for a variable's value display
    '''
    
    def __init__(self, **kwargs):
        super(ListItemVariableSpinnerWithOnChoiceEvent, self).__init__(**kwargs)
        
        self.text = self.variable.options[0]
        self.values = self.variable.options
        
        self.bind(on_choice=self.on_user_choice)
        
    def on_is_open(self, instance, value):
        '''Tell the variable the user is editing
        '''
        self.variable.user_is_editing = value
        super(ListItemVariableSpinnerWithOnChoiceEvent, self).on_is_open(instance, value)
        
    def on_user_choice(self, instance, value):
        '''Tell the variable the user has entered text
        '''
        self.variable.user_entered_text(value)