from __future__ import division
from instrumentino import InstrumentinoApp
from instrumentino.components import Component
from instrumentino.variables import AnalogVariable
from instrumentino.controllers.arduino import Arduino, ArduinoChannelIn_AnalolgInPin

class DummyComp(Component):
    '''A dummy component
    '''
    
    def __init__(self, **kwargs):
        # Add flow variable
        ch_in = kwargs.get('ch_in', None)
        self.add_variable(AnalogVariable(name='Analog', range=[0,100], units='%', channel_in=ch_in))
        
        super(DummyComp, self).__init__(**kwargs)

if __name__ == '__main__':

    app = InstrumentinoApp()
    
    ##########
    # Add controllers
    arduino = Arduino()
    app.add_controller(arduino)
    
    # ProfileLoader Testing
#    app.remove_controller(name=controller.name)
#    app.remove_controllers()
    
    ##########
    # Add channels
    flow1_channel = ArduinoChannelIn_AnalolgInPin(controller=arduino, number=0, sampling_rate=100)
 
    ##########
    # Add components
    app.add_component(DummyComp(name='MFC1', ch_in=flow1_channel))
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

    ##########
    # Add actions
    app.add_action(name='action1', function=lambda:1)
    # ProfileLoader Testing: 
#    app.remove_action(name='action1')
#    app.remove_actions()

    app.run()
