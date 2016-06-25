from __future__ import division

class ArduinoDac(object):
    def __init__(self, dacBits):
        self.maxVal = 2**dacBits-1

    def WriteFraction(self, fraction, controller):
        '''Sub-classes should implement this
        '''
        pass

class DacI2cMAX517(ArduinoDac):
    '''An I2C DAC connected to an Arduino.
    '''
    def __init__(self, address):
        self.address = address
        self.dacBits = 8
        super(DacI2cMAX517, self).__init__(self.dacBits)

    def WriteFraction(self, fraction, controller):
        controller.I2cWrite(self.address, (0, self.maxVal * fraction,))

class DacSpiMCP4922(ArduinoDac):
    '''A channel in an SPI DAC connected to an Arduino.
    '''
    def __init__(self, cs_pin, channel):
        self.dacBits = 12
        self.maxVal = 2**self.dacBits-1
        self.cs_pin = cs_pin
        self.channel = channel
        
        super(DacSpiMCP4922, self).__init__(self.dacBits)

    def WriteFraction(self, fraction, controller):
        value = (int)(self.maxVal * fraction)
        
        dac_register = 0x30
        dac_byte2_mask = 0x00FF
        dac_byte1 = (value >> 8) | dac_register
        dac_byte2 = value & dac_byte2_mask

        if self.channel == 0:
            dac_byte1 &= ~(1<<7)
        elif self.channel == 1:
            dac_byte1 |= (1<<7)
        
        controller.SpiWrite(self.cs_pin, (dac_byte1, dac_byte2))