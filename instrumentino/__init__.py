from __future__ import division
import importlib
import json
import os
import datetime
from os.path import dirname, join 
import random
from exceptions import RuntimeError
import time
import sys
from __builtin__ import isinstance
from inspect import isclass

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

from kivy.garden.graph import Graph, MeshLinePlot
from kivy.garden.navigationdrawer import NavigationDrawer

from instrumentino.popups import ProfileLoader,Help,ActivityLog,ExitConfirmation
from instrumentino.communication import CommunicationTypesLoader
from instrumentino.communication.serial_port import CommunicationPortSerial
from instrumentino.communication.simulated_port import CommunicationPortSimulation
from instrumentino.cfg import *
from instrumentino.controllers import Controller
from instrumentino.controllers.arduino import Arduino
from instrumentino.screens.automation import ActionRunSequenceFile, MyAutomationView, Action
from instrumentino.components import Component
from instrumentino.screens.control import MyControlView
from instrumentino.screens.signal import MySignalView

            
class Instrumentino(NavigationDrawer):
    pass

class InstrumentinoApp(App):
    '''The main application
    '''
    
    top = ObjectProperty(None)
    '''The top widget of the application
    '''
    
    instrument_module = StringProperty('__main__')
    '''The system configuration module for the current loaded instrument 
    '''
    
    controllers = ListProperty()
    '''The connected hardware controllers
    '''
    
    components = ListProperty([])
    '''The hardware components to be controlled
    '''
    
    action_classes = ListProperty([])
    '''The classes of the actions that the system should perform
    '''
    
    default_action_classes = ListProperty([ActionRunSequenceFile])
    '''Default action classes, that are valid for every instrument
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
        
        # Extract data from the instrument module
        self.controllers = get_instances_in_module(self.instrument_module, Controller)
        if not self.controllers: raise RuntimeError('At least one controller must be defined')
        
        self.components = get_instances_in_module(self.instrument_module, Component)

        self.action_classes = [c for c in sys.modules[self.instrument_module].__dict__.values() if isclass(c) and issubclass(c, Action) and c is not Action]
        self.action_classes.extend(self.default_action_classes)
        
    def get_instrument_path(self):
        '''Return the path to the current instrument file
        '''
        return os.path.dirname(sys.modules[self.instrument_module].__file__)
    
    def build(self):
        '''Build the screen.
        '''
        # Settings
        self.settings_cls = InstrumentinoSettings
        
        self.top = Instrumentino()
        
        # add the possible views to the screen manager
        self.top.screen_manager.add_view(MyControlView(name='Control', components=self.components))
        self.top.screen_manager.add_view(MyAutomationView(name='Automation', action_classes=self.action_classes))
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
        f = FileChooserPopup()
        f.show_load(dir,filter)
        
    def OpenFileChooserSave(self,dir,filter):
        f = FileChooserPopup()
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
        
        if DEBUG_AUTO_CONNECT['connect']:
            if DEBUG_AUTO_CONNECT['type'] == 'serial':
                communication_port = CommunicationPortSerial(controller=self.controllers[0], address=DEBUG_AUTO_CONNECT['address'])
            elif DEBUG_AUTO_CONNECT['type'] == 'simulation':
                communication_port = CommunicationPortSimulation(controller=self.controllers[0], address='')
            print 'online: {}'.format(self.controllers[0].connect(communication_port))
        
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
Builder.load_file('screens/control/control.kv')
Builder.load_file('components/components.kv')
Builder.load_file('screens/screens.kv')
Builder.load_file('screens/automation/automation.kv')
Builder.load_file('screens/signal/signal.kv')
Builder.load_file('variables/variables.kv')
Builder.load_file('popups/popups.kv')