from __future__ import division
from instrumentino.controllers.arduino.mks import MKSMassFlowController

'''
*** System constants
'''
# Arduino pin assignments
from instrumentino.action import SysActionParamTime, SysAction, SysActionParamFloat
from instrumentino import cfg, Instrument
pinAnalInMFC1 = 3
pinPwmOutMFC1 = 3

pinAnalInMFC2 = 2
pinPwmOutMFC2 = 9

pinAnalInMFC3 = 1
pinPwmOutMFC3 = 10

pinAnalInMFC4 = 0
pinPwmOutMFC4 = 11

'''
*** System components
'''
mfc1 = MKSMassFlowController('MFC 1', pinAnalInMFC1, pinPwmOutMFC1, None)
mfc2 = MKSMassFlowController('MFC 2', pinAnalInMFC2, pinPwmOutMFC2, None)
mfc3 = MKSMassFlowController('MFC 3', pinAnalInMFC3, pinPwmOutMFC3, None)
mfc4 = MKSMassFlowController('MFC 4', pinAnalInMFC4, pinPwmOutMFC4, None)

'''
*** System actions
'''
class SysActionSetFlows(SysAction):
    def __init__(self):
        self.flow1 = SysActionParamFloat(mfc1.vars['Flow'], name='Flow 1')
        self.flow2 = SysActionParamFloat(mfc2.vars['Flow'], name='Flow 2')
        self.flow3 = SysActionParamFloat(mfc3.vars['Flow'], name='Flow 3')
        self.flow4 = SysActionParamFloat(mfc4.vars['Flow'], name='Flow 4')
        SysAction.__init__(self, 'Set Flows', (self.flow1, self.flow2, self.flow3, self.flow4))

    def Command(self):
        mfc1.vars['Flow'].Set(self.flow1.Get())
        mfc2.vars['Flow'].Set(self.flow2.Get())
        mfc3.vars['Flow'].Set(self.flow3.Get())
        mfc4.vars['Flow'].Set(self.flow4.Get())


class SysActionSleep(SysAction):
    def __init__(self):
        self.seconds = SysActionParamTime(name='Time')
        SysAction.__init__(self, 'Start', (self.seconds,))

    def Command(self):
        cfg.Sleep(self.seconds.Get())


class SysActionStopFlows(SysAction):
    def __init__(self):
        SysAction.__init__(self, 'Stop Flows', ())

    def Command(self):        
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
        description = 'Control 4 Mass Flow Controllers (made by MKS).\n'+
        'Each flow is set by a low-pass-filtered PWM pin, and is monitored by an Analog pin'
        version = '1.0'
        
        Instrument.__init__(self, comps, actions, version, name, description)

'''
*** Run program
'''        
if __name__ == '__main__':
    # run the program
    System()