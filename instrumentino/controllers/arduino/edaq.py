from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino
__author__ = 'yoelk'

from instrumentino import cfg

class EdaqEcorder(SysCompArduino):
    def __init__(self, name, pin):
        SysCompArduino.__init__(self, name, (SysVarDigitalArduino('trigger', pin, name, PreSetFunc=self.Pause),), 'trigger the e-corder')

    def Pause(self, value):
        if value == 'off':
            cfg.Sleep(1)
        
    def TriggerPulse(self):
        self.vars['trigger'].Set('on')
        cfg.Sleep(0.01)
        self.vars['trigger'].Set('off')