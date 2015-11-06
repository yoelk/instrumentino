from __future__ import division
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.event import EventDispatcher
from __builtin__ import NotImplementedError
from threading import Semaphore
import os
import inspect
import glob
import importlib
from kivy.clock import Clock
import time
from kivy.app import App
from instrumentino.cfg import *

class CommunicationPort(EventDispatcher):
    '''A communication port for interfacing with a hardware controller.
    '''

    MAX_BYTES_PER_READ = NumericProperty(1000)
    '''The maximal number of bytes to read in each read cycle.
    '''
    
    controller = ObjectProperty(None)
    '''The controller for which this communication port is used.
    '''

    address = StringProperty(None)
    '''The address to be used when connecting (e.g. COM2 for Serial, 10.0.0.1 for TCP/IP, etc.).
    '''

    incoming_bytes = bytearray()
    '''Incoming bytes to be parsed into packets.
    '''
    
    transmit_semaphore = Semaphore()
    '''A semaphore to make sure the transmit function is called sequentially
    '''
    
    def __init__(self, **kwargs):
        # Check that all of the necessary kwargs are given
        if not set(['controller']) <= set(kwargs): raise MissingKwargsError()
        
        # Check that the sub-class has a type_name. This is used for GUI purposes, to show the communication type on the screen
        if not hasattr(self, 'type_name'): raise AttributeError('Subclasses should have a type_name attribute')
        
        super(CommunicationPort, self).__init__(**kwargs)

    def connect(self):
        '''Set up communication and schedule periodic reading to check for incoming packets.
        Return True or False to indicate if connection was successful.
        '''
        if self._connect():
            Clock.schedule_interval(self.receive, 1/self.controller.data_packet_rate)
            return True
        else:
            return False
            
    def disconnect(self):
        '''Unschedule readings.
        '''
        Clock.unschedule(self.receive)
        self._disconnect()
            
    def transmit(self, packet):
        '''Transmit a packet to the controller, checking that there are no parallel calls
        '''
        self.transmit_semaphore.acquire()
        if DEBUG_TX:
            print 'TX: {}'.format(packet)
        self._transmit(packet)
        self.transmit_semaphore.release()

    def receive(self, dt=0):
        '''Receive incoming bytes and pass them on to the protocol class for parsing.
        This function should be called either regularly or upon interrupt, according to the communication port implementation.
        '''
        
        # Get incoming bytes from the sub-class
        new_incoming_bytes = self._get_incoming_bytes()

        if new_incoming_bytes:

            # Add the incoming data to the buffer.
            self.incoming_bytes.extend(new_incoming_bytes)
            
            # Ask the protocol to parse the data and delete whatever was used.
            self.controller.controlino_protocol.handle_incoming_bytes(self.incoming_bytes)

    def _connect(self):
        '''Set up communication.
        Return True or False to indicate if connection was successful.
        Sub-classes should implement this.
        '''
        return False
    
    def _disconnect(self):
        '''Disconnect communication.
        Sub-classes should implement this.
        '''
        pass
    
    def _transmit(self, packet):
        '''Transmit a packet to the controller.
        Sub-classes should implement this.
        '''
        pass

    def _get_incoming_bytes(self):
        '''Check if new bytes have arrived from the controller, and return them is they have. 
        Sub-classes should implement this.
        '''
        return None
                    
    @staticmethod
    def modify_address_field_options_for_settings_menu(json_dict):
        '''Modify the address item in the settings menu. 
        Sub-classes should implement this.
        '''
        raise NotImplementedError()

class CommunicationTypesLoader(EventDispatcher):
    '''A class to load all available types of communication with controllers.
    '''
    
    @staticmethod
    def get_comm_types():
        '''Load all of the available communication types by looking in the current folder
        and loading all of the relevant classes.
        '''
        
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        current_module_name = os.path.splitext(os.path.basename(current_dir))[0]

        comm_types = {}
        for file in glob.glob(current_dir + "/*.py"):
            name = os.path.splitext(os.path.basename(file))[0]
             
            # TODO: find a way to get this path without defining it statically
            module = importlib.import_module("." + name,package='instrumentino.communication')

            for member in dir(module):
                handler_class = getattr(module, member)
        
                if (handler_class and
                    inspect.isclass(handler_class) and
                    issubclass(handler_class, CommunicationPort) and
                    handler_class is not CommunicationPort):
                    comm_types[handler_class.type_name] = handler_class
        
        return comm_types