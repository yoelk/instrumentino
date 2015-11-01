from __future__ import division
from kivy.properties import BoundedNumericProperty, ListProperty, NumericProperty, BooleanProperty
from numpy import sin, pi, linspace
from construct.macros import Array
import time
from construct.lib.container import Container
import re
from instrumentino.controlino_protocol import ControlinoProtocol
from instrumentino.communication import CommunicationPort

class CommunicationPortSimulation(CommunicationPort):
    '''A simulated communication port
    '''

    type_name = 'Simulation'
    '''The name of this communication type
    '''    

    sim_data_packets_num = BoundedNumericProperty(0, min=0)
    '''Keep a record of how many data packets were rendered
    '''

    sim_data_pattern = ListProperty([sin(x)*49+50 for x in linspace(0, 2*pi, 100, endpoint=False)])
#     sim_data_pattern = [30,70]*10
    '''A pattern for the simulated data.
    '''

    t_zero = NumericProperty(0)
    '''The t=0 time for timestamp calculations
    This is initialized when Instrumentino sends an "RTC:SET" command to the controller.
    '''

    reply_to_ping = BooleanProperty(False)
    '''A flag to indicate if we need to reply to a ping command
    '''

    def __init__(self, **kwargs):
        super(CommunicationPortSimulation, self).__init__(**kwargs)

    def _connect(self):
        '''Set up communication. Nothing to do here.
        '''
        return True
    
    def _transmit(self, packet):
        '''Handle transmitted packets internally.
        '''
        self.handle_instrumentino_commands(packet)

    def _get_incoming_bytes(self):
        '''Render a simulated data packet
        '''
        
        # Check if we need to reply to a ping command
        if self.reply_to_ping:
            # Build the header two times. First without specifying the length, and then a second time,
            # using the anchor to get its length
            sim_packet = self.controller.controlino_protocol.string_packet_format.build(Container(const_header=ControlinoProtocol.CONST_HEADER,
                                                                                                         type='STRING_PACKET',
                                                                                                         packet_length=0,
                                                                                                         string=self.controller.controlino_protocol.STRING_PACKET_TYPE_PONG,
                                                                                                         _end=0)
                                                                                        )
            container = self.controller.controlino_protocol.string_packet_format.parse(sim_packet)
            container.packet_length = container._end
            sim_packet = self.controller.controlino_protocol.string_packet_format.build(container)
            
            # Return the string packet
            self.reply_to_ping = False
        else:
            
            sim_data_packet_blocks = []
            for idx, channel in enumerate(self.controller.input_channels):
                # Determine how many data points (if at all) should be sent this time for this channel.
                rates_ratio = channel.sampling_rate/self.controller.data_packet_rate
                if rates_ratio >= 1:
                    data_points_num = int(rates_ratio)
                elif (self.sim_data_packets_num*rates_ratio).is_integer():
                    data_points_num = 1
                else:
                    continue
    
                # Get the relevant data and serialize it
                start_index = int(self.sim_data_packets_num*rates_ratio)%len(self.sim_data_pattern)
                data_points = self.sim_data_pattern[start_index:start_index+data_points_num]
                data_points_serialized_format = Array(data_points_num, self.controller.get_fitting_data_point_variable(channel.data_bytes))
                data_points_serialized = data_points_serialized_format.build(data_points)
                
                # Build the rest of the data packet block
                id_serialized = self.controller.controlino_protocol.data_packet_block_id_format.build(idx)
                length_serialized = self.controller.controlino_protocol.data_packet_block_length_format.build(len(data_points_serialized))
                block_serialized = id_serialized + length_serialized + data_points_serialized
                
                # Create the data block and append it to the rest of the blocks
                block = self.controller.controlino_protocol.data_packet_block_format.parse(block_serialized)
                sim_data_packet_blocks.append(block)
            
            # Send the relative timestamp in milliseconds
            relative_start_timestamp = (time.time() - self.t_zero) * 1000
            
            # Build the header two times. First without specifying the length, and then a second time,
            # using the anchor to get its length
            sim_packet = self.controller.controlino_protocol.data_packet_format.build(Container(const_header=ControlinoProtocol.CONST_HEADER,
                                                                                                     type='DATA_PACKET',
                                                                                                     packet_length=0,
                                                                                                     relative_start_timestamp=relative_start_timestamp,
                                                                                                     data_packet_block=sim_data_packet_blocks,
                                                                                                     _end=0)
                                                                                      )
            container = self.controller.controlino_protocol.data_packet_format.parse(sim_packet)
            container.packet_length = container._end
            sim_packet = self.controller.controlino_protocol.data_packet_format.build(container)
            
            self.sim_data_packets_num += 1
         
            
        # Send the packet to the communication port
        return sim_packet

    @staticmethod
    def modify_address_field_options_for_settings_menu(json_dict):
        '''Modify the address item in the settings menu. 
        '''
        json_dict['type'] = 'string'
        json_dict['disabled'] = '1' 
        
    def handle_instrumentino_commands(self, packet):
        '''Handle incoming commands from Instrumentino, as if a normal controller would.
        '''
        
        # After removing the terminal \r, the first word is the command, the rest are the params
        command_parts = re.split(' ', packet[:-1])
        command = command_parts[0]
        params = command_parts[1:]
        
        if command == ControlinoProtocol.CMD_SET_CONTROLLER_TIME:
            # Set the t0 time to be now.
            self.t_zero = time.time()
        elif command == ControlinoProtocol.CMD_PING:
            # Flag the packet rendering method to reply to the ping command
            self.reply_to_ping = True