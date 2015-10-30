import kivy
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
kivy.require('1.8.0')
  
from kivy.app import App
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, BoundedNumericProperty
from weakref import ref
from kivy.uix.behaviors import ButtonBehavior

class ToggleButtonMultiBehavior(ButtonBehavior):
    '''like ToggleButton behavior, but allow more than 1 choosable button
    '''

    max_selected = BoundedNumericProperty(1, min=1)
    '''Max number of concurrently selected buttons
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the button. If None, no group will be used (button is
    independent). If specified, :attr:`group` must be a hashable object, like
    a string. Only one button in a group can be in 'down' state.

    :attr:`group` is a :class:`~kivy.properties.ObjectProperty`
    '''

    allow_no_selection = BooleanProperty(True)
    '''This specifies whether the checkbox in group allows everything to
    be deselected.

    ..versionadded::1.9.0

    :attr:`allow_no_selection` is a :class:`BooleanProperty` defaults to
    `True`
    '''

    def __init__(self, **kwargs):
        self._previous_group = None
        super(ToggleButtonMultiBehavior, self).__init__(**kwargs)
        
    def on_group(self, *largs):
        groups = ToggleButtonMultiBehavior.__groups
        if self._previous_group:
            group = groups[self._previous_group]
            for item in group[:]:
                if item() is self:
                    group.remove(item)
                    break
        group = self._previous_group = self.group
        if group not in groups:
            groups[group] = []
        r = ref(self, ToggleButtonMultiBehavior._clear_groups)
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
        num_selected = self.__get_num_selected()
        if (not self.allow_no_selection and
            self.group and self.state == 'down'
            and num_selected <= 1):
            return

        if self.state == 'normal':
            if num_selected < self.max_selected:
                self.state = 'down'
            else:
                return
        else:
            self.state = 'normal'

    @staticmethod
    def _clear_groups(wk):
        # auto flush the element when the weak reference have been deleted
        groups = ToggleButtonMultiBehavior.__groups
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

        l = ToggleButtonMultiBehavior.get_widgets('mygroup')
        # do your job
        del l

        .. warning::

        It's possible that some widgets that you have previously
        deleted are still in the list. Garbage collector might need
        more elements before flushing it. The return of this method
        is informative, you've been warned!
        '''
        groups = ToggleButtonMultiBehavior.__groups
        if groupname not in groups:
            return []
        return [x() for x in groups[groupname] if x()][:]


'''
Toggle button multi
===================
This is like a normal ToggleButton, but with the option to have more than one
button pressed at any given time
'''
class ToggleButtonMulti(ToggleButtonMultiBehavior, Button):
    pass





kv_string='''
BoxLayout:
    ToggleButtonMulti:
        max_selected: 2
        group: 'a'
    ToggleButtonMulti:
        max_selected: 2
        group: 'a'
    ToggleButtonMulti:
        max_selected: 2
        group: 'a'
'''
class TestApp(App):
    def build(self):
        return Builder.load_string(kv_string)

if __name__ == '__main__':
    TestApp().run()