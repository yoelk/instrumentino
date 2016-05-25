from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino, SysVarDigitalArduino
__author__ = 'yoelk'

class DigitalPins(SysCompArduino):
    def __init__(self, name, digiVars=()):
        SysCompArduino.__init__(self, name, digiVars, "turn on/off Arduino digital pins")
 
 
class AnalogPins(SysCompArduino):
    def __init__(self, name, analogVars=()):
        SysCompArduino.__init__(self, name, analogVars, "set Arduino analog pins")