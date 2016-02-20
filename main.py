from __future__ import division
from instrumentino import InstrumentinoApp
from instrumentino.components import Component
from instrumentino.variables import AnalogVariablePercentage,\
    DigitalVariableOnOff
from instrumentino.controllers.arduino import Arduino, ArduinoChannelIn_AnalolgInPin,\
    ArduinoChannelInOut_DigitalPin, ArduinoChannelOut_DigitalPin
from instrumentino.screens.automation import Action
from instrumentino.controllers import Controller
import inspect

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
    
    # Add channels
 
    # Add components
    app.add_component(AnalogInVariables(ch_class=ArduinoChannelIn_AnalolgInPin, controller=arduino, channels_numbers=[0,1], sampling_rate=10))
    app.add_component(DigitalInOutVariables(ch_class=ArduinoChannelInOut_DigitalPin, controller=arduino, channels_numbers=[2,3], sampling_rate=10))

    # Define actions
    class Action1(Action):
        '''An example action
        '''
         
        var1 = AnalogVariablePercentage()
        '''An example variable
        '''
         
        def on_start(self):
            '''Describe here what the action does
            '''
            print self.var1.value
    
    # Add actions
    app.add_action(Action1)

    # Run application
    app.run()