from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

from instrumentino import cfg

class AnalogPinThermometer(SysCompArduino):
    def __init__(self, name, rangeT, pinInT, pinInVoltsMax, pinInVoltsMin):
        SysCompArduino.__init__(self, name,
                                (SysVarAnalogArduinoUnipolar('T', rangeT, pinInT, None, name, 'Temperature', 'C', pinInVoltsMax=pinInVoltsMax, pinInVoltsMin=pinInVoltsMin),),
                                'measure the temperature')


class AnalogPinThermometer_AD22103(AnalogPinThermometer):
    def __init__(self, name, pinInT):
        AnalogPinThermometer.__init__(self, name, [0,100], pinInT, pinInVoltsMax=3.05, pinInVoltsMin=0.25)