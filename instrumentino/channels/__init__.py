from __future__ import division
from kivy.properties import ObjectProperty, ListProperty, StringProperty, BoundedNumericProperty, NumericProperty, AliasProperty
import time
import random
from kivy.event import EventDispatcher
from __builtin__ import ValueError
from math import ceil
import numpy as np
from instrumentino.libs.abs_ratio import abs_ratio
from instrumentino.controlino_protocol import ControlinoProtocol
from kivy.app import App
from instrumentino.cfg import *

class DataChannel(EventDispatcher):
    '''A single data channel between instrumentino and controllers connected to it
    '''

    type_str = StringProperty()
    '''A string that identifies this data channel's type in the controller. (e.g. 'D' for digital pins)
    '''
    
    number = NumericProperty()
    '''A number that identifies this data channel's number in the controller (e.g. a pin's number).
    '''

    controller = ObjectProperty()
    '''The relevant controller for this channel
    '''
    
    variable = ObjectProperty()
    '''The relevant variable for this channel
    '''
    
    data_bits = BoundedNumericProperty(8, min=1)
    '''The number of bits for each data point transferred in the channel.
    '''

    data_bytes = BoundedNumericProperty(1, min=1)
    '''The number of bytes for each data point transferred in the channel.
    This is inferred from the number of bits.
    '''
    
    data_points_serialized_format = ObjectProperty()
    '''The serialized format of data points for this channel in incoming data packets
    '''

    def __init__(self, **kwargs):
        if not set(['controller', 'data_bits', 'type_str', 'number']) <= set(kwargs): raise MissingKwargsError()
            
        super(DataChannel, self).__init__(**kwargs)
        self.data_bytes = ceil(self.data_bits/8)

    def get_identifier(self):
        '''Return a string that identifies this data channel in the controller.
        It is made of the channel's type and its number (e.g. 'D1')
        '''
        return self.type_str + str(self.number)
        

class DataChannelIn(DataChannel):
    '''Data flows from a controller to instrumentino
    '''

    data_blocks = ListProperty()
    '''A list that contains all of the data that was recorded for this
    channel. A data block starts whenever a controller is connected
    (having an online communication_port). Each block contains a data_series.
    The timestamps associated with the data are stored in the controller's data_blocks. 
    '''

    sampling_rate = BoundedNumericProperty(ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
    '''The channel's sampling rate (in Hz).
    '''
    
    max_input_value = NumericProperty()
    '''The maximal native value that can be read for this channel.
    It can be only a positive integer.
    '''
    
    def __init__(self, **kwargs):
        super(DataChannelIn, self).__init__(**kwargs)
        
        if not set(['max_input_value']) <= set(kwargs): raise MissingKwargsError()
        
        # Check that the sampling rate is valid
        if not abs_ratio(self.sampling_rate, self.controller.data_packet_rate).is_integer():
            raise ValueError("Sampling rate doesn't fit controller's data packet rate")
        
        # Add the channel in the controller
        self.controller.add_input_channel(self, sampling_rate=self.sampling_rate)

    def translate_incoming_data(self, data):
        '''Incoming data is received as whole numbers (not floating point) that result in native read functions in the controller.
        For the sake of uniformity, all values should be translated to a [0-100] scale.
        '''
        data[:] = [x / self.max_input_value * 100 for x in data]

    def get_data_block(self, timestamp=None):
        '''Return the relevant data block according to the given timestamp
        '''
        # Use the current time if not specified
        timestamp = timestamp or time.time()
        
        for block in reversed(self.data_blocks):
            if ((block.t_zero != 0 and block.t_zero <= timestamp) and
                (block.t_end == 0 or block.t_end >= timestamp)):
                return block
            
        # No relevant block was found
        return None
    
    def update_timestamp_series(self, relative_start_timestamp, new_data_points_num):
        '''Update the timestamp series with incoming data. The added timestamps are aligned to the expected timestamps in the series.
        For example, in a 1 Hz channel, the timestamp series (relative to t_zero) will be [0,1,2,...] even if we got [0.1,1.05,1.99,...].
        Because timing can't be perfect, we might get positive or negative drifts.
        If the received start timestamp is too late (positive drift), fill in the gap.
        If it's too early (negative drift), overwrite the existing data.
        
        Return the number of points that were added as padding (positive value)
        or the number of old points that were deleted (negative value).
        '''
        # Use the relevant data block
        timestamp_series = self.get_data_block().timestamp_series
        
        aligned_start_index = int(round(relative_start_timestamp * self.sampling_rate))
        points_difference = aligned_start_index - len(timestamp_series)
        
        if DEBUG_COMM_STABILITY:
            if points_difference != 0: print 'points difference: {}'.format(points_difference)
        
        if points_difference > 0:
            # Add dummy time points to fill the gap between the last known time point and the first new one.
            new_data_points_num += points_difference
        elif points_difference < 0:
            # Delete old time points so we can rewrite them.
            for _ in range(abs(points_difference)):
                timestamp_series.pop()
        
        # Add the new time points to the series
        adjusted_aligned_start_index = aligned_start_index - points_difference
        timestamp_series.extend([self.controller.t_zero + (1/self.sampling_rate)*(adjusted_aligned_start_index+i) for i in range(new_data_points_num)])
        
        return points_difference
    
    def update_data_series(self, new_data_points, points_difference):
        '''Update the data series with new data points. Pad with 'None' points or overwrite old data points
        in order to keep the data_series in line with the timestamp_series 
        '''
        # Translate the incoming data to a percentage scale (0-100)
        # The translated data can be presented in the graph 
        self.translate_incoming_data(new_data_points)
        
        # Use the relevant data block
        data_series = self.get_data_block().data_series
        
        if points_difference > 0:
            # Add dummy data points to fill the gap between the last known data point and the first new one.
            new_data_points = [None]*points_difference + new_data_points
        elif points_difference < 0:
            # Delete old data points so we can rewrite them.
            for _ in range(abs(points_difference)):
                data_series.pop()
            
        # Add the new time points to the series
        data_series.extend(new_data_points)
        
        # Notify the variable that new data has arrived
        self.variable.new_data_arrived(new_data_points[-1])
        
    def get_graph_series(self, start_timestamp, end_timestamp, sampling_rate):
        '''Return a list of (x,y) data, x being the timestamp and y being the corresponding datapoints. 
        '''
        #TODO: support returning more than one graph series (for more than one data block)
        # currently we just return the last relevant data block
        
        # Use the relevant data block
        data_block = self.get_data_block(end_timestamp)
        if (not data_block or
            len(data_block.timestamp_series) == 0):
            return []
        data_series = data_block.data_series
        timestamp_series = data_block.timestamp_series
        
        # Align requested timestamps with the existing data
        start_timestamp = timestamp_series[0] + int((start_timestamp - timestamp_series[0])*sampling_rate)/sampling_rate
        end_timestamp = timestamp_series[0] + int((end_timestamp - timestamp_series[0])*sampling_rate)/sampling_rate

        # Check if we don't have the beginning of the requested data.
        start_timestamp_difference = start_timestamp - timestamp_series[0]
        if start_timestamp_difference < 0:
            first_timestamp_index = None
        else:
            first_timestamp_index = int(start_timestamp_difference * self.sampling_rate)
        
        # Check if we don't have the end of the requested data.
        end_timestamp_difference = end_timestamp - timestamp_series[-1]
        if end_timestamp_difference > 0:
            last_timestamp_index = None
        else:
            last_timestamp_index = int((end_timestamp - timestamp_series[0]) * self.sampling_rate) + 1

        # Down-sample if necessary.
        sampling_rates_ratio = max(int(self.sampling_rate/sampling_rate), 1)
        graph_series = zip(timestamp_series[first_timestamp_index:last_timestamp_index:sampling_rates_ratio],
                           data_series[first_timestamp_index:last_timestamp_index:sampling_rates_ratio])
        returned_graph_series = [item for item in graph_series if item[1] != None]
        return returned_graph_series
        
class DataChannelOut(DataChannel):
    '''Data flows from instrumentino to a controller
    '''
    
    max_output_value = NumericProperty()
    '''The maximal native value that can be written for this channel.
    It can be only a positive integer.
    '''
    
    def write(self, **kwargs):
        '''Write data to the channel
        '''
        # TODO: implement.


class DataChannelInOut(DataChannelIn, DataChannelOut):
    '''Data flows both ways between a controller and instrumentino
    '''
    pass


class DataChannelI2C(DataChannel):
    '''A channel for data which is accessed through an I2C bus.
    '''

    i2c_address = NumericProperty() # TODO: make this a bounded numeric property of possible addresses on an I2C bus
    '''The I2C address of data resource.
    '''
    
    def __init__(self, **kwargs):
        if not set(['i2c_address']) <= set(kwargs): raise MissingKwargsError()
        
        super(DataChannelI2C, self).__init__(**kwargs)
