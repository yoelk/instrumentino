from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar, SysVarAnalogArduinoBipolarWithExternalPolarity
__author__ = 'yoelk'

from instrumentino import cfg

class Spellman(SysCompArduino):
    ''' Supports either a unipolar voltage controller or a bipolar voltage controller with a symmetric range [-X,X] '''
    def __init__(self, name, rangeV, rangeI, pinEnable, pinInV, pinInI, pinOutV, pinOutI=None, highFreqPWM=False, pinsVoltsMax=5, safetyMaxAbsVoltage=None):
        varEnable = SysVarDigitalArduino('enable', pinEnable, name)
        
        # Reduce maximal pin output according to security voltage
        if safetyMaxAbsVoltage != None:
            divider = safetyMaxAbsVoltage / max(abs(rangeV[0]), abs(rangeV[1]))
        else:
            divider = 1
        rangeV[0] *= divider
        rangeV[1] *= divider
        pinsVoltsMaxAdjusted = pinsVoltsMax * divider
        
        # set voltage variable according to the voltage range. Use methods defined in the instantiated sub-class 
        if rangeV[0] * rangeV[1] >= 0:
            voltageVar = SysVarAnalogArduinoUnipolar('V', rangeV, pinInV, pinOutV, name, 'Voltage', 'kV', self.PreEditV, highFreqPWM=highFreqPWM, pinOutVoltsMax=pinsVoltsMaxAdjusted, pinInVoltsMax=pinsVoltsMaxAdjusted)
        else:
            voltageVar = SysVarAnalogArduinoBipolarWithExternalPolarity('V', rangeV, pinInV, pinOutV, self.SetPolarityPositive, self.GetPolarityPositive, name, 'Voltage', 'kV', self.PreEditV, highFreqPWM=highFreqPWM, pinOutVoltsMax=pinsVoltsMaxAdjusted, pinInVoltsMax=pinsVoltsMaxAdjusted)            
        
        currentVar = SysVarAnalogArduinoUnipolar('I', rangeI, pinInI, pinOutI, name, 'Current', 'uA', highFreqPWM=highFreqPWM, pinOutVoltsMax=pinsVoltsMax, pinInVoltsMax=pinsVoltsMax)
        
        SysCompArduino.__init__(self, name,
                                (voltageVar, currentVar, varEnable),
                                'monitor/change High Voltage variables')
        
    def FirstTimeOnline(self):
        self.GetController().PinModeOut(self.vars['enable'].pin)
        super(Spellman, self).FirstTimeOnline()
        
    def PreEditV(self, value):
        pass
        

class SpellmanCZE30PN2000(Spellman):
    def __init__(self, name, pinEnable, pinPolaritySet, pinPolarityPositive, pinInV, pinInI, pinOutV, pinOutI=None, highFreqPWM=False, safetyMaxAbsVoltage=None):
        self.varPolaritySet = SysVarDigitalArduino('polaritySet', pinPolaritySet, name)
        self.varPolarityPositive = SysVarDigitalArduino('polarityPositive', pinPolarityPositive, name, editable=False)
        rangeV = [-30, 30]
        rangeI = [0, 300]
        Spellman.__init__(self, name, rangeV, rangeI, pinEnable, pinInV, pinInI, pinOutV, pinOutI, highFreqPWM=highFreqPWM, pinsVoltsMax=5, safetyMaxAbsVoltage=safetyMaxAbsVoltage)
        
    def SetPolarityPositive(self, positive=True):
        self.varPolaritySet.Set('on' if positive else 'off');
    
    def GetPolarityPositive(self):
        return self.varPolarityPositive.Get() == 'on'

    def PreEditV(self, value):
        ''' function overload '''
        self.varPolaritySet.Set('on' if value > 0 else 'off');

    def FirstTimeOnline(self):
        self.GetController().PinModeOut(self.varPolaritySet.pin)
        self.GetController().PinModeIn(self.varPolarityPositive.pin)
        super(SpellmanCZE30PN2000, self).FirstTimeOnline()


class SpellmanUM20_4_PLUS(Spellman):
    def __init__(self, name, pinEnable, pinInV, pinInI, pinOutV, pinOutI=None, highFreqPWM=False, safetyMaxAbsVoltage=None):
        rangeV = [0, 20]
        rangeI = [0, 200]
        Spellman.__init__(self, name, rangeV, rangeI, pinEnable, pinInV, pinInI, pinOutV, pinOutI, highFreqPWM=highFreqPWM, pinsVoltsMax=4.64, safetyMaxAbsVoltage=safetyMaxAbsVoltage)


class SpellmanUM20_4_MINUS(Spellman):
    def __init__(self, name, pinEnable, pinInV, pinInI, pinOutV, pinOutI=None, highFreqPWM=False, safetyMaxAbsVoltage=None):
        rangeV = [-20, 0]
        rangeI = [0, 200]
        Spellman.__init__(self, name, rangeV, rangeI, pinEnable, pinInV, pinInI, pinOutV, pinOutI, highFreqPWM=highFreqPWM, pinsVoltsMax=4.64, safetyMaxAbsVoltage=safetyMaxAbsVoltage)