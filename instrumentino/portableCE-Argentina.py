# coding=UTF-8

### !!!!!!!!!!!!!! 
# check how much volume I need to take to inject samples.
# check what is the maximal speed in which I don't move liquids in the capillary
# check which side is for anions and which for cations, and note it on the box
# check that +/- 30kV works

from __future__ import division
from instrumentino import Instrument
from instrumentino import cfg
from instrumentino.action import SysAction, SysActionParamTime, SysActionParamFloat, SysActionParamInt
from instrumentino.controllers.labsmith_eib.labsmith_comps import LabSmithValves4VM01, LabSmithSPS01SyringePump, LabSmithSensors4AM01
from instrumentino.controllers.arduino.parker import ParkerPressureController
from instrumentino.controllers.labsmith_eib import SysVarDigitalLabSmith_AV201Position, SysVarAnalogLabSmith_SensorValue
from instrumentino.controllers.arduino.hvm import HvmSMHV05100, HvmSMHV05100N
from instrumentino.controllers.arduino.edaq import EdaqEcorder
from instrumentino.controllers.arduino import SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar
from instrumentino.controllers.arduino.pins import DigitalPins, AnalogPins
from instrumentino.controllers.arduino.spellman import SpellmanUM30_4_MINUS, SpellmanUM30_4_PLUS
from instrumentino.controllers.arduino.pid_thermostat import PidControlledThermostat
from instrumentino.controllers.arduino.thermometer import AnalogPinThermometer_AD22103
import numpy as np
 
'''
*** System constants
'''
# Arduino pin assignments
pinAnalInSpellmanMinusV = 5
pinAnalInSpellmanMinusI = 4
pinPwmOutSpellmanMinusV = 11
pinPwmOutSpellmanMinusI = 10
pinDigiOutSpellmanMinusEnable = 12 

pinAnalInSpellmanPlusV = 6
pinAnalInSpellmanPlusI = 7
pinPwmOutSpellmanPlusV = 9
pinPwmOutSpellmanPlusI = 3
pinDigiOutSpellmanPlusEnable = 2

pinAnalInParkerP = 0
pinPwmOutParkerP = 5

pinDigiOutEdaqTrigger = 8
 
pinDigiOutHeaterRelay = 7

pinAnalInThermometerEnvironment = 2
pinAnalInThermometerInBox = 3

# 3-way LabSmith Valves can be set to 'A', 'B' and 'closed'
pumpToInterfaces        = 'A'
pressureToInterfaces    = 'B'

anionsBGE       = 'A'
anionsSample    = 'B'

cationsBGE      = 'B'
cationsSample   = 'A'

pressureOn      = 'A'
pressureVenting = 'B'

# Syringe pump with holding coil 
syringeVolume_ul = 100
pumpBottomPercent = 5
pumpTopPercent = 95
syringeUsableVolume_ul = syringeVolume_ul * (pumpTopPercent - pumpBottomPercent) / 100
 
'''
*** System components
'''
pressureController = ParkerPressureController('Pressure', (0,50), pinAnalInParkerP, pinPwmOutParkerP)
spellmanMinus = SpellmanUM30_4_MINUS('HV-', pinDigiOutSpellmanMinusEnable, pinAnalInSpellmanMinusV, pinAnalInSpellmanMinusI, 
                                   pinPwmOutSpellmanMinusV, pinPwmOutSpellmanMinusI, highFreqPWM=True)
spellmanPlus = SpellmanUM30_4_PLUS('HV+', pinDigiOutSpellmanPlusEnable, pinAnalInSpellmanPlusV, pinAnalInSpellmanPlusI, 
                                   pinPwmOutSpellmanPlusV, pinPwmOutSpellmanPlusI, highFreqPWM=True)
ecorder = EdaqEcorder('e-corder', pinDigiOutEdaqTrigger)

pump = LabSmithSPS01SyringePump('pump', syringeVolume_ul)
valves = LabSmithValves4VM01('valves',  (SysVarDigitalLabSmith_AV201Position('pump/pressure', 4), 
                                         SysVarDigitalLabSmith_AV201Position('anions liquids', 1),
                                         SysVarDigitalLabSmith_AV201Position('cations liquids', 3),
                                         SysVarDigitalLabSmith_AV201Position('pressure', 2)))
sensors = LabSmithSensors4AM01('sensors', (SysVarAnalogLabSmith_SensorValue('Pressure', 1, 'psi', [0,115]),))

boxThermostat = PidControlledThermostat('Thermostat', [0,100], pinAnalInThermometerInBox, pinDigiOutHeaterRelay, 0.25, 3.05, 1, 5000, 2, 5, 1)
envThermometer = AnalogPinThermometer_AD22103('Env. Temperature', pinAnalInThermometerEnvironment)

 
'''
*** System actions
'''
def supplyLiquids(volume, speed):
    valves.vars['pressure'].Set('closed')
    
    pump.vars['Speed'].Set(speed)
    valves.vars['pump/pressure'].Set(pumpToInterfaces)
    pump.vars['Plunger'].Set(min(pumpBottomPercent + volume, pumpTopPercent))
    
    pump.vars['Speed'].Set(30)
    valves.vars['pump/pressure'].Set(pressureToInterfaces)
    pump.vars['Plunger'].Set(pumpBottomPercent)


def setPressure(prs):
    for p in np.linspace(0.0, prs, num=10):
        pressureController.vars['P'].Set(p)
        print p


class SetThermostat(SysAction):
    def __init__(self):
        self.temp = SysActionParamFloat(boxThermostat.vars['T'])
        SysAction.__init__(self, 'Thermostat', (self.temp,))

    def Command(self):
        boxThermostat.vars['T'].Set(self.temp.Get())
        boxThermostat.vars['enable'].Set('on')


class ActionBGE2Interfaces(SysAction):
    def __init__(self):
        self.volume = SysActionParamFloat(range=[0, syringeUsableVolume_ul], name='Volume', units='ul', value=syringeUsableVolume_ul)
        self.repeat = SysActionParamInt('Repeat', [0,100], value=1)
        self.speed = SysActionParamFloat(pump.vars['Speed'], value=10)
        SysAction.__init__(self, 'BGE->interface', (self.volume, self.speed, self.repeat))

    def Command(self):
        valves.vars['anions liquids'].Set(anionsBGE)
        valves.vars['cations liquids'].Set(cationsBGE)
        
        for _ in range(self.repeat.Get()):
            supplyLiquids(self.volume.Get(), self.speed.Get())


class ActionSample2Interfaces(SysAction):
    def __init__(self):
        self.volume = SysActionParamFloat(range=[0, syringeUsableVolume_ul], name='Volume', units='ul', value=syringeUsableVolume_ul)
        self.repeat = SysActionParamInt('Repeat', [0,100], value=1)
        self.speed = SysActionParamFloat(pump.vars['Speed'], value=10)
        SysAction.__init__(self, 'Sample->interface', (self.volume, self.speed, self.repeat))

    def Command(self):
        valves.vars['anions liquids'].Set(anionsSample)
        valves.vars['cations liquids'].Set(cationsSample)
        
        for _ in range(self.repeat.Get()):
            supplyLiquids(self.volume.Get(), self.speed.Get())


class ActionFlushCapillary(SysAction):
    def __init__(self):
        self.prs = SysActionParamFloat(pressureController.vars['P'])
        self.seconds = SysActionParamTime()
        self.trigger = SysActionParamInt('trigger?', [0,1])
        SysAction.__init__(self, 'Flush capillary', (self.seconds, self.prs, self.trigger))

    def Command(self):
        valves.vars['anions liquids'].Set('closed')
        valves.vars['cations liquids'].Set('closed')
        
        valves.vars['pressure'].Set(pressureVenting)
        valves.vars['pump/pressure'].Set(pressureToInterfaces)
        valves.vars['pressure'].Set(pressureOn)
        
        if self.trigger.Get(): ecorder.vars['trigger'].Set('on')
        setPressure(self.prs.Get())
                
        cfg.Sleep(self.seconds.Get())
        
        pressureController.vars['P'].Set(0)
        print 0
        if self.trigger.Get(): ecorder.vars['trigger'].Set('off')
                
        valves.vars['pressure'].Set(pressureVenting)
        valves.vars['pump/pressure'].Set(pumpToInterfaces)
        valves.vars['pressure'].Set('closed')


class ActionSeparation(SysAction):
    def __init__(self):
        self.seconds = SysActionParamTime()
        self.kVoltsMinus = SysActionParamFloat(spellmanMinus.vars['V'], name='V-')
        self.kVoltsPlus = SysActionParamFloat(spellmanPlus.vars['V'], name='V+')
        SysAction.__init__(self, 'HV separation', (self.seconds, self.kVoltsMinus, self.kVoltsPlus))

    def Command(self):
        valves.vars['pump/pressure'].Set('closed')
        valves.vars['pressure'].Set('closed')
        valves.vars['anions liquids'].Set(anionsBGE)
        valves.vars['cations liquids'].Set(cationsBGE)
        
        spellmanMinus.vars['I'].Set(spellmanMinus.vars['I'].range[1])
        spellmanPlus.vars['I'].Set(spellmanPlus.vars['I'].range[1])
        spellmanMinus.vars['enable'].Set('on')
        spellmanPlus.vars['enable'].Set('on')
                
        ecorder.vars['trigger'].Set('on')
        
        spellmanMinus.vars['V'].Set(self.kVoltsMinus.Get())
        spellmanPlus.vars['V'].Set(self.kVoltsPlus.Get())
                    
        cfg.Sleep(self.seconds.Get())
        
        spellmanMinus.vars['V'].Set(0)
        spellmanPlus.vars['V'].Set(0)
    
        ecorder.vars['trigger'].Set('off')
        
        spellmanMinus.vars['enable'].Set('off')
        spellmanPlus.vars['enable'].Set('off')
        spellmanMinus.vars['I'].Set(0)
        spellmanPlus.vars['I'].Set(0)
    

'''
*** System
'''
class System(Instrument):
    def __init__(self):
        comps = (spellmanMinus, spellmanPlus, pressureController, sensors, envThermometer, boxThermostat, valves, pump, ecorder)
        actions = (ActionBGE2Interfaces(),
                   ActionSample2Interfaces(),
                   ActionFlushCapillary(),
                   ActionSeparation(),
                   SetThermostat()
                   )
        name = 'portableCE-Argentina'
        description = 'A portable dual-channel Capillary Electrophoresis instrument'
        version = '1.0'
         
        Instrument.__init__(self, comps, actions, version, name, description)
 
'''
*** Run program
'''        
if __name__ == '__main__':
    # run the program
    System()