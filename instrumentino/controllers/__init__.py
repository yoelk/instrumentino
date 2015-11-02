from __future__ import division
from kivy.properties import StringProperty, ListProperty, DictProperty, BoundedNumericProperty, ObjectProperty
import numpy as np
from kivy.event import EventDispatcher
from construct.core import Struct, Sequence
from construct.macros import UBInt8, UBInt16, UBInt32, UBInt64, PrefixedArray, \
    CString, Enum, GreedyRange, Array, OptionalGreedyRange
from construct import Embed
from construct.lib.container import Container
import time
import gc
from instrumentino.channels.blocks import TimeBlock, DataBlock
from instrumentino.controlino_protocol import ControlinoProtocol

class Controller(EventDispatcher):
    '''A general controller class
    ''' 
    
    name = StringProperty('a controller')
    '''The controller's name.
    '''
    
    url = StringProperty('')
    '''A link for more information about this controller.
    '''

    channel_types = DictProperty()
    '''A dictionary of channel types (keys) in this controller and the characters (values) to identify them in the controller.
    This should be filled by the controller subclass.
    e.g. {'analog_in': 'A',
          'digital': 'D',
          'pwm': 'P',
          'I2C': 'I'}
    '''
    
    input_channels = ListProperty()
    '''Registered input channels that need updating
    '''
    
    time_blocks = ListProperty()
    '''A list that contains all of the data that was recorded for this
    controller. A data block starts whenever a controller is connected
    (having an online communication_port). Each block contains a dictionary of
    timestamp_series (one for each sampling_rate). The data associated with the
    timestamps is stored in each individual channel, in their own data_blocks. 
    '''

    data_packet_rate = BoundedNumericProperty(ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
    '''The rate in which we want to receive data packets from the controller (in Hz).
    The data packet rate serves as a base rate for the allowed channel sampling rates in this controller.
    For example, for the default rate (10 Hz):
    - Sampling rates that are higher than the data packet rate must be multiples of this rate (e.g. 10, 20, 30, 40, ...).
    - Sampling rates that are lower than the data packet rate must be exact dividers of this rate (e.g. 5, 2, 1, 0.5, ...).
    This makes sure that we either have an integer number of data points per packet or a single data point arriving every X packets (X being an integer)
    '''
    
    communication_port = ObjectProperty(None, allownone=True)
    '''The communication port used for interacting with the controller
    '''

    controlino_protocol = ObjectProperty(None)
    '''A handler to the controlino protocol
    '''

    t_zero = BoundedNumericProperty(0, min=0)
    '''The time which is set to be 'zero' for timestamps exchanged between the controller and instrumentino. 
    '''

    def __init__(self, **kwargs):
        # Set a default name
        if not set(['name']) <= set(kwargs):
            self.name = '{} {}'.format(type(self).__name__, len([obj for obj in gc.get_objects() if isinstance(obj, type(self))]))
        
        super(Controller, self).__init__(**kwargs)
        self.controlino_protocol = ControlinoProtocol(controller=self)
        
        # Add the first time block without setting its t_zero. It will be set later when comm is online.
        self.time_blocks.append(TimeBlock())
        
        #TODO: set the default URL as to be a google search URL.

    def get_fitting_data_point_variable(self, bytes_num):
        '''Translate between the number of required bytes per data point and an appropriately sized variable.
        '''
        return {0<bytes_num<=1: UBInt8(''),
                1<bytes_num<=2: UBInt16(''),
                2<bytes_num<=4: UBInt32(''),
                4<bytes_num<=8: UBInt64(''),
                }[True]                

    def get_time_block(self, timestamp=None):
        '''Return the relevant time block according to the given timestamp
        '''
        # Use the current time if not specified
        timestamp = timestamp or time.time()

        # Find a fitting time block. The last one is usually the relevant one.
        for block in reversed(self.time_blocks):
            if ((block.t_zero != 0 and block.t_zero <= timestamp) and
                (block.t_end == 0 or block.t_end >= timestamp)):
                return block
        
        # No relevant block was found
        return None

    def add_input_channel(self, channel, **kwargs):
        '''Add an input channel for updating
        '''
        # by default request a single data point in each data packet
        sampling_rate = kwargs.get('sampling_rate', ControlinoProtocol.DEFAULT_DATA_PACKET_RATE)

        # Use the first data block (t_zero not set yet)
        timestamp_series_dict = self.time_blocks[0].timestamp_series_dict
        
        # Start a new timestamp series if necessary.
        if sampling_rate not in timestamp_series_dict:
            timestamp_series_dict[sampling_rate] = []

        # Add a data block that uses the relevant timestamp series from the controller.
        channel.data_blocks.append(DataBlock(timestamp_series=timestamp_series_dict[sampling_rate]))
        
        # Set the appropriate serialized format class, in order to handle incoming data packets
        channel.data_points_serialized_format = GreedyRange(self.get_fitting_data_point_variable(channel.data_bytes))
        
        self.input_channels.append(channel)
    
    def update_input_channels(self, new_data_packet):
        '''Update the input data channels with newly read values.
        
        This method should be called by the communication port when a new data packet arrives.
        '''
        
        data_packet = self.controlino_protocol.data_packet_format.parse(new_data_packet)
        data_blocks = data_packet['data_packet_block']
        
        # Convert the relative timestamp from milliseconds to seconds
        relative_start_timestamp = data_packet['relative_start_timestamp'] / 1000

        # Use the relevant time block
        timestamp_series_dict = self.get_time_block().timestamp_series_dict
        
        # Prepare a temporary dictionary to point to all of the existing timestamp_series (there is one for each sampling_rate).
        # This will be used to make sure we only update each of them once, as it may be used for more than one data_series.
        #
        # The second value in the tuple is the number of points that have been added as padding or overwritten
        # in the timestamp series, in order to follow the same procedure in the data series.
        timestamp_series_updated = {key:{'updated':False, 'points_difference':0} for key in timestamp_series_dict.keys()}
        
        # Parse the received data and add it to the appropriate channels
        # The received id field correlates to the index in the controller's channels list
        for block in data_blocks:
            channel = self.input_channels[block['id']]
            ubint_buffer = GreedyRange(UBInt8(''))
            new_data_points = channel.data_points_serialized_format.parse(ubint_buffer.build(block['data_points']))
            
            # Update the timestamp series. Channels which have the same sampling rate share their timestamp series
            # so we only need to update it once. 
            if not timestamp_series_updated[channel.sampling_rate]['updated']:
                points_added_or_deleted = channel.update_timestamp_series(relative_start_timestamp, len(new_data_points))
                
                # Mark this series as updated
                timestamp_series_updated[channel.sampling_rate]['updated'] = True
                timestamp_series_updated[channel.sampling_rate]['points_difference'] = points_added_or_deleted
            
            # Update the data series.
            channel.update_data_series(new_data_points, timestamp_series_updated[channel.sampling_rate]['points_difference'])
                
    def disconnect(self):
        ''' Disconnect communication.
        '''
        
        # Check if we're connected 
        if not self.communication_port:
            return
        
        self.communication_port.disconnect()
        self.communication_port = None
        
        # Close the time block
        if self.get_time_block():
            now = time.time()
            self.get_time_block().t_end = now
        
        for channel in self.input_channels:
            if channel.get_data_block():
                channel.get_data_block().t_end = now
    
    def connect(self, communication_port):
        '''Setup a communication port for this controller.
        Return True/False to indicate success.
        '''
        if (communication_port == None or
            not communication_port.connect()):
            return False
        
        # Adopt this communication port
        self.communication_port = communication_port
        
        # Check controller response
        if not self.controlino_protocol.ping():
            # Disconnect if the controller doesn't respond
            communication_port.disconnect()
            return False
        
        # Set t=0 in the controller so we have a mutual time base, and open a new timestamp block for this session
        # If a time block already exists but hasn't had its t_zero set, update it and use this one.
        self.t_zero = time.time()
        self.controlino_protocol.start_acquiring_data()
        if not self.time_blocks[-1].t_zero:
            self.time_blocks[-1].t_zero = self.t_zero
        else:
            # Create a new time block, based on the last time block
            self.time_blocks.append(self.time_blocks[-1].copy(self.t_zero)) 
            
        # Now that communication is up, notify the controller that we want to start getting data.
        # Open a new data block for each channel, corresponding to the timestamp block.
        # If a data block already exists but hasn't had its t_zero set, update it and use this one.
        for channel in self.input_channels:
            if not channel.data_blocks[-1].t_zero:
                channel.data_blocks[-1].t_zero = self.t_zero
            else:
                channel.data_blocks.append(DataBlock(timestamp_series=self.get_time_block().timestamp_series_dict[channel.sampling_rate],
                                                     t_zero=self.t_zero))
            self.controlino_protocol.register_input_channel(channel)

        return True

