from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino,\
    SysVarAnalogArduinoUnipolar
__author__ = 'yoelk'

class ParkerPressureController(SysCompArduino):
    def __init__(self, name, rangeP, pinInP, pinOutP=None, highFreqPWM=False, units='psi', I2cDac=None):
        SysCompArduino.__init__(self, name,
                                (SysVarAnalogArduinoUnipolar('P', rangeP, pinInP, pinOutP, name, 'Pressure', units, highFreqPWM=highFreqPWM, I2cDac=I2cDac),),
                                'monitor/change pressure')