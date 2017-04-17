from kivy.properties import BoundedNumericProperty, ListProperty, NumericProperty, BooleanProperty
from numpy import sin, cos, pi, linspace
import time
from construct.lib.container import Container
import re
from instrumentino.controlino_protocol import ControlinoProtocol
from instrumentino.communication import CommunicationPort
from instrumentino.cfg import *
from instrumentino.channels import DataChannelIn
from instrumentino import channels


class CommunicationPortSimulation(CommunicationPort):
    '''A simulated communication port
    '''

    type_name = 'Simulation'
    '''The name of this communication type
    '''

    sim_data_packets_num = BoundedNumericProperty(0, min=0)
    '''Keep a record of how many data packets were rendered
    '''

    t_zero = NumericProperty(0)
    '''The t=0 time for timestamp calculations
    This is initialized when Instrumentino sends an "RTC:SET" command to the controller.
    '''

    t_zero_set = BooleanProperty(False)
    '''Indicate if t_zero was set.
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
            sim_packet = self.controller.controlino_protocol.string_packet_format.build(
                {'packet_header': {'type': 'STRING_PACKET', 'packet_length': 0},
                 'string': self.controller.controlino_protocol.STRING_PACKET_TYPE_PONG
                 })
            packet_length = len(sim_packet)
            sim_packet = self.controller.controlino_protocol.string_packet_format.build(
                {'packet_header': {'type': 'STRING_PACKET', 'packet_length': packet_length},
                 'string': self.controller.controlino_protocol.STRING_PACKET_TYPE_PONG
                 })


            # Return the string packet
            self.reply_to_ping = False

        elif self.t_zero_set:
            # Simulate data packets
            sim_data_packet_blocks = []
            for idx, channel in enumerate(self.controller.input_channels):
                # Determine how many data points (if at all) should be sent this time for this channel.
                rates_ratio = channel.sampling_rate / self.controller.data_packet_rate
                if rates_ratio >= 1:
                    data_points_num = int(rates_ratio)
                elif (self.sim_data_packets_num * rates_ratio).is_integer():
                    data_points_num = 1
                else:
                    continue

                # Create the data block and append it to the rest of the blocks
                pattern = self.__get_sim_data_pattern(channel)
                start_index = int(self.sim_data_packets_num * rates_ratio) % len(pattern)
                data_points = pattern[start_index:start_index + data_points_num]
                block = self.controller.controlino_protocol.data_packet_data_block_format.build({block_id:idx, data:{Int8:data_points}})
                sim_data_packet_blocks.append(block)

            # Send the relative timestamp in milliseconds
            relative_start_timestamp = (time.time() - self.t_zero) * 1000

            # Build the header two times. First without specifying the length, and then a second time,
            # using the anchor to get its length
            sim_packet = self.controller.controlino_protocol.data_packet_format.build(
                {'packet_header': {'type': 'DATA_PACKET', 'packet_length': 0},
                 'data_packet_header': {'relative_start_timestamp': relative_start_timestamp},
                 'data_blocks': sim_data_packet_blocks
                 }
            )
            packet_length = len(sim_packet)
            sim_packet = self.controller.controlino_protocol.data_packet_format.build(
                {'packet_header': {'type': 'DATA_PACKET', 'packet_length': packet_length},
                 'data_packet_header': {'relative_start_timestamp': relative_start_timestamp},
                 'data_blocks': sim_data_packet_blocks
                 }
            )

            self.sim_data_packets_num += 1

        # Send the packet to the communication port
        return sim_packet

    def __get_sim_data_pattern(self, channel):
        '''Simulate incoming data
        '''

        if channel.type_str == 'A':
            return [channel.max_input_value / 2 + sin(x * (channel.number + 1)) * (channel.max_input_value / 3) for x in
                    linspace(0, 2 * pi, channel.sampling_rate * 10, endpoint=False)]
        elif channel.type_str == 'D':
            return [0] * (channel.sampling_rate * (channel.number + 1)) + [channel.max_input_value] * (
                channel.sampling_rate * (channel.number + 1))
        else:
            raise RuntimeError('Unsopported channel type for simulation')

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

        if command == ControlinoProtocol.CMD_ACQUIRE_START:
            # Set the t0 time to be now.
            self.t_zero = time.time()
            self.t_zero_set = True
        elif command == ControlinoProtocol.CMD_ACQUIRE_STOP:
            self.t_zero_set = False
        elif command == ControlinoProtocol.CMD_PING:
            # Flag the packet rendering method to reply to the ping command
            self.reply_to_ping = True
