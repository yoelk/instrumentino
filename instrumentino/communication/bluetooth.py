# from kivy.properties import StringProperty, NumericProperty
# from instrumentino.controllers.communication import CommunicationPort
# 
# class CommunicationPortBluetooth(CommunicationPort):
#     '''A Bluetooth communication port
#     '''
# 
#     def get_new_data_packet(self):
#         '''Return data packets received via Bluetooth
#         '''
#         # TODO: implement
#         
#     def __init__(self, **kwargs):
#         '''Setup serial communication.
#         '''
#         super(CommunicationPortBluetooth, self).__init__(**kwargs)
#         serial_port = kwargs.get('serial_port', '')
#         baudrate = kwargs.get('baudrate', 0)