from kivy.properties import StringProperty, ListProperty, DictProperty, BoundedNumericProperty, ObjectProperty
import numpy as np
from kivy.event import EventDispatcher
from datetime import datetime as dt, timedelta
import time
import gc
from instrumentino.controlino_protocol import ControlinoProtocol
from kivy.app import App
from instrumentino.channels import DataChannelIn
from instrumentino.cfg import *


class Controller(EventDispatcher):
    '''A general controller class
    '''

    name = StringProperty()
    '''The controller's name.
    '''

    url = StringProperty('')
    '''A link for more information about this controller.
    '''

    channel_types = DictProperty()
    '''A dictionary of channel types (keys) in this controller and the characters (values) to identify them in the
    controller. This should be filled by the controller subclass.
    e.g. {'analog_in': 'A',
          'digital': 'D',
          'pwm': 'P',
          'I2C': 'I'}
    '''

    channels = ListProperty()
    '''The list of all channels used in this controller
    '''

    input_channels = ListProperty()
    '''Registered input channels that need updating
    '''

    data_packet_rate = BoundedNumericProperty(ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
    '''The rate in which we want to receive data packets from the controller (in Hz).
    The data packet rate serves as a base rate for the allowed channel sampling rates in this controller.
    For example, for the default rate (10 Hz):
    - Sampling rates that are higher than the data packet rate must be
      multiples of this rate (e.g. 10, 20, 30, 40, ...).
    - Sampling rates that are lower than the data packet rate must be
      exact dividers of this rate (e.g. 5, 2, 1, 0.5, ...).
    This makes sure that we either have an integer number of data points per packet or a single data point arriving
    every X packets (X being an integer)
    '''

    comm_port = ObjectProperty(None, allownone=True)
    '''The communication port used for interacting with the controller
    '''

    comm_log = DictProperty({'connect': [], 'disconnect': []})
    '''Logs connectivity events such as 'connect' and 'disconnect' by saving
    timestamps in lists
    '''

    controlino_protocol = ObjectProperty(None)
    '''A handler to the controlino protocol
    '''

    t_zero = ObjectProperty()
    '''The time which is set to be 'zero' for timestamps exchanged between the controller and instrumentino. 
    '''

    def __init__(self, **kwargs):
        # Set a default name
        self.name = self.name or create_default_name(self)

        super(Controller, self).__init__(**kwargs)
        self.controlino_protocol = ControlinoProtocol(controller=self)

        # TODO: set the default URL as to be a google search URL.

    def add_channel(self, channel, **kwargs):
        '''Add a channel
        '''
        self.channels.append(channel)

        if isinstance(channel, DataChannelIn):
            self.input_channels.append(channel)

    def update_input_channels(self, data_packet):
        '''Update the input data channels with newly read values.
        
        This method should be called by the communication port when a new data packet arrives.
        '''

        # Convert the relative timestamp from milliseconds to seconds
        packet_timedelta = timedelta(seconds=data_packet.search('relative_start_timestamp') / 1000)

        # Parse the received data and add it to the appropriate channels
        # The received id field correlates to the index in the controller's channels list
        for block in data_packet.search('data_blocks'):
            channel = self.input_channels[block['block_id']]
            raw_data_points = block['data'][channel.fitting_datapoint_variable_name]
            channel.update_data_series(packet_timedelta, raw_data_points)

    def disconnect(self):
        ''' Disconnect communication.
        '''

        # Check if we're connected 
        if not self.comm_port:
            return

        self.comm_log['disconnect'].append(dt.now())

        self.comm_port.disconnect()
        self.comm_port = None

    def connect(self, communication_port):
        '''Setup a communication port for this controller.
        Return True/False to indicate success.
        '''
        if (communication_port is None or
                not communication_port.connect()):
            return False

        # Adopt this communication port
        self.comm_port = communication_port

        # Check controller response
        if not self.controlino_protocol.ping():
            # Disconnect if the controller doesn't respond
            communication_port.disconnect()
            return False

        # First, set up all of the channels
        for channel in self.channels:
            channel.do_first_when_online()

        # Now that we've prepared everything, ask the controller to start acquiring data
        now = dt.now()
        self.comm_log['connect'].append(now)
        self.t_zero = now
        self.controlino_protocol.start_acquiring_data()

        return True
