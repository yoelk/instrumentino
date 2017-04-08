from __future__ import division
from kivy.properties import ObjectProperty, ListProperty, StringProperty, BoundedNumericProperty, NumericProperty, AliasProperty
import time
import random
from kivy.event import EventDispatcher
from __builtin__ import ValueError
from math import ceil
from construct.macros import UBInt8, UBInt16, UBInt32, UBInt64, GreedyRange
import numpy as np
import pandas as pd
from datetime import timedelta
from instrumentino.libs.abs_ratio import abs_ratio
from instrumentino.controlino_protocol import ControlinoProtocol
from kivy.app import App
from instrumentino.cfg import *

def get_fitting_data_point_variable(bytes_num):
        '''Translate between the number of required bytes per data point and an appropriately sized variable.
        '''
        return {0<bytes_num<=1: UBInt8(''),
                1<bytes_num<=2: UBInt16(''),
                2<bytes_num<=4: UBInt32(''),
                4<bytes_num<=8: UBInt64(''),
                }[True]
                
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
        check_for_necessary_attributes(self, ['controller', 'data_bits', 'type_str', 'number'], kwargs)
        super(DataChannel, self).__init__(**kwargs)

        self.data_bytes = ceil(self.data_bits/8)
        
        # Add the channel to the controller
        self.controller.add_channel(self)

    def get_identifier(self):
        '''Return a string that identifies this data channel in the controller.
        It is made of the channel's type and its number (e.g. 'D1')
        '''
        return self.type_str + str(self.number)

    def do_first_when_online(self):
        '''Initialization code that has to be done when communication was set up with the controller.
        To be implemented by sub-classes.
        '''
        pass
        

class DataChannelIn(DataChannel):
    '''Data flows from a controller to instrumentino
    '''

    data_frames = ListProperty()
    '''A list that contains all of the data that was recorded for this
    channel. A data frame starts whenever a controller is connected
    (having an online communication_port). Each data frame has a DateTimeIndex
    named 'time' and a single 'data' column 
    '''

    sampling_rate = BoundedNumericProperty(ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
    '''The channel's sampling rate (in Hz).
    '''
    
    sampling_period = BoundedNumericProperty(1/ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
    '''The channel's sampling period (in seconds).
    '''
    
    max_input_value = NumericProperty()
    '''The maximal native value that can be read for this channel.
    It can be only a positive integer.
    '''
    
    def __init__(self, **kwargs):
        super(DataChannelIn, self).__init__(**kwargs)
        check_for_necessary_attributes(self, ['max_input_value'], kwargs)
        
        # Check that the sampling rate is valid
        if not abs_ratio(self.sampling_rate, self.controller.data_packet_rate).is_integer():
            raise ValueError("Sampling rate doesn't fit controller's data packet rate")
        self.sampling_period = 1/self.sampling_rate
        
        # Init the first data_frame structure
        df = pd.DataFrame(columns=['time', 'percent'])
        df = df.set_index('time')
        self.data_frames.append(df)
        
        # Set the appropriate serialized format class, in order to handle incoming data packets
        self.data_points_serialized_format = GreedyRange(get_fitting_data_point_variable(self.data_bytes))
                
    def do_first_when_online(self):
        '''Register this channel at the controller
        '''
        self.controller.controlino_protocol.register_input_channel(self)
    
    def translate_incoming_data(self, data):
        '''Incoming data is received as whole numbers (not floating point) that result in native read functions in the controller.
        For the sake of uniformity, all values should be translated to a [0,100] scale (percentage).
        '''
        return [x / self.max_input_value * 100 for x in data]

    def update_data_series(self, packet_timedelta, raw_data_points):
        '''Update the data series with new data points. 
        '''
        
        # Create the time series based on the packet's timestamp
        packet_datetime = self.controller.t_zero + packet_timedelta
        time_series = [packet_datetime + timedelta(seconds=self.sampling_period) * i for i in range(len(raw_data_points))]
        
        # Translate the incoming data to a percentage scale (0-100)
        # The translated data can be presented in a graph with a common Y axis (percentage) 
        percent_data_points = self.translate_incoming_data(raw_data_points)
        
        # Add the timed data to the current data frame
        for time, percent in zip(time_series, percent_data_points):
            self.data_frames[-1].loc[time] = percent
        
        # Notify the variable that new data has arrived
        if self.variable:
            self.variable.new_data_arrived(self.data_frames[-1]['percent'].iloc[-1])
        
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
    
    def write(self, percentage_value):
        '''Write data to the channel
        '''
        self.controller.controlino_protocol.write_to_channel(self, [int(percentage_value / 100 * self.max_output_value)])

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
        check_for_necessary_attributes(self, ['i2c_address'], kwargs)
        super(DataChannelI2C, self).__init__(**kwargs)
