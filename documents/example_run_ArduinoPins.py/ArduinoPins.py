from __future__ import division
from instrumentino import Instrument
from instrumentino import cfg
from instrumentino.action import SysAction, SysActionParamTime, SysActionParamFloat, SysActionParamInt
from instrumentino.controllers.arduino import SysVarDigitalArduino, SysVarAnalogArduinoUnipolar
from instrumentino.controllers.arduino.pins import DigitalPins, AnalogPins
 
'''
*** System constants
'''
# Arduino pins
pinAnalInA = 1
pinPwmOutA = 9

pinAnalInB = 2
pinPwmOutB = 10

'''
*** System components
'''
analPins = AnalogPins('analog pins', (SysVarAnalogArduinoUnipolar('A', (0,5), pinAnalInA, pinPwmOutA, 'analPins', units='volts'),
                                      SysVarAnalogArduinoUnipolar('B', (0,5), pinAnalInB, pinPwmOutB, 'analPins', units='volts')))
 
'''
*** System actions
'''
class SysActionSetPins(SysAction):
    def __init__(self):
        self.seconds = SysActionParamTime()
        self.pinA = SysActionParamFloat(analPins.vars['A'])
        self.pinB = SysActionParamFloat(analPins.vars['B'])
        SysAction.__init__(self, 'Set pins', (self.seconds, self.pinA, self.pinB))
 
    def Command(self):
        # Set pins
        analPins.vars['A'].Set(self.pinA.Get())
        analPins.vars['B'].Set(self.pinB.Get())
         
        # Wait some time
        cfg.Sleep(self.seconds.Get())

        # Zero pins
        analPins.vars['A'].Set(0)
        analPins.vars['B'].Set(0)


'''
*** System
'''
class System(Instrument):
    def __init__(self):
        comps = (analPins,)
        actions = (SysActionSetPins(),)
        name = 'Arduino simple example'
        description = 'A simple example using only an Arduino. Analog pins 1,2 should be connected to PWM pins 9,10 respectively, through a low-pass filter.'
        version = '1.0'
         
        Instrument.__init__(self, comps, actions, version, name, description)
 
'''
*** Run program
'''        
if __name__ == '__main__':
    # run the program
    System()