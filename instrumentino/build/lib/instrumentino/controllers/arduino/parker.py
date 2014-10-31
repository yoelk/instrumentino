from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

class ParkerPressureController(SysCompArduino):
    def __init__(self, name, rangeP, pinInP, pinOutP, highFreqPWM=False):
        SysCompArduino.__init__(self, name,
                                (SysVarAnalogArduinoUnipolar('P', rangeP, pinInP, pinOutP, name, 'Pressure', 'psi', highFreqPWM=highFreqPWM),),
                                'monitor/change pressure')