from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar, SysVarPidRelayArduino
__author__ = 'yoelk'

from instrumentino import cfg

class PidControlledThermostat(SysCompArduino):
    def __init__(self, name, rangeT, pinInT, pinOutRelay, sensorVoltsMin, sensorVoltsMax, pidVar, windowSizeMs, kp, ki, kd):
        self.varEnable = SysVarDigitalArduino('enable', None, name, PreSetFunc=self.PreEditEnable)
        self.pidRelayVar = SysVarPidRelayArduino('T', rangeT, pidVar, windowSizeMs, kp, ki, kd, pinInT, pinOutRelay, name, 'Temperature',
                                                 'C', pinInVoltsMin=sensorVoltsMin, pinInVoltsMax=sensorVoltsMax)
        SysCompArduino.__init__(self, name,
                                (self.pidRelayVar, self.varEnable), 
                                'control a heating element through a relay to keep the temperature set')
        
    def FirstTimeOnline(self):
        super(PidControlledThermostat, self).FirstTimeOnline()
        
    def PreEditEnable(self, value):
        self.pidRelayVar.Enable(value=='on')