from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

class PewatronPressureSensor(SysCompArduino):
    def __init__(self, name, rangeP, units, pinInP, pinInVoltsMax, pinInVoltsMin):
        SysCompArduino.__init__(self, name,
                                (SysVarAnalogArduinoUnipolar(name='P',
                                                             range=rangeP,
                                                             pinAnalIn=pinInP,
                                                             pinPwmOut=None,
                                                             compName=name,
                                                             helpLine='Pressure',
                                                             units=units,
                                                             pinInVoltsMax=pinInVoltsMax,
                                                             pinInVoltsMin=pinInVoltsMin),),
                                'monitor pressure')