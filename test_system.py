#################################
# make a simple example to demonstrate some of the GUI capabilities
# Use an Arduino to track the values of two analog pins.
# The first has a unipolar positive range (0 to 5 V).
# The second has a unipolar negative range (-5 to 0 V).
# The third has a bipolar range (-5 to 5 V) while a digital pin sets the polarity.
from instrumentino.controllers.arduino import SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar, SysVarAnalogArduinoBipolarWithExternalPolarity
from instrumentino.controllers.arduino.pins import AnalogPins, DigitalPins
from instrumentino.action import SysAction, SysActionParamInt,\
    SysActionParamTime
from instrumentino import Instrument
if __name__ == '__main__':
    '''
    *** System constants
    '''
    # pin assignments
    pinAnal_unipolarPositive = 0
    pinAnal_unipolarNegative = 1
    pinAnal_bipolar = 2
    pinDigi_polarity = 2
            
    '''
    *** System components
    '''
    polarityVariable = SysVarDigitalArduino('polarity', pinDigi_polarity)
    
    def SetPolarityPositiveFunc():
        pass
    
    def GetPolarityPositiveFunc():
        return polarityVariable.Get() == 'on'
    
    analPins = AnalogPins('analog pins',
                          (SysVarAnalogArduinoUnipolar('unipolar +',[0,5],pinAnal_unipolarPositive,None, units='V'),
                           SysVarAnalogArduinoUnipolar('unipolar -',[-5,0],pinAnal_unipolarNegative,None, units='V'),
                           SysVarAnalogArduinoBipolarWithExternalPolarity('bipolar',[-5,5],pinAnal_bipolar,None, SetPolarityPositiveFunc, GetPolarityPositiveFunc, units='V'),))
                                                                
    digiPins = DigitalPins('digital pins',
                           (polarityVariable,))

    '''
    *** System actions
    '''
    class SysActionSetPolarity(SysAction):
        def __init__(self):
            self.polarity = SysActionParamInt('Polarity', [-1,1])
            SysAction.__init__(self, 'Set polarity', (self.polarity,))
    
        def Command(self):
            polarityVariable.Set('on' if self.polarity.Get()>0 else 'off')
            
            
    class SysActionSleep(SysAction):
        def __init__(self):
            self.seconds = SysActionParamTime(name='Time')
            SysAction.__init__(self, 'Sleep', (self.seconds,))
    
        def Command(self):
            cfg.Sleep(self.seconds.Get())
            
    '''
    *** System
    '''
    class System(Instrument):
        def __init__(self):
            comps = (analPins, digiPins)
            actions = (SysActionSetPolarity(),
                       SysActionSleep())
            name = 'Basic Arduino example'
            description = '''Basic Arduino example.\n 
                             Use an Arduino to track the values of two analog pins.\n
                             The first has a unipolar positive range (0 to 5 V).\n
                             The second has a unipolar negative range (-5 to 0 V).\n
                             The third has a bipolar range (-5 to 5 V) while a digital pin sets the polarity.'''
            version = '1.0'
            
            Instrument.__init__(self, comps, actions, version, name, description)
            
    '''
    *** Run program
    '''
    System()