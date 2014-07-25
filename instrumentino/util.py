from __future__ import division
__author__ = 'yoelk'

import sys
import os
import serial
import glob
from serial.serialutil import SerialException
try:
    import _winreg as winreg
except ImportError:
    pass
import itertools

class Chdir:    
    '''
    Instantiating this class changes the current directory until the object is deleted
    '''     
    def __init__( self, newPath ):  
        self.savedPath = os.getcwd()
        os.chdir(newPath)

    def __del__( self ):
        os.chdir( self.savedPath )


"""
Lists the serial ports available on the computer.
some of the code was taken from Eli Bendersky (eliben@gmail.com), License: this code is in the public domain
"""
class SerialUtil():
    def enumerate_serial_ports(self):
        """ Uses the Win32 registry to return an
            iterator of serial (COM) ports
            existing on this computer.
        """
        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        except WindowsError:
            raise IterationError
    
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                yield str(val[1])
            except EnvironmentError:
                break
            
    def full_port_name(self, portname):
        """ Given a port-name (of the form COM7,
            COM12, CNCA0, etc.) returns a full
            name suitable for opening with the
            Serial class.
        """
        m = re.match('^COM(\d+)$', portname)
        if m and int(m.group(1)) < 10:
            return portname
        return '\\\\.\\' + portname
    
    def getSerialPortsList(self):
            ports = []
            if os.name == 'nt':
                for portname in self.enumerate_serial_ports():
                    ports.append(portname)
            elif os.name == 'posix':
                ports = glob.glob('/dev/tty.*')
                
            return ports
        
if __name__ == '__main__':
    print SerialUtil().getSerialPortsList()