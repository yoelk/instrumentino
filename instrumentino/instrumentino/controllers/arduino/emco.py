from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

from instrumentino import cfg

class EmcoHvSypplyCA_Series_Input12V(SysCompArduino):
    def __init__(self, name, rangeV, pinInV, pinOutV):
        SysCompArduino.__init__(self, name,
                                (SysVarAnalogArduinoUnipolar('V', rangeV, pinInV, pinOutV, name, 'Voltage', 'V'),),
                                'monitor/change High Voltage variables')
        
        
class EmcoCA05P(EmcoHvSypplyCA_Series_Input12V):
    def __init__(self, name, pinInV, pinOutV):
        EmcoHvSypplyCA_Series_Input12V.__init__(self, name, [0, 500], pinInV, pinOutV)