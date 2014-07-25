from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

class PewatronPressureSensor(SysCompArduino):
    def __init__(self, name, rangeP, pinInP):
        SysCompArduino.__init__(self, name,
                                (SysVarAnalogArduinoUnipolar('P', rangeP, pinInP, None, name, 'Pressure', 'mbar', pinInVoltsMax=4.5, pinInVoltsMin=0.5),),
                                'monitor pressure')