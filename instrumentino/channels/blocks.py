from __future__ import division
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, DictProperty, ListProperty, BooleanProperty
import time

class UninterruptedBlock(EventDispatcher):
    '''A block of uninterrupted information.
    '''
    
    t_zero = NumericProperty(0)
    '''The timestamp at which this block started recording.
    If not set (=0), the block is considered still inactive
    '''
    
    t_end = NumericProperty(0)
    '''The timestamp at which this block stopped recording
    '''
    
class TimeBlock(UninterruptedBlock):
    '''A block of uninterrupted timestamps, for which data was acquired.
    These blocks are saved in the controller, as timestamp information
    may be relevant to several channels (all having the same sampling rate).
    '''
    
    timestamp_series_dict = DictProperty()
    '''A set of timestamp series for the different sampling rates (rates are the dictionary keys).
    The timestamps are "x axis" values which correspond to the input channels'
    "y axis" data (saved in their respective data_series).
    A separate timestamp series is saved for each requested sampling rate. 
    '''
    
    def copy(self, timestamp):
        new_block = TimeBlock(t_zero=timestamp)
        
        # Copy the timestamp series structure (all the sampling rate keys)
        for key in self.timestamp_series_dict.keys():
            new_block.timestamp_series_dict[key] = []
            
        return new_block
    
class DataBlock(UninterruptedBlock):
    '''A block of uninterrupted acquired data.
    These blocks are saved in the channel, and the timestamps that correspond
    to these data are saved in the controller.
    '''
    
    data_series = ListProperty()
    '''The channel's data series, which is updated by the controller.
    This list entries correspond to the timestamp_series list.
    '''
    
    timestamp_series = []
    '''The timestamp series that correspond to the data series.
    This is just a reference to the timestamp series saved in the controller.
    
    We can't use a kivy ListProperty here because timestamp_series should point 
    to the list in the controller, and if we initialize it here with a ListProperty, it doesn't point there anymore.  
    '''
    
    def __init__(self, **kwargs):
        if not set(['timestamp_series']) <= set(kwargs): raise TypeError('missing mandatory kwargs')
        
        # Get the timestamp_series
        self.timestamp_series = kwargs['timestamp_series']
        
        super(DataBlock, self).__init__(**kwargs)