from __future__ import division
import os
import glob
import time
from instrumentino.communication import CommunicationPort
try:
    import _winreg as winreg
except ImportError:
    pass
import itertools
from kivy.properties import NumericProperty, ObjectProperty
import serial

class CommunicationPortSerial(CommunicationPort):
    '''A serial communication port
    '''

    type_name = 'Serial'
    '''The name of this communication type
    '''    

    DEFAULT_BAUDRATE = 115200
    '''The dafault baudrate
    '''

    SERIAL_WRITE_TIMEOUT_SEC = NumericProperty(0)
    '''Maximal time to wait for a single write operation.
    '''

    baudrate = NumericProperty(DEFAULT_BAUDRATE)
    '''The baudrate to use for communication.
    '''

    serial_port = ObjectProperty()
    '''The opened serial that we use for communication 
    '''

    def __init__(self, **kwargs):
        '''Setup serial communication.
        '''
        if not set(['address']) <= set(kwargs): raise TypeError('missing mandatory kwargs')
        
        super(CommunicationPortSerial, self).__init__(**kwargs)
        
    def _connect(self):
        '''Connect to the chosen serial port.
        '''
        
        try:
            # Set read timeout according to the controller's data packet rate (It shouldn't be larger than that).
            self.serial_port = serial.Serial(self.address, self.baudrate, writeTimeout=self.SERIAL_WRITE_TIMEOUT_SEC, timeout=(1/self.controller.data_packet_rate) * 0.90)
        except:
            return False

        # Let the controller a couple of seconds to wake up
        time.sleep(2)
        self.serial_port.flushInput()
        return True if self.serial_port else False
            
    def _disconnect(self):
        '''Close the serial port.
        '''
        self.serial_port.close()
    
    def _transmit(self, packet):
        '''Transmit the packet through the serial port.
        '''
        self.serial_port.write(packet)
    
    def _get_incoming_bytes(self):
        '''Check the rx buffer for incoming bytes 
        '''
        return self.serial_port.read(self.MAX_BYTES_PER_READ)
        
    @staticmethod
    def modify_address_field_options_for_settings_menu(json_dict):
        '''Modify the address item in the settings menu. 
        '''
        json_dict['type'] = 'dynamic_options'
        json_dict['function_string'] = 'instrumentino.communication.util.get_serial_ports_list'

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