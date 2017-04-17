
from instrumentino import InstrumentinoApp
from instrumentino.components import AnalogVariables, DigitalVariables
from instrumentino.variables import AnalogVariablePercentage, \
    AnalogVariableDurationInSeconds
from instrumentino.controllers.arduino import Arduino, ArduinoChannelIn_AnalolgInPin, \
    ArduinoChannelInOut_DigitalPin
from instrumentino.screens.automation import Action

# Define controllers
arduino = Arduino()

# Define channels and components
anal_vars = AnalogVariables(ch_class=ArduinoChannelIn_AnalolgInPin, controller=arduino, channels_numbers=[0, 1],
                            sampling_rate=10)
digi_vars = DigitalVariables(ch_class=ArduinoChannelInOut_DigitalPin, controller=arduino, channels_numbers=[2, 3],
                             sampling_rate=10)


# Define actions
class Action1(Action):
    '''An example action
    '''

    name = 'Example'

    def __init__(self, **kwargs):
        self.var1 = AnalogVariablePercentage(name='var1')
        self.var2 = AnalogVariableDurationInSeconds(name='var2')

        super(Action1, self).__init__(**kwargs)

    def on_start(self):
        '''Describe here what the action does
        '''
        print('vars={}'.format([self.var1.value, self.var2.value]))


# Run application
InstrumentinoApp().run()
