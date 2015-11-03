/*******************************************************************************
 * Controlino2 - A library to control the resources (e.g. pins)
 * of electronic controllers (e.g. Arduino)
 * through some communication interface (e.g. USB)
 *
 * Copyright (C) 2015 Joel Koenka
 *
 * This code is released under the MIT license.
 *
 * Controlino let's a user control the Arduino pins by issuing simple serial commands such
 * as "CH:READ", "CH:WRITE" etc.
 * It was originally written to be used with Instrumentino, the open-source GUI platform
 * for experimental settings, but can also be used for other purposes.
 *
 * Links:
 *
 * Scientific articles:
 * http://www.sciencedirect.com/science/article/pii/S0010465514002112
 * http://www.ingentaconnect.com/content/scs/chimia/2015/00000069/00000004/art00003
 *
 * Package in PyPi:
 * https://pypi.python.org/pypi/instrumentino
 *
 * Code in GitHub:
 * https://github.com/yoelk/instrumentino
 * https://github.com/yoelk/instrumentino2
 *
 *
 * Modifiers (!!! ATTENTION !!! PLEASE READ !!!)
 * =============================================
 * Before compiling this sketch, make sure you've checked
 * that the right modifiers are set in "controlino_cfg.h"
 *
 ******************************************************************************/

#include "controlino.h"
#include "string.h"

/*******************************************************************************
 * External libraries support
 ******************************************************************************/

// PID library
#ifdef USE_ARDUINO_PID
	#include "PID_v1.h"

	// PID
	#define PID_RELAY_MAX_VARS	4

	// PID-relay variable descriptor
	typedef struct {
		PID* handler;
		int pin_anal_in;
		int pin_digi_out;
		double input_var;
		double output_var;
		unsigned long window_size;
		unsigned long window_start_time;
		double set_point;
		boolean enable;
	} PidRelayDesc;

	// Descriptors for PID controlled variables
	PidRelayDesc pid_relay_descs[PID_RELAY_MAX_VARS];

#endif

/*******************************************************************************
 * Communication
 ******************************************************************************/
// USB Serial communication with user (usually with Instrumentino)
SerialCommand serial_command(Serial);

// data packet const header for synchronization
uint8_t packet_const_header[4] = {0xA5,0xA5,0xA5,0xA5};

// Channels registered for data acquisition
RegisteredChannelDesc registered_channels[MAX_REGISTERED_CHANNELS];
int registered_channels_num = 0;

// Variables for correctly timing sent packets are inside a DataBlock
// Each time we start a new acquisition block, we reset the variables.
// All t_XXX variables in the code are relative to the block's t_zero
// All time variables are expressed in milliseconds
uint32_t millis_at_t_zero = 0;
boolean t_zero_set = false;
uint32_t t_next_sent_packet = 0;

// Counters
int cnt_missed_samples = 0;
int cnt_missed_packets = 0;

// A buffer for sending data packets and pointers inside of it.
uint8_t data_packet[MAX_DATA_PACKET];
DataPacketHeader* data_packet_header = (DataPacketHeader*)data_packet;
DataBlockHeader* data_block_header_1 = (DataBlockHeader*)(&data_packet_header[1]);

/*******************************************************************************
 * Help functions
 ******************************************************************************/

/***
 * Get millis relative to t_zero.
 */
uint32_t t_now() {
	return millis() - millis_at_t_zero;
}

/***
 * Get the channel descriptor according to channel type name.
 *
 * ch_type_name: The channel type to check.
 *
 * Return: The found channel type descriptor.
 */
ChannelTypeDesc* get_ch_type_desc(char ch_type_name) {
	int i;

	for (i = 0; i < channel_types_num; i++) {
		if (ch_type_name == channel_types[i].name) {
			return &channel_types[i];
		}
	}

	// If reached here, it was not found.
	return NULL;
}

/***
 * Initialize data packets creation.
 */
void init_data_packets() {
	int i;

	// Tell the registered channels to prepare a sample for the next packet
	for (i = 0; i < registered_channels_num; i++) {
		registered_channels[i].ready_datapoints = 0;
		registered_channels[i].t_next_sample = t_next_sent_packet;
	}

	// Prepare the data packet buffer
	memcpy(data_packet_header->header.const_header, packet_const_header, sizeof(packet_const_header));
	data_packet_header->header.type = DATA_PACKET;

	// Schedule the next packet to be after all channels have filled their data blocks
	t_next_sent_packet += DATA_PACKETS_SAMPLING_PERIOD_MS;
}

/***
 * Tend to registered channels and add measurements if necessary.
 * Also send data packets when the time comes.
 */
void tend_to_registered_channels() {
	int i, j, sample_in_data_block;
	uint32_t value;
	uint32_t cur_time;
	RegisteredChannelDesc* reg_ch_desc;
	boolean missed_samples = false;
	DataBlockHeader* data_block_header;
	uint8_t* data_block;

	// Check if we are ready to start sending
	if (registered_channels_num == 0 || t_zero_set != true) {
		return;
	}

	// Set the current sample time
	cur_time = t_now();

	// Sample channels if necessary
	for (i = 0; i < registered_channels_num; i++) {
		reg_ch_desc = &registered_channels[i];

		// Do we need to sample now?
		if (cur_time < reg_ch_desc->t_next_sample) {
			// No need for a sample at the moment.
			continue;
		} else {

			// Check if we missed samples and invalidate this packet if we did.
			reg_ch_desc->t_next_sample += reg_ch_desc->sampling_period_ms;
			if (reg_ch_desc->t_next_sample < cur_time) {
				missed_samples = true;
				break;
			}

			// Sample once
			if (reg_ch_desc->type_desc->read_func != NULL) {
				value = reg_ch_desc->type_desc->read_func(reg_ch_desc->ch_num);
			} else {
				value = 0;
			}

			// Add the sample to the data block, byte by byte (big-endian style).
			// Don't over-fill in case the block is full.
			if (reg_ch_desc->ready_datapoints < reg_ch_desc->max_samples_num) {
				sample_in_data_block = reg_ch_desc->ready_datapoints * reg_ch_desc->bytes_per_datapoint;
				for (j = 0; j < reg_ch_desc->bytes_per_datapoint; j++) {
					reg_ch_desc->data_block[sample_in_data_block + reg_ch_desc->bytes_per_datapoint - 1 - j] = value&0xFF;
					value = value>>8;
				}
				reg_ch_desc->ready_datapoints++;
			}
		}
	}

	// Update counters
	if (missed_samples) {
		cnt_missed_samples++;

		// Schedule the next packet.
		while (t_next_sent_packet < cur_time + DATA_PACKETS_SAMPLING_PERIOD_MS) {
			t_next_sent_packet += DATA_PACKETS_SAMPLING_PERIOD_MS;
			cnt_missed_packets++;
		}
		init_data_packets();
	}

	// Send a packet if we're ready
	if (cur_time > t_next_sent_packet) {
		// Init data block pointers
		data_block_header = data_block_header_1;
		data_block = (uint8_t*)(&data_block_header[1]);

		// Init data packet header
		data_packet_header->header.packet_length = sizeof(DataPacketHeader);
		data_packet_header->relative_start_timestamp = cur_time;
		data_packet_header->num_of_blocks = 0;

		// Prepare the data blocks
		for (i = 0; i < registered_channels_num; i++) {
			reg_ch_desc = &registered_channels[i];

			// Copy data to the outgoing packet if channel is ready
			if (reg_ch_desc->ready_datapoints == reg_ch_desc->max_samples_num) {
				data_block_header->id = i;
				data_block_header->length = reg_ch_desc->data_block_len;
				memcpy(data_block, reg_ch_desc->data_block, reg_ch_desc->data_block_len);

				// Update data packet header
				data_packet_header->num_of_blocks++;
				data_packet_header->header.packet_length += (sizeof(DataBlockHeader) + data_block_header->length);

				// Init the channel descriptor
				reg_ch_desc->ready_datapoints = 0;

				// Advance data block pointers
				data_block_header = (DataBlockHeader*)(data_block + data_block_header->length);
				data_block = (uint8_t*)(&data_block_header[1]);
			}
		}

		// Transmit the packet
		serial_command.write(data_packet, data_packet_header->header.packet_length);

		// Schedule the next sent data packet
		t_next_sent_packet += DATA_PACKETS_SAMPLING_PERIOD_MS;
	}

}

/*******************************************************************************
 * Command handlers - These functions are called when their respective command
 * was issued by the user
 ******************************************************************************/

/***
 * PING
 *
 * Used for communications check. Answer with a simple 'pong' string
 */
void cmd_ping(SerialCommand this_scmd) {
	uint8_t packet[100];
	PacketHeader* general_header = (PacketHeader*)packet;
	uint8_t* reply = (uint8_t*)(&general_header[1]);
	char reply_string[5] = "PONG";

	// Prepare reply packet
	memcpy(general_header->const_header, packet_const_header, sizeof(packet_const_header));
	general_header->type = STRING_PACKET;
	memcpy(reply, reply_string, strlen(reply_string));
	general_header->packet_length = sizeof(PacketHeader) + strlen(reply_string);

	// Transmit reply the packet
	serial_command.write(packet, general_header->packet_length);
}

/***
 * ACQUIRE:START
 *
 * Start an acquisition block, so start sending data from registered channels.
 * Adjust the real-time clock to 0 so we can time our measurements that are sent.
 * A block can't be longer than 10 days because millis() will overflow (32 bit counter).
 */
void cmd_acquire_start(SerialCommand this_scmd) {
	// Set t_zero to be now.
	millis_at_t_zero = millis();
	t_zero_set = true;

	// Initialize data packets related timers
	t_next_sent_packet = 0 + DATA_PACKETS_SAMPLING_PERIOD_MS;

	init_data_packets();
}

/***
 * ACQUIRE:STOP
 *
 * Stop an acquisition block, so stop sending data from registered channels.
 */
void cmd_acquire_stop(SerialCommand this_scmd) {
	t_zero_set = false;
}

/***
 * CH:REGISTER <pin=D0|A0|...>, <sampling_rate>, <bytes_per_datapoint>
 *
 * Register a channel for data acquisition.
 * The data is sent in binary form together with values from other registered channels.
 * The value can be 1|0 for digital pins (for HIGH & LOW) or a native analog value.
 *
 * pin:					The pin's name, e.g. D0, A0, etc.
 * sampling_rate:		How often should the pin be read.
 * bytes_per_datapoint:	How many bytes are needed for a single data point. This is optional and is mainly relevant for bus cahnnels (I2C, SPI, etc.)
 */
void cmd_ch_register(SerialCommand this_scmd) {
	char *arg;
	int ch_num, sampling_rate, bytes_per_datapoint;
	ChannelTypeDesc* ch_type_desc;
	RegisteredChannelDesc* reg_ch_desc;
	boolean isInput;

	// get and check ch_type
	if (!(arg = this_scmd.next())) return;
	ch_type_desc = get_ch_type_desc(arg[0]);
	if (!ch_type_desc) return;

	// get ch_num
	ch_num = atol(&arg[1]);

	// get sampling_rate
	if (!(arg = this_scmd.next())) return;
	sampling_rate = atol(arg);

	// get bytes_per_datapoint
	if (ch_type_desc->bytes_per_datapoint != 0) {
		bytes_per_datapoint = ch_type_desc->bytes_per_datapoint;
	} else {
		if (!(arg = this_scmd.next())) return;
		bytes_per_datapoint = atol(&arg[1]);
	}

	// Add the channel to the registered channels list.
	reg_ch_desc = &registered_channels[registered_channels_num];
	reg_ch_desc->type_desc = ch_type_desc;
	reg_ch_desc->ch_num = ch_num;
	reg_ch_desc->sampling_rate = sampling_rate;
	reg_ch_desc->sampling_period_ms = 1000 / sampling_rate;
	reg_ch_desc->bytes_per_datapoint = bytes_per_datapoint;

	// Allocate memory for the acquired data
	if (sampling_rate > DATA_PACKETS_SAMPLING_RATE) {
		reg_ch_desc->max_samples_num = sampling_rate / DATA_PACKETS_SAMPLING_RATE;
	} else {
		reg_ch_desc->max_samples_num = 1;
	}
	reg_ch_desc->data_block_len = bytes_per_datapoint * reg_ch_desc->max_samples_num;
	reg_ch_desc->data_block = (uint8_t*)malloc(reg_ch_desc->data_block_len);
	if (reg_ch_desc->data_block == 0) return;

	// Schedule the next sample
	reg_ch_desc->t_next_sample = t_next_sent_packet;

	// If successful, update the registered channels number
	registered_channels_num++;
}

/***
 * CH:DIR <channel=D0|D1|...>, <direction=IN|OUT>
 *
 * Set direction of a channel to output or input.
 *
 * channel:		The channel's name, e.g. D0, D1, etc.
 * direction:	IN or OUT for input and output.
 */
void cmd_ch_dir(SerialCommand this_scmd) {
	char *arg;
	int ch_num, i;
	ChannelTypeDesc* ch_type_desc;
	char* direction;
	boolean isInput;

	// get and check ch_type
	if (!(arg = this_scmd.next())) return;
	ch_type_desc = get_ch_type_desc(arg[0]);
	if (!ch_type_desc) return;

	// get ch_num
	ch_num = atol(&arg[1]);

	// get direction
	if (!(arg = this_scmd.next())) return;
	direction = arg;

	if (strcmp(direction, "IN") == 0) {
		isInput = true;
	} else if (strcmp(direction, "OUT") == 0) {
		isInput = false;
	} else {
		return;
	}

	// set the direction
	if (ch_type_desc->direction_func != NULL) {
		ch_type_desc->direction_func(ch_num, isInput);
	}
}

/***
 * CH:WRITE <pin=D0|A0|...>, <value1>, <value2>,...
 *
 * Write to a channel one or more values. For digital pins, 1 is HIGH and 0 is LOW.
 *
 * channel:	The channel's name, e.g. D0, D1, etc.
 * values:	Each value is up to 32 bit. Several values can be written to bus channels.
 */
void cmd_ch_write(SerialCommand this_scmd) {
	char *arg;
	int ch_num;
	uint32_t values[CH_WRITE_MAX_VALUES];
	int values_num = 0;
	ChannelTypeDesc* ch_type_desc;
	boolean isInput;

	// get and check ch_type
	if (!(arg = this_scmd.next())) return;
	ch_type_desc = get_ch_type_desc(arg[0]);
	if (!ch_type_desc) return;

	// get ch_num
	ch_num = atol(&arg[1]);

	// get the values to write
	for (arg = this_scmd.next(), values_num = 0; arg != NULL; arg = this_scmd.next()) {
		values[values_num] = atol(arg);
	}

	// set the direction
	if (ch_type_desc->write_func != NULL) {
		ch_type_desc->write_func(ch_num, values, values_num);
	}
}

#ifdef USE_ARDUINO_PID
/***
 * PID:RELAY:INIT <id=0|1|...> <input pin=A0|A1|...> <output_pin=D0|D1|...> <window_size> <k_p> <k_i> <k_d>
 *
 * Create a PID variable that controls a relay.
 *
 * id:				An identifier for this PID variable in order to support several simultaneous variables.
 * 					The id has to be set here by the user and be used in later PID related commands.
 * input pin:		The analog input pin through which the analog data is read (to be fed into the PID algorithm).
 * output pin:		The digital output pin that controls a relay. Opening the relay activates something
 * 					(e.g. a heating film) that affects the analog input reading (e.g. a thermometer).
 * window size:		The window size in miliseconds for the PID algorithm.
 * k_p, k_i, k_d:	The P, I and D parameters for the PID calculation.
 *
 * For more information: http://playground.arduino.cc/Code/PIDLibraryRelayOutputExample
 */
void cmd_pid_relay_init(SerialCommand this_scmd) {
	char *arg;
	int id, pin_anal_in, pin_digi_out, window_size;
	char pin_type;
	double k_p, k_i, k_d;

	if (!(arg = this_scmd.next())) return;
	id = atol(arg);
	if (id < 0 || id >= PID_RELAY_MAX_VARS) return;

	if (!(arg = this_scmd.next())) return;
	pin_type = arg[0];
	if (pin_type != 'A') return;
	pin_anal_in = atol(&arg[1]);

	if (!(arg = this_scmd.next())) return;
	pin_type = arg[0];
	if (pin_type != 'D') return;
	pin_digi_out = atol(&arg[1]);

	if (!(arg = this_scmd.next())) return;
	window_size = atol(arg);

	if (!(arg = this_scmd.next())) return;
	k_p = atof(arg);

	if (!(arg = this_scmd.next())) return;
	k_i = atof(arg);

	if (!(arg = this_scmd.next())) return;
	k_d = atof(arg);


	// Init the PID variable
	PidRelayDesc* pid_desc = &pid_relay_descs[id];
	pid_desc->pin_anal_in = pin_anal_in;
	pid_desc->pin_digi_out = pin_digi_out;
	pid_desc->window_size = window_size;
	pid_desc->handler = new PID(&pid_desc->input_var, &pid_desc->output_var, &pid_desc->set_point, k_p, k_i, k_d, DIRECT);
	pid_desc->handler->SetOutputLimits(0, pid_desc->window_size);
	pid_desc->enable = false;
}

/***
 * PID:RELAY:TUNE <k_p>,<k_i>,<k_d>
 *
 * Set the PID tuning parameters.
 *
 * id:				An identifier for this PID variable in order to support several simultaneous variables.
 * 					This is the same id that was recevied in the PID:RELAY:INIT command.
 * k_p, k_i, k_d:	The P, I and D parameters for the PID calculation.
 *
 */
void cmd_pid_relay_tune(SerialCommand this_scmd) {
	char *arg;
	int id;
	double k_p, k_i, k_d;

	if (!(arg = this_scmd.next())) return;
	id = atol(arg);
	if (id < 0 || id >= PID_RELAY_MAX_VARS) return;

	if (!(arg = this_scmd.next())) return;
	k_p = atof(arg);

	if (!(arg = this_scmd.next())) return;
	k_i = atof(arg);

	if (!(arg = this_scmd.next())) return;
	k_d = atof(arg);

	PidRelayDesc* pid_desc = &pid_relay_descs[id];
	pid_desc->handler->SetTunings(k_p, k_i, k_d);
}

/***
 * PID:RELAY:SET <id>,<set_point>
 *
 * Start controlling a relay using a PID variable
 *
 * id:			An identifier for this PID variable in order to support several simultaneous variables.
 * 				This is the same id that was received in the PID:RELAY:INIT command.
 * set_point:	The desired value to be read from the input variable.
 */
void cmd_pid_relay_set(SerialCommand this_scmd) {
	char *arg;
	int id, set_point;

	if (!(arg = this_scmd.next())) return;
	id = atol(arg);
	if (id < 0 || id >= PID_RELAY_MAX_VARS) return;

	if (!(arg = this_scmd.next())) return;
	set_point = atol(arg);

	PidRelayDesc* pid_desc = &pid_relay_descs[id];
	pid_desc->set_point = set_point;
}

/***
 * PID:RELAY:ENABLE <id>,<enable=HIGH|LOW>
 *
 * Start/Stop the control loop.
 *
 * id:		An identifier for this PID variable in order to support several simultaneous variables.
 * 			This is the same id that was recevied in the PID:RELAY:INIT command.
 * enable:	Enable/disable (HIGH or LOW) the PID feedback loop.
 */
void cmd_pid_relay_enable(SerialCommand this_scmd) {
	char *arg, *enable;
	int id;

	if (!(arg = this_scmd.next())) return;
	id = atol(arg);
	if (id < 0 || id >= PID_RELAY_MAX_VARS) return;

	if (!(arg = this_scmd.next())) return;
	enable = arg;

	PidRelayDesc* pid_desc = &pid_relay_descs[id];
	pid_desc->window_start_time = millis();

	// turn the PID on/off
	if (strcmp(enable, "HIGH") == 0) {
		pid_desc->enable = true;
		pid_desc->handler->SetMode(AUTOMATIC);
	} else if (strcmp(enable, "LOW") == 0) {
		pid_desc->enable = false;
		pid_desc->handler->SetMode(MANUAL);
		digitalWrite(pid_desc->pin_digi_out, LOW);
	} else {
		return;
	}
}
#endif

/*******************************************************************************
 * Main functions
 ******************************************************************************/
/***
 * The setup function is called once at startup of the sketch
 */
void setup() {
	// Init serial communication
	Serial.begin(SERIAL0_BAUD);

	// Setup callbacks for SerialCommand commands
	serial_command.addCommand("PING",			cmd_ping);
	serial_command.addCommand("CH:DIR",			cmd_ch_dir);
	serial_command.addCommand("CH:WRITE",		cmd_ch_write);
	serial_command.addCommand("CH:REGISTER",	cmd_ch_register);
	serial_command.addCommand("ACQUIRE:START",	cmd_acquire_start);
	serial_command.addCommand("ACQUIRE:STOP",	cmd_acquire_stop);
#ifdef USE_ARDUINO_PID
	serial_command.addCommand("PID:RELAY:INIT",	cmd_pid_relay_init);
	serial_command.addCommand("PID:RELAY:SET",	cmd_pid_relay_set);
	serial_command.addCommand("PID:RELAY:TUNE",	cmd_pid_relay_tune);
	serial_command.addCommand("PID:RELAY:ENABLE",	cmd_pid_relay_enable);
#endif
}

/***
 * The loop function is called in an endless loop
 */
void loop() {
	int i;
	uint32_t curr_millis;

	// Tend to registered channels
	tend_to_registered_channels();

	// Tend to serial communication
	serial_command.readSerial();

#ifdef USE_ARDUINO_PID
	// Take care PID-relay variables
	for (i = 0; i < PID_RELAY_MAX_VARS; i++) {
		if (pid_relay_descs[i].enable) {
			pid_relay_descs[i].input_var = analogRead(pid_relay_descs[i].pin_anal_in);
			pid_relay_descs[i].handler->Compute();

			// turn relay on/off according to the PID output
			curr_millis = millis();
			if (curr_millis - pid_relay_descs[i].window_start_time > pid_relay_descs[i].window_size) {
				//time to shift the Relay Window
				pid_relay_descs[i].window_start_time += pid_relay_descs[i].window_size;
			}
			if (pid_relay_descs[i].output_var > curr_millis - pid_relay_descs[i].window_start_time) {
				digitalWrite(pid_relay_descs[i].pin_digi_out, HIGH);
			}
			else {
				digitalWrite(pid_relay_descs[i].pin_digi_out, LOW);
			}
		}
	}
#endif
}
