from kivy.properties import ListProperty
from instrumentino.screens import MyView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView
from kivy.adapters.listadapter import ListAdapter
from instrumentino.components import Component
from instrumentino.cfg import check_for_necessary_attributes


class MyControlView(BoxLayout, MyView):
    '''The Control view allows the user to manually control and monitor all of the system's components individually
    '''

    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['components'], kwargs)
        super(MyControlView, self).__init__(**kwargs)

        # Add components
        for comp in self.components:
            self.components_list.adapter.data.append(comp)
        self.components_list._trigger_reset_populate()
