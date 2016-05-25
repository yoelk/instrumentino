from __future__ import division
__author__ = 'yoelk'

from ctypes import *
from instrumentino.controllers import InstrumentinoController
from instrumentino.comp import SysVarDigital, SysComp, SysVarAnalog
from instrumentino import cfg
import time
from instrumentino.util import Chdir
from threading import Semaphore, Thread

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
    DEVICE_TYPE_4AM01 = 3
    
    VALVE_STATE_UNKNOWN = 0
    VALVE_STATE_UNCHANGED = 0
    VALVE_STATE_A = 1
    VALVE_STATE_CLOSED = 2
    VALVE_STATE_B = 3
    
    REG_CHANNEL_A = 0
    REG_CHANNEL_B = 1
    REG_CHANNEL_C = 2
    REG_CHANNEL_D = 3

    
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
        self.syringePumps = {}

    def Connect(self, port):
        '''
        port - the name of the serial port. This works on unix and windows systems, given the appropriate name
        '''
        # This works only in windows, so port numbers are COM1,COM2 etc.
        portNumber = int(port.replace('COM', ''))
        
        tempDirChange = Chdir(cfg.ResourcePath())
        self.DLL = CDLL('uProcessDriver_C_V1_2_1.dll')
        del tempDirChange
        self.EIB = self.DLL.NewEIB()
        if self.EIB == 0:
            return False
        retCode = self.DLL.ConnectEIB(self.EIB, portNumber)
        if retCode != 0:
            return False
        self.syringePumps = {}
        self.valves = None
        self.sensors = None
        
        DeviceDataArray = c_ubyte * (self.MAX_DEVICE_ADDRESS+1)
        deviceAddresses = DeviceDataArray()
        deviceTypes = DeviceDataArray()
        devicesNum = self.DLL.ScanDevices(self.EIB, byref(deviceAddresses), byref(deviceTypes))
        print str(devicesNum) + ' devices found:'
        if not devicesNum > 0:
            return False
        for idx in range(devicesNum):
            if deviceTypes[idx] == self.DEVICE_TYPE_SPS01:
                print 'SPS01 @' + str(deviceAddresses[idx])
                self.syringePumps[deviceAddresses[idx]] = self.DLL.NewSPS01(self.EIB, c_ubyte(deviceAddresses[idx]))
                retCode = self.DLL.InitSyringe(self.syringePumps[deviceAddresses[idx]])
                if retCode == 0:
                    return False
            if deviceTypes[idx] == self.DEVICE_TYPE_4VM01:
                print '4VM01 @' + str(deviceAddresses[idx])
                self.valves = self.DLL.New4VM01(self.EIB, c_ubyte(deviceAddresses[idx]))
                retCode = self.DLL.InitValves(self.valves)
                if retCode == 0:
                    return False
            if deviceTypes[idx] == self.DEVICE_TYPE_4AM01:
                print '4AM01 @' + str(deviceAddresses[idx])
                self.sensors = self.DLL.New4AM01(self.EIB, c_ubyte(deviceAddresses[idx]))
                retCode = self.DLL.InitSensors(self.sensors)
                if retCode == 0:
                    return False
        
        return True
    
    def Close(self):
        self.accessSemaphore.acquire(True)
        for pump in self.syringePumps.values():
            self.DLL.StopSyringe(pump)
        self.accessSemaphore.release()
        
    def GetSensorValue(self, port):
        getFunc = self.DLL.GetSensorValue
        getFunc.restype = c_double
        return getFunc(self.sensors, c_int(port))
            
    def SetValves(self, **kwargs):
        valves = ['unchanged', 'unchanged', 'unchanged', 'unchanged']
        for name, value in kwargs.items():
            valveNum = int(name.replace('valve', ''))
            valves[valveNum-1] = value
        
        thread = Thread(target=self.DLL.SetValves, args=(self.valves,
                                                          c_int(self.valveStateToValue[valves[0]]),
                                                          c_int(self.valveStateToValue[valves[1]]),
                                                          c_int(self.valveStateToValue[valves[2]]),
                                                          c_int(self.valveStateToValue[valves[3]])))
        thread.start()
        thread.join()

        time.sleep(0.7)
        
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


class SysVarAnalogLabSmith_SensorValue(SysVarAnalog):
    '''
    A LabSmith analog variable for sensor readings (using a 4AM01 manifold)
    '''
    def __init__(self, name, manifoldPort, units, range, helpLine='', editable=False):
        SysVarAnalog.__init__(self, name, range, LabSmithEIB, helpLine=helpLine, editable=editable, units=units)
        self.sensorManifold = None
        self.manifoldPort = manifoldPort

    def SetManifold(self, sensorManifold):
        self.sensorManifold = sensorManifold
        self.compName = sensorManifold.name
        
    def GetFunc(self):
        return self.sensorManifold.getSensor(self.manifoldPort) 
    
    def SetFunc(self, percent):
        pass


class SysVarDigitalLabSmith_CachedAnalog(SysVarAnalog):
    '''
    A LabSmith cached analog variable
    '''
    def __init__(self, name, compName, comp, units='%', range=[0,100], helpLine='', editable=True, showInSignalLog=True):
        SysVarAnalog.__init__(self, name, range, LabSmithEIB, compName, helpLine=helpLine, editable=editable, units=units, showInSignalLog=showInSignalLog)
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
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Speed', compName, comp, helpLine='set pump speed', showInSignalLog=False)

    def SetFunc(self, percent):
        super(SysVarDigitalLabSmith_SyringeSpeed, self).SetFunc(percent)
        self.comp.SetSyringeSpeed(percent)
        
        
class SysVarDigitalLabSmith_SyringeFlowrate(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 flow-rate (in uL/min)
    '''
    def __init__(self, compName, comp, range, editable=True):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Flowrate', compName, comp, range=range, helpLine='set pump flow rate', showInSignalLog=False, units='uL/min')

    def SetFunc(self, flowrate):
        super(SysVarDigitalLabSmith_SyringeFlowrate, self).SetFunc(flowrate)
        self.comp.SetSyringeFlowrate(flowrate)
        
        
class SysVarDigitalLabSmith_SyringePower(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 power
    '''
    def __init__(self, compName, comp, editable=True):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Power', compName, comp, helpLine='set pump power', showInSignalLog=False)

    def SetFunc(self, percent):
        super(SysVarDigitalLabSmith_SyringePower, self).SetFunc(percent)
        self.comp.SetSyringePower(percent)
        
        
class SysVarDigitalLabSmith_SyringeMaxVolume(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 maximal volume
    '''
    def __init__(self, compName, comp):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Max volume', compName, comp, units='ul', editable=False, helpLine='syringe maximal volume', showInSignalLog=False)
        
    def SetMaxVolume(self, maxVolume):
        self.cache = maxVolume


class SysVarDigitalLabSmith_SyringePlunger(SysVarDigitalLabSmith_CachedAnalog):
    '''
    A LabSmith SPS01 plunger location
    '''
    def __init__(self, compName, comp, editable=True):
        SysVarDigitalLabSmith_CachedAnalog.__init__(self, 'Plunger', compName, comp, helpLine='set plunger location', showInSignalLog=False)
        self.maxVolume = 0

    def SetFunc(self, percent):
        super(SysVarDigitalLabSmith_SyringePlunger, self).SetFunc(percent)
        self.comp.MoveSyringeToVolumePercent(percent, self.maxVolume)
        
    def SetMaxVolume(self, maxVolume):
        self.maxVolume = maxVolume