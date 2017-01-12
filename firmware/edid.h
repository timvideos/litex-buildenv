#ifndef __EDID_H
#define __EDID_H

#define DESCRIPTOR_DUMMY 0x10
#define DESCRIPTOR_MONITOR_NAME 0xFC
#define DESCRIPTOR_MONITOR_RANGE 0xFD

#define MAX_DESCRIPTOR_DATA_LEN 13

/* Timing flags */
#define TIMING_H_SYNC_POS	0b00000010
#define TIMING_H_SYNC_NEG	0b00000000
#define TIMING_V_SYNC_POS	0b00000100
#define TIMING_V_SYNC_NEG	0b00000000
#define TIMING_INTERLACED	0b10000000
#define TIMING_DIG_SEP		0b00011000

struct video_timing {
	unsigned int pixel_clock; /* in tens of kHz */

	unsigned int h_active;
	unsigned int h_blanking;
	unsigned int h_sync_offset;
	unsigned int h_sync_width;

	unsigned int v_active;
	unsigned int v_blanking;
	unsigned int v_sync_offset;
	unsigned int v_sync_width;

	unsigned int flags;

	unsigned int established_timing;
	const char* comment;
};

int validate_edid(const void *buf);
void generate_edid(void *out,
	const char mfg_name[3], const char product_code[2], int year,
	const char *name,
	const struct video_timing *timing);

unsigned calculate_refresh_rate(const struct video_timing* video_mode);


#endif
