from kivy.properties import ObjectProperty, ListProperty, StringProperty, BoundedNumericProperty, NumericProperty, \
    AliasProperty
import time
import random
from kivy.event import EventDispatcher
from math import ceil
import numpy as np
import pandas as pd
from datetime import timedelta
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

    fitting_datapoint_variable_name = StringProperty()
    '''The name of a fitting variable for a single datapoint. For example, if the channel is transferring 15 bits for a
     datapoint, it needs 2 bytes, which fit inside an 'Int16' variable. If each datapoint has 17 bits, then an 'Int32'
     will be used.
    '''

    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['controller', 'data_bits', 'type_str', 'number'], kwargs)
        super(DataChannel, self).__init__(**kwargs)

        self.data_bytes = ceil(self.data_bits / 8)
        self.fitting_datapoint_variable_name = {0 < self.data_bytes <= 1: 'Int8',
                                                1 < self.data_bytes <= 2: 'Int16',
                                                2 < self.data_bytes <= 4: 'Int32',
                                                4 < self.data_bytes <= 8: 'Int64',
                                                }[True]

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

    data_frame = ObjectProperty()
    '''A list that contains all of the data that was recorded for this
    channel. A data frame starts whenever a controller is connected
    (having an online communication_port). Each data frame has a DateTimeIndex
    named 'time' and a single 'data' column 
    '''

    sampling_rate = BoundedNumericProperty(ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
    '''The channel's sampling rate (in Hz).
    '''

    sampling_period = BoundedNumericProperty(1 / ControlinoProtocol.DEFAULT_DATA_PACKET_RATE, min=0)
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
        self.sampling_period = 1 / self.sampling_rate

        # Init the data frame structure
        self.data_frame = pd.DataFrame(columns=['time', 'percent'])
        self.data_frame = self.data_frame.set_index('time')

    def do_first_when_online(self):
        '''Register this channel at the controller
        '''
        self.controller.controlino_protocol.register_input_channel(self)

    def translate_incoming_data(self, data):
        '''Incoming data is received as whole numbers (not floating point) that result in native read functions in the
        controller. For the sake of uniformity, all values should be translated to a [0,100] scale (percentage).
        '''
        return [x / self.max_input_value * 100 for x in data]

    def update_data_series(self, packet_timedelta, raw_data_points):
        '''Update the data series with new data points. 
        '''

        # Create the time series based on the packet's timestamp
        packet_datetime = self.controller.t_zero + packet_timedelta
        time_series = [packet_datetime + timedelta(seconds=self.sampling_period) * i for i in
                       range(len(raw_data_points))]

        # Translate the incoming data to a percentage scale (0-100)
        # The translated data can be presented in a graph with a common Y axis (percentage) 
        percent_data_points = self.translate_incoming_data(raw_data_points)

        # Add the timed data to the current data frame
        for time, percent in zip(time_series, percent_data_points):
            self.data_frame.loc[time] = percent

        # Notify the variable that new data has arrived
        if self.variable:
            self.variable.new_data_arrived(self.data_frame['percent'].iloc[-1])

    def get_dataframe_subset(self, start_timestamp, end_timestamp, sampling_rate):
        '''Return a list of (x,y) data, x being the timestamp and y being the corresponding datapoints. 
        '''
        # Convert sampling rate (in Hz) to sampling period (in milliseconds)
        sampling_period_ms = (1 / sampling_rate) * 1000
        return self.data_frame.query('start_timestamp <= time <= end_timestamp').resample(
            '{}L'.format(sampling_period_ms))


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
        self.controller.controlino_protocol.write_to_channel(self,
                                                             [int(percentage_value / 100 * self.max_output_value)])


class DataChannelInOut(DataChannelIn, DataChannelOut):
    '''Data flows both ways between a controller and instrumentino
    '''
    pass


class DataChannelI2C(DataChannel):
    '''A channel for data which is accessed through an I2C bus.
    '''

    i2c_address = NumericProperty()  # TODO: make this a bounded numeric property of possible addresses on an I2C bus
    '''The I2C address of data resource.
    '''

    def __init__(self, **kwargs):
        check_for_necessary_attributes(self, ['i2c_address'], kwargs)
        super(DataChannelI2C, self).__init__(**kwargs)
