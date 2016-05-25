from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

from instrumentino import cfg

class EmcoHvSypplyCA_Series_Input12V(SysCompArduino):
    def __init__(self, name, rangeV, pinInV, pinOutV=None, ctlV_I2cDac=None):
        if ctlV_I2cDac:
            voltageVar = SysVarAnalogArduinoUnipolar('V', rangeV, pinInV, None, name, 'Voltage', 'V', I2cDac=ctlV_I2cDac)
        else:
            voltageVar = SysVarAnalogArduinoUnipolar('V', rangeV, pinInV, pinOutV, name, 'Voltage', 'V')
        
        SysCompArduino.__init__(self, name,
                                (voltageVar,),
                                'monitor/change High Voltage variables')
        
        
class EmcoCA05P(EmcoHvSypplyCA_Series_Input12V):
    def __init__(self, name, pinInV, pinOutV=None, ctlV_I2cDac=None):
        EmcoHvSypplyCA_Series_Input12V.__init__(self, name, [0, 500], pinInV, pinOutV=pinOutV, ctlV_I2cDac=ctlV_I2cDac)