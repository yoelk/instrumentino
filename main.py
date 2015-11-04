from __future__ import division
from instrumentino import InstrumentinoApp
from instrumentino.components import Component
from instrumentino.variables import AnalogVariablePercentage,\
    DigitalVariableOnOff
from instrumentino.controllers.arduino import Arduino, ArduinoChannelIn_AnalolgInPin,\
    ArduinoChannelInOut_DigitalPin

class ArduinoAnalogInPins(Component):
    '''An array of Arduino analog input pins
    '''
    
    def __init__(self, **kwargs):
        controller = kwargs.get('controller', None)
        channels_num = kwargs.get('channels_num', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        for i in range(channels_num):
            ch_in = ArduinoChannelIn_AnalolgInPin(controller=controller, number=i, sampling_rate=sampling_rate)
            self.add_variable(AnalogVariablePercentage(name='Analog'+str(i), channel_in=ch_in))
        
        super(ArduinoAnalogInPins, self).__init__(**kwargs)


class ArduinoDigitalInOutPins(Component):
    '''An array of Arduino digital input/output pins
    '''
    
    def __init__(self, **kwargs):
        controller = kwargs.get('controller', None)
        channels_num = kwargs.get('channels_num', None)
        sampling_rate = kwargs.get('sampling_rate', None)
        
        for i in range(channels_num):
            ch_in = ArduinoChannelInOut_DigitalPin(controller=controller, number=i, sampling_rate=sampling_rate)
            self.add_variable(DigitalVariableOnOff(name='Digital'+str(i), channel_in=ch_in))
        
        super(ArduinoDigitalInOutPins, self).__init__(**kwargs)


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
    app.add_component(ArduinoDigitalInOutPins(controller=arduino, channels_num=2, sampling_rate=10))
    app.add_component(ArduinoAnalogInPins(controller=arduino, channels_num=2, sampling_rate=10))
    
    
    
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
