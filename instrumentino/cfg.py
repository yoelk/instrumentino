from __future__ import division

DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'simulation', 'address': ''}
# DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'serial', 'address': '/dev/tty.usbserial-A400Y5SF'}
import gc
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

def get_attributes_of_type(obj, attribute_type, kwargs={}):
    '''Return a list of objects of a specific type. The objects might already exist
    in the object or they've been passed to it through kwargs. 
    '''
    matching_attributes = []
    
    # First go over the kwargs
    for key, value in kwargs.items():
        if isinstance(value, attribute_type):
            matching_attributes.append(value)
    
    # Now go over the existing attributes, but don't add items that we already added from kwargs
    for attr_name in [n for n in dir(obj) if n not in kwargs.keys()]:
        attr = getattr(obj, attr_name)
        if isinstance(attr, attribute_type):
            matching_attributes.append(attr)
            
    return matching_attributes

def create_default_name(object_self, use_index=True):
    '''Create a default name for GUI items that didn't get their name defined.
    For example, if an controller from class "Arduino" isn't given a name specifically, it will be called "Arduino 1"
    '''
    name = '{}'.format(type(object_self).__name__)
    if use_index:
        name += '{}'.format(len([obj for obj in gc.get_objects() if isinstance(obj, type(object_self))]))
    return name


class MissingNecessaryAttributeError(RuntimeError):
    '''Raised when a necessary attribute is missing in a subclass.
    '''
    pass
    