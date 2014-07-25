from __future__ import division
from instrumentino.controllers.labsmith_eib import SysCompLabSmith,\
    SysVarDigitalLabSmith_SyringeSpeed, SysVarDigitalLabSmith_SyringePower,\
    SysVarDigitalLabSmith_SyringeMaxVolume, SysVarDigitalLabSmith_SyringePlunger
__author__ = 'yoelk'

from instrumentino import cfg
import wx
import time
from instrumentino.comp import SysVarDigital, SysComp


"""
system components
"""

class LabSmithValves4VM01(SysCompLabSmith):
    def __init__(self, name, digiVars):
        SysCompLabSmith.__init__(self, name, digiVars, 'open/close valves')
        
        for var in digiVars:
            var.SetController(self)
            
        self.valvesDriver = None
        
    def setValve(self, port, state):
        if port == 1:
            self.GetController().SetValves(valve1=state)
        if port == 2:
            self.GetController().SetValves(valve2=state)
        if port == 3:
            self.GetController().SetValves(valve3=state)
        if port == 4:
            self.GetController().SetValves(valve4=state)
            
    def getValve(self, port):
        valves = self.GetController().GetValves()
        return valves[port-1]


class LabSmithSPS01SyringePump(SysCompLabSmith):
    '''
    A LabSmith SPS01 syringe pump
    '''
    syringeVolumeMicroLitToDiameterMiliMeter = {100: 3.256, # -80 (100 ul): .1282" (3.256 mm)
                                                50: 2.304,  # -40 (50 ul): .0907" (2.304 mm)
                                                20: 1.458,  # -20 (20 ul): .0574" (1.458 mm)
                                                10: 1.031,  # -08 (10 ul): .0406" (1.031 mm) 
                                                5: 0.729}   # -04 (5 ul): .0287" (0.729 mm) 
    
    def __init__(self, name, volumeMicroLit, helpline='', defaultSpeedPercent = 50, defaultPowerPercent = 75):
        self.defaultSpeedPercent = defaultSpeedPercent
        self.defaultPowerPercent = defaultPowerPercent
        self.diameterMiliMeter = self.syringeVolumeMicroLitToDiameterMiliMeter[volumeMicroLit]
        
        self.volume = SysVarDigitalLabSmith_SyringeMaxVolume(name, self)
        self.plunger = SysVarDigitalLabSmith_SyringePlunger(name, self)
        self.speed = SysVarDigitalLabSmith_SyringeSpeed(name, self)
        self.power = SysVarDigitalLabSmith_SyringePower(name, self)
        SysCompLabSmith.__init__(self, name, (self.volume, self.plunger, self.speed, self.power), 'move syringe pump')
        
    def FirstTimeOnline(self):
        maxVolume = self.GetController().SetSyringeDiameterAndGetMaxVolume(self.diameterMiliMeter)
        self.volume.SetMaxVolume(maxVolume)
        self.plunger.SetMaxVolume(maxVolume)
        self.speed.Set(self.defaultSpeedPercent)
        self.power.Set(self.defaultPowerPercent)
        self.plunger.Set(5)
