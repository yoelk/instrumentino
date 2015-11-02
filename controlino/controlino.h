#ifndef _controlino_h_
#define _controlino_h_

#ifdef __cplusplus
extern "C" {
#endif
void loop();
void setup();
#ifdef __cplusplus
} // extern "C"
#endif

#include "controlino_cfg.h"
#include "boards.h"
#include "stdint.h"
#include "Libraries/SerialCommand/SerialCommand.h"

/*******************************************************************************
 * Channel definitions
 ******************************************************************************/
// The maximal number of values to write in a single CH:WRITE command
#define CH_WRITE_MAX_VALUES	10

// For bus channels (I2C, SPI, etc.) where the number of bytes per datapoint depends on the connected device
#define CH_BYTES_PER_DATAPOINT_UNKNOWN	0

// The list of pins to be read when sending periodic data packets
#define MAX_REGISTERED_CHANNELS	(NUM_DIGITAL_PINS + NUM_ANALOG_INPUTS)

// A channel descriptor
typedef struct {
	char name; // The channel type's name
	int bytes_per_datapoint; // The number of bytes needed to describe a single datapoint
	uint32_t (*read_func) (int ch_num); // Read function for this channel
	void (*write_func) (int ch_num, uint32_t values[], int values_num); // Write function for this channel
	void (*direction_func) (int ch_num, boolean isInput); // Direction setting function for this channel
} ChannelTypeDesc;

extern ChannelTypeDesc channel_types[];
extern int channel_types_num;

/*******************************************************************************
 * The controlino-instrumentino data protocol
 *
 * A data packet (Controller->Instrumentino) has the following form (with sizes in bytes):
 * [const_header, 4][type, 1][packet_length, 2]    <- general packet header
 * [relative_start_timestamp, 4]                   <- data packet header
 * [num_of_blocks, 2]
 * [block1_id][block1_length, 2][block1_data]
 * [block2_id][block2_length, 2][block2_data] ...
 ******************************************************************************/

// Packet types (controlino->instrumentino)
typedef enum {
	DATA_PACKET = 0,
	STRING_PACKET = 1
} PacketType;

// data packet full header
typedef struct {
	uint8_t const_header[4];
	uint8_t type;
	uint16_t packet_length;
} PacketHeader;

// data packet full header
typedef struct {
	PacketHeader header;
	uint32_t relative_start_timestamp;
	uint16_t num_of_blocks;
} DataPacketHeader;

// data block header in a data packet
typedef struct {
	uint8_t id;
	uint16_t length;
} DataBlockHeader;

/*******************************************************************************
 * Communication definitions
 ******************************************************************************/
// The serial baudrate to use.
#define SERIAL0_BAUD	115200

// The biggest data packet we allow
#define MAX_DATA_PACKET	500

// How often should we send data packets (in Hz)
#define DATA_PACKETS_SAMPLING_RATE		10
#define DATA_PACKETS_SAMPLING_PERIOD_MS	(1000 / DATA_PACKETS_SAMPLING_RATE)

// A registered channel descriptor
// Some redundancy exists to avoid on-the-fly calculations
typedef struct {
	// Channel characteristics
	ChannelTypeDesc* type_desc;	// The channel type descriptor
	int ch_num;					// The channel's number (e.g. pin number)
	int bytes_per_datapoint;	// The number of bytes needed to describe a single datapoint
	int sampling_rate;			// In Hz. If set to CH_SAMPLING_RATE_ONCE then read the value only once and remove it from the list
	int sampling_period_ms;		// The sampling period in milliseconds.

	// Data block
	int data_block_len;			// How long is the data block (in bytes)
	int max_samples_num;		// How long is the data block (in samples)
	uint8_t* data_block;		// The data block is allocated once the sampling rate is known

	// Timing variables
	int ready_datapoints;		// The number of datapoints ready to be sent
	long t_next_sample;			// The next time in which we need to sample the channel.
} RegisteredChannelDesc;


#endif // _controlino_H_
