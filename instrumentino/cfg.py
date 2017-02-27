from __future__ import division
from __builtin__ import list
import sys

DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'simulation', 'address': ''}
# DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'serial', 'address': '/dev/tty.usbserial-A400Y5SF'}
import gc
import collections
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
    
    # Copy the list since we need to modify it in the loop.
    updated_attr_list = list(attributes_list)
    
    # First use all of the given kwargs
    for attr_name in attributes_list:
        if attr_name in kwargs.keys():
            setattr(obj, attr_name, kwargs[attr_name])
            updated_attr_list.remove(attr_name)
    
    # Now check if all of the necessary attributes exist
    for attr_name in updated_attr_list:
        if (not hasattr(obj, attr_name) or
            not getattr(obj, attr_name)):
            # A necessary attribute is missing or empty
            raise MissingNecessaryAttributeError(attr_name)

def get_instances_in_object(obj, attribute_type, kwargs={}, search_in_lists=True):
    '''Return a list of instances of a specific type. They might already exist
    in the object or they've been passed to it through kwargs. 
    '''
    matching_attributes = []
    
    # First go over the kwargs
    search_list = kwargs.values()
    
    # Now go over the existing attributes, but don't add items that we already added from kwargs
    search_list.extend([getattr(obj, attr_name) for attr_name in dir(obj) if attr_name not in kwargs.keys()])

    for attr in search_list:
        if isinstance(attr, attribute_type):
            matching_attributes.append(attr)
            continue
        
        # Check if fitting attributes are saved in list attributes (or other iterables like tuples etc.)
        if search_in_lists and (isinstance(attr, list) or
                                isinstance(attr, tuple) or
                                isinstance(attr, set)):
            for sub_attr in attr:
                if isinstance(sub_attr, attribute_type) and not sub_attr in matching_attributes:
                    matching_attributes.append(sub_attr)
            
    return matching_attributes

def get_instances_in_module(module, instance_type):
    '''Return a list of instances of a specific type in a module.
    '''
    return [o for o in sys.modules[module].__dict__.values() if isinstance(o, instance_type)]
    
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
    