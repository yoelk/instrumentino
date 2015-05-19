from __future__ import division
from instrumentino.controllers.arduino.mks import MKSMassFlowController
from instrumentino.controllers.arduino import ArduinoI2cDac

'''
*** System constants
'''
# Arduino pin assignments
from instrumentino.action import SysActionParamTime, SysAction, SysActionParamFloat
from instrumentino import cfg, Instrument
pinAnalInMFC1 = 0
I2C_Address_MFC1 = 0x2C

pinAnalInMFC2 = 1
I2C_Address_MFC2 = 0x2D

pinAnalInMFC3 = 2
I2C_Address_MFC3 = 0x2E

pinAnalInMFC4 = 3
I2C_Address_MFC4 = 0x2F

'''
*** System components
'''

mfc1 = MKSMassFlowController('MFC 1', pinAnalInMFC1, None, None, ArduinoI2cDac(8, I2C_Address_MFC1))
mfc2 = MKSMassFlowController('MFC 2', pinAnalInMFC2, None, None, ArduinoI2cDac(8, I2C_Address_MFC2))
mfc3 = MKSMassFlowController('MFC 3', pinAnalInMFC3, None, None, ArduinoI2cDac(8, I2C_Address_MFC3))
mfc4 = MKSMassFlowController('MFC 4', pinAnalInMFC4, None, None, ArduinoI2cDac(8, I2C_Address_MFC4))

'''
*** System actions
'''
class SysActionStart(SysAction):
    def __init__(self):
        self.seconds = SysActionParamTime(name='Time')
        self.flow1 = SysActionParamFloat(mfc1.vars['Flow'], name='Flow 1')
        self.flow2 = SysActionParamFloat(mfc2.vars['Flow'], name='Flow 2')
        self.flow3 = SysActionParamFloat(mfc3.vars['Flow'], name='Flow 3')
        self.flow4 = SysActionParamFloat(mfc4.vars['Flow'], name='Flow 4')
        SysAction.__init__(self, 'Start', (self.seconds, self.flow1, self.flow2, self.flow3, self.flow4))

    def Command(self):
        mfc1.vars['Flow'].Set(self.flow1.Get())
        mfc2.vars['Flow'].Set(self.flow2.Get())
        mfc3.vars['Flow'].Set(self.flow3.Get())
        mfc4.vars['Flow'].Set(self.flow4.Get())
        
        cfg.Sleep(self.seconds.Get())

        mfc1.vars['Flow'].Set(0)
        mfc2.vars['Flow'].Set(0)
        mfc3.vars['Flow'].Set(0)
        mfc4.vars['Flow'].Set(0)

'''
*** System
'''
class System(Instrument):
    def __init__(self):
        comps = (mfc1, mfc2, mfc3, mfc4)
        actions = (SysActionStart(),)
        name = 'ctlMFC4'
        description = 'Control 4 Mass Flow Controllers (MKS)'
        version = '1.0'
        
        Instrument.__init__(self, comps, actions, version, name, description)

'''
*** Run program
'''        
if __name__ == '__main__':
    # run the program
    System()