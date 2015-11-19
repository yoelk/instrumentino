from __future__ import division

DEBUG_AUTO_CONNECT = {'connect': True, 'type': 'serial', 'address': '/dev/tty.usbserial-A400Y5SF'}
DEBUG_COMM_STABILITY = False
DEBUG_RX = False
DEBUG_TX = False

DEBUG_PLOT_DIGITAL = False
'''Set debug modes
'''

class MissingKwargsError(RuntimeError):
    '''Raised when a necessary argument was missing in the kwargs.
    '''
    pass
    