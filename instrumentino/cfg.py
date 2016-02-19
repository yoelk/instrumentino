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
    
    # First use all of the given kwargs
    for attr_name in attributes_list:
        if attr_name in kwargs.keys():
            setattr(obj, attr_name, kwargs[attr_name])
            attributes_list.remove(attr_name)
    
    # Now check if all of the necessary attributes exist
    for attr_name in attributes_list:
        if (not hasattr(obj, attr_name) or
            not getattr(obj, attr_name)):
            # A necessary attribute is missing or empty
            raise MissingNecessaryAttributeError(attr_name)


class MissingNecessaryAttributeError(RuntimeError):
    '''Raised when a necessary attribute is missing in a subclass.
    '''
    pass
    