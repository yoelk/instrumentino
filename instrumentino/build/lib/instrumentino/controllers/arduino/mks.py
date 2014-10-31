from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino,\
    SysVarAnalogArduinoUnipolar, SysVarDigitalArduino
__author__ = 'yoelk'

from instrumentino import cfg

class MKSMassFlowController(SysCompArduino):
    def __init__(self, name, pinInPercent, pinOutPercent, pinOutClose=None):
        SysCompArduino.__init__(self, name, 
                                (SysVarAnalogArduinoUnipolar('Flow', [0,100], pinInPercent, pinOutPercent, name, 'Flow percentage', '%', self.PreEditPercent, highFreqPWM=True),),
                                'monitor/change gas flow')
        
        self.pinOutClose = pinOutClose
        if self.pinOutClose != None:
            self.varClose = SysVarDigitalArduino('close', pinOutClose, name)
        
    def FirstTimeOnline(self):
        if self.pinOutClose != None:
            self.GetController().PinModeOut(self.varClose.pin)
        return super(MKSMassFlowController, self).FirstTimeOnline()
        
    def PreEditPercent(self, value):
        if self.pinOutClose != None:
            if value == 0:
                self.varClose.Set('off')
            else:
                self.varClose.Set('on')