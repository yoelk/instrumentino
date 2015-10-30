from __future__ import division
from instrumentino.components import Component
from instrumentino.variables import AnalogVariable, DigitalVariable
__author__ = 'yoelk'

class MassFlowController(Component):
    '''A mass flow controller.
    '''
    
    def __init__(self, **kwargs):
        # Add flow variable
        flow_ch_in = kwargs.get('flow_ch_in', None)
        flow_ch_out = kwargs.get('flow_ch_in', None)
        self.add_variable(AnalogVariable(name='Flow', range=[0,100], units='%', 
                                         channel_in=flow_ch_in, channel_out=flow_ch_out))
        # Add enable variable
        enable_ch_in = kwargs.get('enable_ch_in', None)
        enable_ch_out = kwargs.get('enable_ch_in', None)
        self.add_variable(DigitalVariable(name='Enable', options=['on', 'off'],
                                          channel_in=enable_ch_in, channel_out=enable_ch_out))
        
        super(MassFlowController, self).__init__(**kwargs)        