from __future__ import division
from instrumentino import Instrument
from instrumentino import cfg
from instrumentino.action import SysAction, SysActionParamTime, SysActionParamFloat
from instrumentino.controllers.labsmith_eib.labsmith_comps import LabSmithValves4VM01
from instrumentino.controllers.arduino.parker import ParkerPressureController
from instrumentino.controllers.labsmith_eib import SysVarDigitalLabSmith_AV201Position
 
'''
*** System constants
'''
# Arduino pin assignments
pinAnalInParkerP = 5
pinPwmOutParkerP = 6
 
# 3-way LabSmith Valves can be set to 'A', 'B' and 'closed'
valvePortPressure = 'A'
valvePortExhaust = 'B'
 
'''
*** System components
'''
pressureController = ParkerPressureController('Pressure', (0,100), pinAnalInParkerP, pinPwmOutParkerP)
valves = LabSmithValves4VM01('valves', (SysVarDigitalLabSmith_AV201Position('V1', 4, 'Help text about valve 1'),))
 
'''
*** System actions
'''
class SysActionFillContainer(SysAction):
    def __init__(self):
        self.seconds = SysActionParamTime()
        self.psi = SysActionParamFloat(pressureController.vars['P'])
        SysAction.__init__(self, 'Fill Container', (self.seconds, self.psi))
 
    def Command(self):
        # Connect container to pressure controller
        valves.vars['V1'].Set(valvePortPressure)
        # Start pressure
        pressureController.vars['P'].Set(self.psi.Get())
         
        # Wait some time
        cfg.Sleep(self.seconds.Get())
        
        # Close container
        valves.vars['V1'].Set('closed')
 
 
class SysActionEmptyContainer(SysAction):
    def __init__(self):
        self.seconds = SysActionParamTime()
        SysAction.__init__(self, 'Empty Container', ())
 
    def Command(self):
        # Stop pressure
        pressureController.vars['P'].Set(0)
        
        # Connect container to pressure controller
        valves.vars['V1'].Set(valvePortExhaust)
         
        # Wait some time
        cfg.Sleep(2)
         
        # Close container
        valves.vars['V1'].Set('closed')
 
'''
*** System
'''
class System(Instrument):
    def __init__(self):
        comps = (pressureController, valves)
        actions = (SysActionFillContainer(),
                   SysActionEmptyContainer())
        name = 'Example System'
        description = 'A container connected, through a valve, to a pressure controller or to the atmosphere'
        version = '1.0'
         
        Instrument.__init__(self, comps, actions, version, name, description)
 
'''
*** Run program
'''        
if __name__ == '__main__':
    # run the program
    System()