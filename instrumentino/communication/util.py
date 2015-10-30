from __future__ import division
import os
import glob
try:
    import _winreg as winreg
except ImportError:
    pass
import itertools

def enumerate_serial_ports():
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

def get_serial_ports_list():
        ports = []
        if os.name == 'nt':
            for portname in enumerate_serial_ports():
                ports.append(portname)
        elif os.name == 'posix':
            ports = glob.glob('/dev/tty.*')
            
            return ports