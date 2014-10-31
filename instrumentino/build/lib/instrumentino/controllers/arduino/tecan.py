from __future__ import division
from instrumentino.controllers.arduino import SysCompArduino
from collections import OrderedDict
__author__ = 'yoelk'

from instrumentino import cfg

class TecanSia(SysCompArduino):
    # currently only N0/N1 is supported
    strokeToSeconds = OrderedDict({'N1': 
                                   {0: 1.25,
                                    1: 1.30,
                                    2: 1.39,
                                    3: 1.52,
                                    4: 1.71,
                                    5: 1.97,
                                    6: 2.37,
                                    7: 2.77,
                                    8: 3.03,
                                    9: 3.36,
                                    10: 3.77,
                                    11: 4.30,
                                    12: 5.00,
                                    13: 6.00,
                                    14: 7.50,
                                    15: 10.00,
                                    16: 15.00,
                                    17: 30.00,
                                    18: 31.58,
                                    19: 33.33,
                                    20: 35.29,
                                    21: 37.50,
                                    22: 40.00,
                                    23: 42.86,
                                    24: 46.15,
                                    25: 50.00,
                                    26: 54.55,
                                    27: 60.00,
                                    28: 66.67,
                                    29: 75.00,
                                    30: 85.71,
                                    31: 100.00,
                                    32: 120.00,
                                    33: 150.00,
                                    34: 200.00,
                                    35: 300.00,
                                    36: 333.33,
                                    37: 375.00,
                                    38: 428.57,
                                    39: 500.00, 
                                    40: 600.00}, 
                                   'N2': {}})
    
    DtCmdStart = '/'
    DtCmdEnd = '\r'
    DtCmdExecute = 'R'
    
    serialBaudrate = 9600
    pumpMaxMicroSteps = 48000
    
    def __init__(self, name, pumpVolumeMiliLit, addressPump, addressMultivalve, pinRx=None, pinTx=None, serialPort=1):
        SysCompArduino.__init__(self, 'SIA', (), "send commands to the SIA")
        self.serialPort = serialPort
        if (pinRx != None and pinTx != None):
            self.pinRx = pinRx
            self.pinTx = pinTx
            self.useSoftSer = True
        else:
            self.useSoftSer = False
        self.pumpVolumeMiliLit = pumpVolumeMiliLit
        self.addressPump = addressPump
        self.addressMultivalve = addressMultivalve
        
    def sendCommand(self, address, command, waitForAnswerSec=None):
        self.GetController().SerSend(self.DtCmdStart + address + command + self.DtCmdExecute + self.DtCmdEnd, waitForAnswerSec, self.useSoftSer, self.serialPort)

    def miliLitToMicroSteps(self, miliLit):
        return str(int(miliLit * self.pumpMaxMicroSteps / self.pumpVolumeMiliLit))

    def InitPumpAndMultivalve(self, pumpInitCmd='N1ZJ0', valveInitCmd='ZJ0'):
        self.sendCommand(self.addressPump, pumpInitCmd, waitForAnswerSec=3)
        self.sendCommand(self.addressMultivalve, valveInitCmd, waitForAnswerSec=1)
        
    def selectMultivalvePort(self, port, moveDirection='O', waitForAnswerSec=1):
        self.sendCommand(self.addressMultivalve, moveDirection + str(port), waitForAnswerSec)
    
    def _pullOrDispenseAtMultivalvePort(self, pullOrDispense, port, miliLit, speed, moveDirection, waitForAnswerSec):
        self.selectMultivalvePort(port, moveDirection, waitForAnswerSec)
        volumeFraction = miliLit / self.pumpVolumeMiliLit
        speedIndex = self.speedToSecondsPerStrokeIndex(speed)
        self.sendCommand(self.addressPump, 'OS' + str(speedIndex) + 'M1000' + pullOrDispense + self.miliLitToMicroSteps(miliLit), self.strokeToSeconds['N1'][speedIndex] * volumeFraction + 2)
        
    def _pullOrDispenseAtPumpInputPort(self, pullOrDispense, miliLit, speed):
        volumeFraction = miliLit / self.pumpVolumeMiliLit
        speedIndex = self.speedToSecondsPerStrokeIndex(speed)
        self.sendCommand(self.addressPump, 'IS' + str(speedIndex) + 'M1000' + pullOrDispense + self.miliLitToMicroSteps(miliLit), self.strokeToSeconds['N1'][speedIndex] * volumeFraction + 2)
        
    def pullFromMultivalvePort(self, port, miliLit, speed, moveDirection='I', waitForAnswerSec=1):
        self._pullOrDispenseAtMultivalvePort('P', port, miliLit, speed, moveDirection, waitForAnswerSec)
        
    def dispenseToMultivalvePort(self, port, miliLit, speed, moveDirection='I', waitForAnswerSec=1):
        self._pullOrDispenseAtMultivalvePort('D', port, miliLit, speed, moveDirection, waitForAnswerSec)
        
    def pullFromPumpInputPort(self, miliLit, speed):
        self._pullOrDispenseAtPumpInputPort('P', miliLit, speed)
        
    def dispenseToPumpInputPort(self, miliLit, speed):
        self._pullOrDispenseAtPumpInputPort('D', miliLit, speed)
        
    def TransferFromInputToMultivalvePort(self, port, miliLit, speed, moveDirection='I', waitForAnswerSec=1):
        self.selectMultivalvePort(port, moveDirection, waitForAnswerSec)
        volumeFraction = (miliLit*2) / self.pumpVolumeMiliLit
        speedIndex = self.speedToSecondsPerStrokeIndex(speed)
        self.sendCommand(self.addressPump, 'IS' + str(speedIndex) + 'M1000P' +self.miliLitToMicroSteps(miliLit) + 
                             'OD' + self.miliLitToMicroSteps(miliLit), self.strokeToSeconds['N1'][speedIndex] * volumeFraction + 2)    
        
    def FirstTimeOnline(self):
        if self.useSoftSer:
            self.GetController().SoftSerConnect(self.pinRx, self.pinTx, self.serialBaudrate, self.serialPort)
        else:
            self.GetController().HardSerConnect(self.serialBaudrate, self.serialPort)
        return super(TecanSia, self).FirstTimeOnline()
    
    def speedToSecondsPerStrokeIndex(self, microLitPerSec, microstepMode = 'N1'):
        miliLitPerSec = microLitPerSec / 1000
        secPerStroke = 1 / (miliLitPerSec / self.pumpVolumeMiliLit)
        for indexString, val in self.strokeToSeconds[microstepMode].items():
            if secPerStroke < val:
                return indexString
        # if reached here, return the slowest possibility
        return self.strokeToSeconds[microstepMode].keys()[-1]