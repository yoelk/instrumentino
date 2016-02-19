from __future__ import division
from kivy.lang import Builder
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.uix.settings import SettingsWithSidebar, SettingOptions
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import sp
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

from .libs.garden.graph import Graph, MeshLinePlot
from .libs.garden.navigationdrawer import NavigationDrawer

import importlib
import json
import os
import datetime
from os.path import dirname, join 
import random
from exceptions import RuntimeError
from .screens.control import MyControlView
from .screens.automation import MyAutomationView
from .screens.signal import MySignalView
from .screens.automation import Action

from instrumentino.popups import ProfileLoader,Help,ActivityLog,FileChooser,ExitConfirmation
from instrumentino.communication import CommunicationTypesLoader
from instrumentino.communication.serial_port import CommunicationPortSerial
import time
from instrumentino.communication.simulated_port import CommunicationPortSimulation
from instrumentino.cfg import *
import gc
            
class Instrumentino(NavigationDrawer):
    pass

class InstrumentinoApp(App):
    '''The main application
    '''
    
    top = ObjectProperty(None)
    '''The top widget of the application
    '''
    
    controllers = ListProperty()
    '''The connected hardware controllers
    '''
    
    components = ListProperty([])
    '''The hardware components to be controlled
    '''
    
    actions = ListProperty([])
    '''The actions that the system should perform
    '''

    SETTINGS_KEY_SEPARATOR = '---'
    '''A string separator to be used in complex keys that are made of two parts.
    For example: 'Arduino1>CommType' is the key for the communication type of controller 'Arduino1'
    '''

    SETTINGS_COMM_MENU = 'COMM'
    '''The name of the comm menu in the settings file
    '''

    SETTINGS_KEY_COMM_TYPE = 'comm_type'
    '''The key name for communication type (e.g. Serial, TCP/IP, etc.)
    '''

    SETTINGS_KEY_COMM_ADDRESS = 'comm_address'
    '''The address for the communication type (e.g. COM2, 10.0.0.1, etc.)
    '''

    SETTINGS_KEY_COMM_STATUS = 'comm_status'
    '''The key name for communication status (is the controller connected or not)
    '''

    def __init__(self, **kwargs):
        super(InstrumentinoApp, self).__init__(**kwargs)
        
        # Bind methods to the keyboard
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    ##########
    # Keyboard methods
    ##########
    def _keyboard_closed(self):
        '''Keyboard closed.  Only for virtual keyboards?
        '''
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        '''Capture keyboard input
           The values of the keys are the keycode "common names" used in pygame.
           See: http://www.pygame.org/docs/ref/key.html
        '''
        # Return True to accept/capture the key. Otherwise, it will also be used by
        # the system.
        if keycode[1] == 'escape':
            self.ShowExitConfirmation()
            return True

    ##########
    # Controller methods
    ##########
    def add_controller(self, controller):
        '''Add a controller.
        '''
        self.controllers.append(controller)

    def remove_controller(self, name):
        '''Remove a single controller, by the "name" attribute.
        '''
        for ndx, controller in enumerate(self.controllers):
            if str(controller.name) == name:
                del self.controllers[ndx]

    def remove_controllers(self):
        '''Remove all controllers.
        '''
        for ndx, controller in enumerate(self.controllers):
            self.remove_controller(controller.name)

    ##########
    # Component methods
    ##########
    def add_component(self, comp):
        '''Add a component.
        '''
        self.components.append(comp)
        
    def remove_component(self, name):
        '''Remove a single component, by the "name" attribute.
        '''
        for ndx, component in enumerate(self.components):
            if str(component.name) == name:
                # Notify the controller to unregister all input channels
                for var in component.variables:
                    if var.channel_in:
                        var.channel_in.unregister()

                # Clean up the UI widgets
                component.remove_variables()

                # Delete the component
                del self.components[ndx]

    def remove_components(self):
        '''Remove all components.
        '''
        for ndx, component in enumerate(self.components):
            self.remove_component(component.name)

    ##########
    # Action methods
    ##########
    def add_action(self, action):
        '''Add an action
        '''
        self.actions.append(action)

    def remove_action(self, name):
        '''Remove a single action, by the "name" attribute.
        '''
        for ndx, action in enumerate(self.actions):
            if str(action.name) == name:
                del self.actions[ndx]

    def remove_actions(self):
        '''Remove all actions.
        '''
        for ndx, action in enumerate(self.actions):
            self.remove_action(action.name)

    def build(self):
        '''Build the screen.
        '''
        # Settings
        self.settings_cls = InstrumentinoSettings
        
        self.top = Instrumentino()
        
        # add the possible views to the screen manager
        self.top.screen_manager.add_view(MyControlView(name='Control', components=self.components))
        self.top.screen_manager.add_view(MyAutomationView(name='Automation', actions=self.actions))
        self.top.screen_manager.add_view(MySignalView(name='Signal', components=self.components))
        
        # Application styling
        # TODO: App Icon: It works if you pass the full path to the file
        #self.icon = '<ROOT PATH>/instrumentino2/instrumentino2/kivy/resources/icon32/logo.png'
        self.title = 'Instrumentino'

        return self.top
    
    # BEGIN: Settings
    # https://www.youtube.com/watch?v=oQdGWeN51EE
    def build_config(self, config):
        # http://kivy.org/docs/api-kivy.app.html#kivy.app.App.build_config
        # Kivy core settings .ini file: http://kivy.org/docs/guide/config.html
        # http://pymotw.com/2/ConfigParser/
        config.read(self.get_application_config())
        
        # Add special environment specific settings to config
        # Options: get, getint, getfloat, getboolean
        # Remove them on exit!
        config.set('DEFAULT', 'home_dir', dirname(__file__))
        # # Go 'up' one directory to the project directory
        config.set('DEFAULT', 'project_dir', dirname(dirname(__file__)))

        # Reset the communication settings
        config.remove_section(self.SETTINGS_COMM_MENU)
        config.add_section(self.SETTINGS_COMM_MENU)
        for controller in self.controllers:
            config.set(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_TYPE), CommunicationTypesLoader.get_comm_types().keys()[0])
            config.set(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_ADDRESS), '')
            config.set(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_STATUS), '0')

        config.write()

        # Initial window size handling
        #print "DPI: " + str(Window.dpi)
        #print "Rotation: " + str(Window.rotation)
        #print "Size: " + str(Window.size) # [width, height]
        #print "System Size: " + str(Window.system_size) # [width, height]
        #print "Height: " + str(Window.height)
        #print "Width: " + str(Window.width)

    def create_settings_key(self, controller_name, setting_name):
        '''Create a key string for a controller's connection setting. 
        '''
        return '{}{}{}'.format(controller_name, self.SETTINGS_KEY_SEPARATOR, setting_name)
    
    def parse_settings_key(self, key):
        '''Parse a key and return the controller's name and the setting's name 
        '''
        return key.split(self.SETTINGS_KEY_SEPARATOR)

    def build_settings(self, settings):
        pDir = self.config.get('DEFAULT', 'settings_panels_dir')
        
        # Add the connectivity options for the needed controllers
        comm_menu = []
        for controller in self.controllers:
            # A choice of available communication types (Serial, TCP/IP, etc.)
            comm_menu.append({'type': 'title',
                              'title': controller.name})
            comm_menu.append({'type': "options",
                              'title': 'Connection',
                              'desc': 'Connection type',
                              'section': self.SETTINGS_COMM_MENU,
                              'key': self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_TYPE),
                              'options': CommunicationTypesLoader.get_comm_types().keys()})
            
            # Create address field according to the communication type
            comm_type = self.config.get(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_TYPE))
            comm_class = CommunicationTypesLoader.get_comm_types()[comm_type]
            address_json_dict = {'title': 'Address',
                                 'desc': 'Communication address',
                                 'section': self.SETTINGS_COMM_MENU,
                                 'key': self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_ADDRESS)}
            comm_class.modify_address_field_options_for_settings_menu(address_json_dict)
            comm_menu.append(address_json_dict)
            
            # Add the connection status field
            comm_menu.append({'type': 'bool',
                              'title': 'Online',
                              'desc': 'Communication status',
                              'section': self.SETTINGS_COMM_MENU,
                              'key': self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_STATUS)})
            
        settings.add_json_panel('Comm', self.config, data=json.dumps(comm_menu))
        
        settings.add_json_panel('Example panel', self.config, join(pDir,'example.json'))
        settings.add_json_panel('Files and Directories', self.config, join(pDir,'files_and_dirs.json'))
        settings.add_json_panel('Profile', self.config, join(pDir,'profile.json'))

    def on_config_change(self, config, section, key, value):
        print 'Config settings changed. Section:' + section + '. Key: ' + key + '. Value: ' + value
        
        # Act on Comm settings changes
        if section == self.SETTINGS_COMM_MENU:
            [controller_name, setting_name] = self.parse_settings_key(key)
            controller = [c for c in self.controllers if c.name == controller_name][0]
            if setting_name == self.SETTINGS_KEY_COMM_STATUS:
                if value == '0':
                    controller.disconnect()
                else:
                    # Try to connect with the current settings
                    address = self.config.get(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_ADDRESS))
                    comm_type = self.config.get(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_TYPE))
                    comm_class = CommunicationTypesLoader.get_comm_types()[comm_type]
                    communication_port = comm_class(controller=controller, address=address)
                    comm_established = controller.connect(communication_port)
                    config.set(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_STATUS), '1' if comm_established else '0')
                    config.write()
                    self.refresh_settings_menu()
                            
            if setting_name == self.SETTINGS_KEY_COMM_TYPE:
                # Refresh the settings menu with the updated address field
                config.set(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_ADDRESS), '')
                config.set(self.SETTINGS_COMM_MENU, self.create_settings_key(controller.name, self.SETTINGS_KEY_COMM_STATUS), '0')
                controller.disconnect()
                config.write()
                self.refresh_settings_menu()
                
    def refresh_settings_menu(self):
        '''Rebuild the settings menu and display it.
        To be used when we change some setting in the code and we want to GUI to reflect that.
        '''
        self.close_settings()
        self.open_settings()
        
    def open_settings(self, *largs):
        '''Override. Make sure that the settings are newly created when the panel is opened. 
        '''
        self.destroy_settings()
        super(InstrumentinoApp, self).open_settings()
                               
    # END: Settings

    # BEGIN: Popups
    def OpenFileChooserLoad(self,dir,filter):
        f = FileChooser()
        f.show_load(dir,filter)
        
    def OpenFileChooserSave(self,dir,filter):
        f = FileChooser()
        f.show_save(dir,filter)
    
    def ShowHelp(self):
        p = Help()
        p.open()

    def ShowUserLog(self):
        p = ActivityLog()
        p.open()
    
    def ShowProfileLoader(self):
        p = ProfileLoader(app=self)
        p.open()

    def ShowExitConfirmation(self):
        p = ExitConfirmation()
        p.open()
    # END: Popups
    
    def LogToScreen(self,s):
        print "TO DO: LogToScreen()"

    def on_start(self):
        self.top.screen_manager.on_start()
        
        # For some reason when using the fade transition in the screen manager, the initial view
        # doesn't fill the screen. So schedule a small window height change in one second to trigger
        # an update
        # TODO: find a better solution
        Clock.schedule_once(lambda dt: self.force_update_size(), 1)

        if DEBUG_AUTO_CONNECT['connect']:
            if DEBUG_AUTO_CONNECT['type'] == 'serial':
                communication_port = CommunicationPortSerial(controller=self.controllers[0], address=DEBUG_AUTO_CONNECT['address'])
            elif DEBUG_AUTO_CONNECT['type'] == 'simulation':
                communication_port = CommunicationPortSimulation(controller=self.controllers[0], address='')
            print 'online: {}'.format(self.controllers[0].connect(communication_port))
        
    def force_update_size(self):
        '''Add a negligible value to the height, to force the children to update their height
        
        TODO: check if there is a better way to solve this problem
        '''
        
        (x, y) = Window.size
        Window.size = (x, y+2)
    
    def on_stop(self):
        '''The application stops so clean up
        '''
        
        # Disconnect from controllers
        for controller in self.controllers:
            controller.disconnect()
        
        # Blow away this var as we set it fresh every on startup
        # and don't want to upload an invalid patch to Github
        self.config.set('DEFAULT', 'home_dir', 'WILL-BE-AUTO-SET')
        self.config.set('DEFAULT', 'project_dir', 'WILL-BE-AUTO-SET')
        self.config.write()
    
    # BEGIN: Mobile devices only
    def on_pause(self):
        # TO DO: Save data?
        return True

    def on_resume(self):
        pass
    # END: Mobile devices only
    
    def SaveChart(self):#TODO: this doesn't work now. we need to support all kinds of data saving modes
        graph = self.top.ids.my_graph
        gDir = self.config.get('files_and_dirs', 'user_dir')
        # TO DO: file name: just get by for now.
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file = join(gDir,date+'_chart.png')
        print "SaveChart: " + file
        graph.export_to_png(file)

    @staticmethod
    def create_default_name(object_self):
        '''Create a default name for GUI items that didn't get their name defined.
        For example, if an controller from class "Arduino" isn't given a name specifically, it will be called "Arduino 1"
        '''
        return '{} {}'.format(type(object_self).__name__, len([obj for obj in gc.get_objects() if isinstance(obj, type(object_self))]))


class SettingDynamicOptions(SettingOptions):
    '''Implementation of an option list that creates the items in the possible
    options list by calling an external method, that should be defined in
    the settings class.
    '''

    function_string = StringProperty()
    '''The function's name to call each time the list should be updated.
    It should return a list of strings, to be used for the options.
    '''

    def _create_popup(self, instance):
        # Update the options
        mod_name, func_name = self.function_string.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        self.options = func()
        
        # Call the parent __init__
        super(SettingDynamicOptions, self)._create_popup(instance)


class InstrumentinoSettings(SettingsWithSidebar):
    '''Customized settings panel for Instrumentino.
    '''
    def __init__(self, *args, **kargs):
        super(InstrumentinoSettings, self).__init__(*args, **kargs)
        self.register_type('dynamic_options', SettingDynamicOptions)
        
        
# Load all of the kv files
Builder.load_file('instrumentino/screens/screens.kv')
Builder.load_file('instrumentino/components/components.kv')
Builder.load_file('instrumentino/variables/variables.kv')
Builder.load_file('instrumentino/popups/popups.kv')
