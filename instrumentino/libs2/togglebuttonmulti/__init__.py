'''
MultichoiceToggleButton
=======================

The :class:`MultichoiceToggleButton` widget is like the :class:`ToggleButton`
but it allows choosing more than one button in a group. The maximal and
minimal numbers of concurrently selected buttons can be set. The same
settings should be set to all buttons in a group.

Like ToggleButtons, Each button needs to be assigned to a group.

To configure the ToggleButton, you can use the same properties that you can use
for a :class:`~kivy.uix.button.Button` class.

'''

__all__ = ('MultichoiceToggleButtonBehavior', 'MultichoiceToggleButton')

from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, BoundedNumericProperty
from weakref import ref
from kivy.uix.behaviors import ButtonBehavior

class MultichoiceToggleButtonBehavior(ButtonBehavior):
    '''Like ToggleButtonBehavior, but allowing several buttons selected.
    See module documentation for more information.
    '''

    max_selected = BoundedNumericProperty(1, min=1)
    '''Maximal number of concurrently selected buttons
    
    :attr:`max_selected` is a :class:`BoundedNumericProperty` defaults to 1
    '''
    
    min_selected = BoundedNumericProperty(0, min=0)
    '''Minimal number of concurrently selected buttons
    
    :attr:`min_selected` is a :class:`BoundedNumericProperty` defaults to 0
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the button. If None, no group will be used (button is
    independent). If specified, :attr:`group` must be a hashable object, like
    a string.

    :attr:`group` is a :class:`~kivy.properties.ObjectProperty`
    '''

    def __init__(self, **kwargs):
        self._previous_group = None
        super(MultichoiceToggleButtonBehavior, self).__init__(**kwargs)
        
    def on_group(self, *largs):
        groups = MultichoiceToggleButtonBehavior.__groups
        if self._previous_group:
            group = groups[self._previous_group]
            for item in group[:]:
                if item() is self:
                    group.remove(item)
                    break
        group = self._previous_group = self.group
        if group not in groups:
            groups[group] = []
        r = ref(self, MultichoiceToggleButtonBehavior._clear_groups)
        groups[group].append(r)

    def __get_num_selected(self):
        if self.group is None:
            return 1 if self.state is 'down' else 0
        group = self.__groups[self.group]
        num = 0
        for item in group[:]:
            widget = item()
            if widget is None:
                group.remove(item)
            if widget.state is 'down':
                num += 1
        return num
            
    def _do_release(self, *args):
        pass

    def _do_press(self):
        if not self.group:
            return
        
        num_selected = self.__get_num_selected()

        if (self.state == 'normal' and
            num_selected < self.max_selected):
            self.state = 'down'
        elif (self.state == 'down' and
            num_selected > self.min_selected):
            self.state = 'normal'
        else:
            return

    @staticmethod
    def _clear_groups(wk):
        # auto flush the element when the weak reference have been deleted
        groups = MultichoiceToggleButtonBehavior.__groups
        for group in list(groups.values()):
            if wk in group:
                group.remove(wk)
                break

    @staticmethod
    def get_widgets(groupname):
        '''Return the widgets contained in a specific group. If the group
        doesn't exist, an empty list will be returned.

        .. important::

        Always release the result of this method! In doubt, do::

        l = MultichoiceToggleButtonBehavior.get_widgets('mygroup')
        # do your job
        del l

        .. warning::

        It's possible that some widgets that you have previously
        deleted are still in the list. Garbage collector might need
        more elements before flushing it. The return of this method
        is informative, you've been warned!
        '''
        groups = MultichoiceToggleButtonBehavior.__groups
        if groupname not in groups:
            return []
        return [x() for x in groups[groupname] if x()][:]

    
'''
Toggle button multi
===================
This is like a normal ToggleButton, but with the option to have more than one
button pressed at any given time
'''
class MultichoiceToggleButton(MultichoiceToggleButtonBehavior, Button):
    pass


if __name__ == '__main__':

    kv_string='''
BoxLayout:
    orientation: 'vertical'
    Label:
        text: 'our main dish today is Hummus.\\nPlease choose two side dishes:'

    BoxLayout:
        MultichoiceToggleButton:
            text: 'rice'
            group: 'side dishes'
            max_selected: 2
        MultichoiceToggleButton:
            text: 'salad'
            group: 'side dishes'
            max_selected: 2
        MultichoiceToggleButton:
            text: 'soup'
            group: 'side dishes'
            max_selected: 2
'''
    class TestApp(App):
        def build(self):
            return Builder.load_string(kv_string)
    
    TestApp().run()