from __future__ import division
from instrumentino import InstrumentinoApp
from instrumentino.components import Component
from instrumentino.variables import AnalogVariablePercentage,\
    DigitalVariableOnOff
from instrumentino.controllers.arduino import Arduino, ArduinoChannelIn_AnalolgInPin,\
    ArduinoChannelInOut_DigitalPin, ArduinoChannelOut_DigitalPin

class AnalogInVariables(Component):
    '''An array of analog input variables
    '''
    
    def __init__(self, **kwargs):
        ch_class = kwargs.get('ch_class', None)
        controller = kwargs.get('controller', None)
        channels_numbers = kwargs.get('channels_numbers', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        for i in channels_numbers:
            ch_in = ch_class(controller=controller, number=i, sampling_rate=sampling_rate)
            self.add_variable(AnalogVariablePercentage(name='Analog '+str(i), channel_in=ch_in))
        
        super(AnalogInVariables, self).__init__(**kwargs)


class DigitalInOutVariables(Component):
    '''An array of digital input/output variables
    '''
    
    def __init__(self, **kwargs):
        ch_class = kwargs.get('ch_class', None)
        controller = kwargs.get('controller', None)
        channels_numbers = kwargs.get('channels_numbers', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        for i in channels_numbers:
            ch = ch_class(controller=controller, number=i, sampling_rate=sampling_rate)
            self.add_variable(DigitalVariableOnOff(name='Digital '+str(i), channel_in=ch, channel_out=ch))

        super(DigitalInOutVariables, self).__init__(**kwargs)


if __name__ == '__main__':

    app = InstrumentinoApp()
    
    # Add controllers
    arduino = Arduino()
    app.add_controller(arduino)
    
    # ProfileLoader Testing
#    app.remove_controller(name=controller.name)
#    app.remove_controllers()
    
    # Add channels
 
    # Add components
    app.add_component(AnalogInVariables(ch_class=ArduinoChannelIn_AnalolgInPin, controller=arduino, channels_numbers=[0,1], sampling_rate=10))
    app.add_component(DigitalInOutVariables(ch_class=ArduinoChannelInOut_DigitalPin, controller=arduino, channels_numbers=[2,3], sampling_rate=10))
    
    
    
    # ProfileLoader Testing: 
#    app.remove_component(name='MFC1')
#    app.remove_components()

#     app.add_component(MassFlowController(name='MFC1', 
#                                          flow_ch_in=flow1_channel_in_out, flow_ch_out=flow1_channel_in_out,
#                                          enable_ch_in=enable1_channel_in_out, enable_ch_out=enable1_channel_in_out,))
#     app.add_component(MassFlowController(name='MFC2', 
#                                          flow_ch_in=flow2_channel_in_out, flow_ch_out=flow2_channel_in_out,
#                                          enable_ch_in=enable2_channel_in_out, enable_ch_out=enable2_channel_in_out,))
#     app.add_component(MassFlowController(name='MFC3', 
#                                          flow_ch_in=flow3_channel_in_out, flow_ch_out=flow3_channel_in_out,
#                                          enable_ch_in=enable3_channel_in_out, enable_ch_out=enable3_channel_in_out,))

    # Add actions
    app.add_action(name='action1', function=lambda:1)
    # ProfileLoader Testing: 
#    app.remove_action(name='action1')
#    app.remove_actions()

    app.run()
