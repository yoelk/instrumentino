from __future__ import division

DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'simulation', 'address': ''}
# DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'serial', 'address': '/dev/tty.usbserial-A400Y5SF'}
DEBUG_COMM_STABILITY = False
DEBUG_RX = False
DEBUG_TX = False

DEBUG_PLOT_DIGITAL = False
'''Set debug modes
'''

def check_for_necessary_attributes(obj, attributes_list, kwargs={}):
    '''Check if all the necessary attributes for an object exist and non-empty.
    If they're empty, check if attr value was passed to them through kwargs.
    '''
    
    for attr in attributes_list:
        if (not hasattr(obj, attr) or
            not getattr(obj, attr)):
            if set([attr]) <= set(kwargs):
                setattr(obj, attr, kwargs[attr])
            else:
                # A necessary attribute is missing or empty
                raise MissingNecessaryAttributeError

class MissingNecessaryAttributeError(RuntimeError):
    '''Raised when a necessary attribute is missing in a subclass.
    '''
    pass
    