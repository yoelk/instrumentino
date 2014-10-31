from __future__ import division
__author__ = 'yoelk'

from ctypes import *
from instrumentino.controllers import InstrumentinoController
from instrumentino.comp import SysVarDigital, SysComp, SysVarAnalog
from instrumentino import cfg
import time
from instrumentino.util import Chdir
from threading import Semaphore

class LabSmithEIB(InstrumentinoController):
    '''
    This class implements an interface to a LabSmith EIB controller 
    '''

    '''
    EIB constants
    '''
    MIN_DEVICE_ADDRESS = 0x01
    MAX_DEVICE_ADDRESS = 0x7F
    
    DEVICE_TYPE_SPS01 = 1
    DEVICE_TYPE_4VM01 = 2
    
    VALVE_STATE_UNKNOWN = 0
    VALVE_STATE_UNCHANGED = 0
    VALVE_STATE_A = 1
    VALVE_STATE_CLOSED = 2
    VALVE_STATE_B = 3
    
    SYRINGE_PUMP_MAX_POWER = 0xA0

    valveStateToValue = {'A': VALVE_STATE_A,
                         'B': VALVE_STATE_B,
                         'closed': VALVE_STATE_CLOSED,
                         'unchanged': VALVE_STATE_UNCHANGED}
    valveValueToState = {v: k for k, v in valveStateToValue.items()}
    
    name = 'LabSmith EIB'
    
    def __init__(self):
        InstrumentinoController.__init__(self, self.name)
        self.accessSemaphore = Semaphore()
        self.syringePump = None

    def Connect(self, port):
        '''
        port - the name of the serial port. This works on unix and windows systems, given the appropriate name
        '''
        # This works only in windows, so port numbers are COM1,COM2 etc.
        portNumber = int(port.replace('COM', ''))
        
        tempDirChange = Chdir(cfg.ResourcePath())
#         self.DLL = CDLL('uProcessDriver_C_V1_2_1.dll')
        self.DLL = CDLL('uProcessDriver_C.dll')
        del tempDirChange
        self.EIB = self.DLL.NewEIB()
        if self.EIB == 0:
            return False
        retCode = self.DLL.ConnectEIB(self.EIB, portNumber)
        if retCode != 0:
            return False
        self.syringePump = None
        self.valves = None
        
        DeviceDataArray = c_ubyte * (self.MAX_DEVICE_ADDRESS+1)
        deviceAddresses = DeviceDataArray()
        deviceTypes = DeviceDataArray()
        devicesNum = self.DLL.ScanDevices(self.EIB, byref(deviceAddresses), byref(deviceTypes))
        if not devicesNum > 0:
            return False
        for idx in range(devicesNum):
            if deviceTypes[idx] == self.DEVICE_TYPE_SPS01:
                self.syringePump = self.DLL.NewSPS01(self.EIB, c_ubyte(deviceAddresses[idx]))
                retCode = self.DLL.InitSyringe(self.syringePump)
                if retCode == 0:
                    return False
            if deviceTypes[idx] == self.DEVICE_TYPE_4VM01:
                self.valves = self.DLL.New4VM01(self.EIB, c_ubyte(deviceAddresses[idx]))
                retCode = self.DLL.InitValves(self.valves)
                if retCode == 0:
                    return False
        
        return True
    
    def Close(self):
        if self.syringePump != None:
            self.StopSyringe()
            
    def SetValves(self, **kwargs):
        self.accessSemaphore.acquire(True)
        valves = ['unchanged', 'unchanged', 'unchanged', 'unchanged']
        for name, value in kwargs.items():
            valveNum = int(name.replace('valve', ''))
            valves[valveNum-1] = value
        
        self.DLL.SetValves(self.valves,
                           c_int(self.valveStateToValue[valves[0]]),
                           c_int(self.valveStateToValue[valves[1]]),
                           c_int(self.valveStateToValue[valves[2]]),
                           c_int(self.valveStateToValue[valves[3]]))
        time.sleep(0.7)
        self.accessSemaphore.release()
        
    def GetValves(self):
        self.accessSemaphore.acquire(True)
        valves = [c_int(), c_int(), c_int(), c_int()]
        self.DLL.GetValves(self.valves,
                           byref(valves[0]),
                           byref(valves[1]),
                           byref(valves[2]),
                           byref(valves[3]))
        for idx, _ in enumerate(valves):
            try:
                valves[idx] = self.valveValueToState[valves[idx].value]
            except:
                valves[idx] = 0
        
        self.accessSemaphore.release()
        return valves
    
    def SetSyringePower(self, percent):
        self.accessSemaphore.acquire(True)
        self.DLL.SetSyringePower(self.syringePump, c_int(int(percent / 100 * self.SYRINGE_PUMP_MAX_POWER)))
        self.accessSemaphore.release()
        
    def SetSyringeSpeed(self, percent):
        self.accessSemaphore.acquire(True)
        self.DLL.SetSyringeSpeedPercent(self.syringePump, c_double(percent))
        self.accessSemaphore.release()
        
    def SetSyringeDiameterAndGetMaxVolume(self, diameterMiliMeter):
        self.accessSemaphore.acquire(True)
        self.DLL.SetSyringeDiameter(self.syringePump, c_double(diameterMiliMeter))
        maxVolume = self.DLL.GetSyringeMaxVolume(self.syringePump)
        self.accessSemaphore.release()
        return maxVolume

    def MoveSyringeToPosition(self, pos):
        self.accessSemaphore.acquire(True) 
        self.DLL.MoveSyringeToPosition(self.syringePump, c_int(pos))
        time.sleep(6)
        self.accessSemaphore.release()
        
    def MoveSyringeToVolumePercent(self, percent, maxVolume):
        self.accessSemaphore.acquire(True)
        self.DLL.MoveSyringeToVolume(self.syringePump, c_double(percent / 100 * maxVolume))
        time.sleep(6)
        self.accessSemaphore.release()
        
    def StopSyringe(self):
        self.accessSemaphore.acquire(True)
        self.DLL.StopSyringe(self.syringePump)
        self.accessSemaphore.release()


# base class and variables        
class SysCompLabSmith(SysComp):
    '''
    A LabSmith component base class
    '''
    def __init__(self, name, vars, helpLine=''):
        SysComp.__init__(self, name, vars, LabSmithEIB, helpLine)


class SysVarDigitalLabSmith_AV201Position(SysVarDigital):
    '''
    A LabSmith AV201 valve position
    '''
    states = ('A', 'closed', 'B')
    
    def __init__(self, name, valvesControllerPort, helpLine='', editable=True):
        SysVarDigital.__init__(self, name, self.states, LabSmithEIB, helpLine=helpLine, editable=editable)
        self.valvesController = None
        self.valvesControllerPort = valvesControllerPort

    def SetController(self, valvesController):
        self.valvesController = valvesController
        self.compName = valvesController.name
        
    def GetFunc(self):
        state = self.valvesController.getValve(self.valvesControllerPort) 
        return state if state in self.states else None
    
    def SetFunc(self, state):
        self.valvesController.setValve(self.valvesControllerPort, state)


class SysVarDigitalLabSmith_CachedAnalog(SysVarAnalog):
    '''
    A LabSmith cached analog variable
    '''
    def __init__(self, name, compName, comp, units='%', helpLine='', editable=True):
        SysVarAnalog.__init__(self, name, [0,100], LabSmithEIB, compName, helpLine=helpLine, editable=editable, units=units)
        self.comp = comp
        self.cache = 0

    def GetFunc(self):
        return self.cache
    
    def SetFunc(self, percent):
        self.cache = percent


class SysVarDigitalLabSmith_SyringeSpeed(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 speed
    '''
    def __init__(self, compName, comp, editable=True):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Speed', compName, comp, helpLine='set pump speed')

    def SetFunc(self, percent):
        super(SysVarDigitalLabSmith_SyringeSpeed, self).SetFunc(percent)
        self.comp.GetController().SetSyringeSpeed(percent)
        
        
class SysVarDigitalLabSmith_SyringePower(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 power
    '''
    def __init__(self, compName, comp, editable=True):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Power', compName, comp, helpLine='set pump power')

    def SetFunc(self, percent):
        super(SysVarDigitalLabSmith_SyringePower, self).SetFunc(percent)
        self.comp.GetController().SetSyringePower(percent)
        
        
class SysVarDigitalLabSmith_SyringeMaxVolume(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 maximal volume
    '''
    def __init__(self, compName, comp):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Max volume', compName, comp, units='ul', editable=False, helpLine='syringe maximal volume')
        
    def SetMaxVolume(self, maxVolume):
        self.cache = maxVolume


class SysVarDigitalLabSmith_SyringePlunger(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 plunger location
    '''
    def __init__(self, compName, comp, editable=True):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Plunger', compName, comp, helpLine='set plunger location')
        self.maxVolume = 0

    def SetFunc(self, percent):
        super(SysVarDigitalLabSmith_SyringePlunger, self).SetFunc(percent)
        self.comp.GetController().MoveSyringeToVolumePercent(percent, self.maxVolume)
        
    def SetMaxVolume(self, maxVolume):
        self.maxVolume = maxVolume