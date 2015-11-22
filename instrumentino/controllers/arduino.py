from kivy.properties import NumericProperty
from instrumentino.channels import DataChannelIn, DataChannelOut,\
    DataChannelInOut
from instrumentino.controllers import Controller
from instrumentino.cfg import *

class Arduino(Controller):
    '''An Arduino hardware controller.
    For more details: http://www.arduino.cc/
    '''

    BITS_NUM_ANALOG_IN_PIN = 10
    BITS_NUM_DIGITAL_PIN = 8
    '''The number of bits in different channels
    '''

    MAX_VALUE_ANALOG_IN_PIN = 1024
    MAX_VALUE_DIGITAL_PIN = 1
    MAX_VALUE_PWM_PIN = 256
    '''Maximal values for native read and write operations
    '''

    CHANNEL_TYPE_STR_ANALOG_IN = 'A'
    CHANNEL_TYPE_STR_DIGITAL = 'D'
    CHANNEL_TYPE_STR_PWM = 'P'
    CHANNEL_TYPE_STR_I2C = 'I'
    '''Channel identifiers in the controller
    '''

    def __init__(self, **kwargs):
        super(Arduino, self).__init__(**kwargs)

        
class ArduinoChannelIn_AnalolgInPin(DataChannelIn):
    '''An analog pin input channel.
    '''
    
    def __init__(self, **kwargs):
        kwargs['data_bits'] = Arduino.BITS_NUM_ANALOG_IN_PIN
        kwargs['type_str'] = Arduino.CHANNEL_TYPE_STR_ANALOG_IN
        kwargs['max_input_value'] = Arduino.MAX_VALUE_ANALOG_IN_PIN
        super(ArduinoChannelIn_AnalolgInPin, self).__init__(**kwargs)
    
    
class ArduinoChannelIn_DigitalPin(DataChannelIn):
    '''A digital pin input channel.
    '''
    
    def __init__(self, **kwargs):
        kwargs['data_bits'] = Arduino.BITS_NUM_DIGITAL_PIN
        kwargs['type_str'] = Arduino.CHANNEL_TYPE_STR_DIGITAL
        kwargs['max_input_value'] = Arduino.MAX_VALUE_DIGITAL_PIN
        super(ArduinoChannelIn_DigitalPin, self).__init__(**kwargs)
        
    def do_first_when_online(self):
        '''Tell the Arduino that this is an input pin. 
        '''
        self.controller.controlino_protocol.set_channel_direction(self, is_output=False)
        super(ArduinoChannelIn_DigitalPin, self).do_first_when_online()
    

class ArduinoChannelOut_DigitalPin(DataChannelOut):
    '''A digital pin output channel.
    '''
    
    def __init__(self, **kwargs):
        kwargs['data_bits'] = Arduino.BITS_NUM_DIGITAL_PIN
        kwargs['type_str'] = Arduino.CHANNEL_TYPE_STR_DIGITAL
        kwargs['max_output_value'] = Arduino.MAX_VALUE_DIGITAL_PIN
        super(ArduinoChannelOut_DigitalPin, self).__init__(**kwargs)
        
    def do_first_when_online(self):
        '''Tell the Arduino that this is an output pin. 
        '''
        self.controller.controlino_protocol.set_channel_direction(self, is_output=True)
        super(ArduinoChannelOut_DigitalPin, self).do_first_when_online()

    
class ArduinoChannelInOut_DigitalPin(DataChannelInOut):
    '''A digital pin output channel.
    '''
    
    def __init__(self, **kwargs):
        kwargs['data_bits'] = Arduino.BITS_NUM_DIGITAL_PIN
        kwargs['type_str'] = Arduino.CHANNEL_TYPE_STR_DIGITAL
        kwargs['max_input_value'] = Arduino.MAX_VALUE_DIGITAL_PIN
        kwargs['max_output_value'] = Arduino.MAX_VALUE_DIGITAL_PIN
        super(ArduinoChannelInOut_DigitalPin, self).__init__(**kwargs)
        
    def do_first_when_online(self):
        '''Tell the Arduino that this is an output pin. 
        '''
        self.controller.controlino_protocol.set_channel_direction(self, is_output=True)
        super(ArduinoChannelInOut_DigitalPin, self).do_first_when_online()
    
    
class ArduinoChannelOut_PwmPin(DataChannelOut):
    '''A PWM pin output channel.
    '''
    
    def __init__(self, **kwargs):
        kwargs['data_bits'] = Arduino.BITS_NUM_DIGITAL_PIN
        kwargs['type_str'] = Arduino.CHANNEL_TYPE_STR_PWM
        kwargs['max_output_value'] = Arduino.MAX_VALUE_PWM_PIN
        super(ArduinoChannelOut_PwmPin, self).__init__(**kwargs)

