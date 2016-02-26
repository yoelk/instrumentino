from __future__ import division
from instrumentino import InstrumentinoApp
from instrumentino.components import AnalogInVariables, DigitalInOutVariables
from instrumentino.variables import AnalogVariablePercentage
from instrumentino.controllers.arduino import Arduino, ArduinoChannelIn_AnalolgInPin,\
    ArduinoChannelInOut_DigitalPin
from instrumentino.screens.automation import Action

# Define controllers
arduino = Arduino()

# Define channels and components
anal_vars = AnalogInVariables(ch_class=ArduinoChannelIn_AnalolgInPin, controller=arduino, channels_numbers=[0,1], sampling_rate=10)
digi_vars = DigitalInOutVariables(ch_class=ArduinoChannelInOut_DigitalPin, controller=arduino, channels_numbers=[2,3], sampling_rate=10)

# Define actions
class Action1(Action):
    '''An example action
    '''

    name = 'Example'
    
    var1 = AnalogVariablePercentage()
    '''An example variable
    '''

    def on_start(self):
        '''Describe here what the action does
        '''
        print self.var1.value

# Run application
InstrumentinoApp().run()