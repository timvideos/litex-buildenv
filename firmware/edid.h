/*
 * Copyright 2015 / TimVideo.us
 * Copyright 2015 / EnjoyDigital
 * Copyright 2017 Joel Addison <joel@addison.net.au>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 */

#ifndef __EDID_H
#define __EDID_H

#define DESCRIPTOR_DUMMY 0x10
#define DESCRIPTOR_MONITOR_NAME 0xFC
#define DESCRIPTOR_MONITOR_RANGE 0xFD

#define MAX_DESCRIPTOR_DATA_LEN 13

#define EDID_SECONDARY_MODE_OFF -1

#define REFRESH_RATE_PRINTF "%u.%02u"
#define REFRESH_RATE_PRINTF_ARGS(x) \
	x/100, x%100

/* Timing flags */
#define EDID_HSYNC_POS		0b00000010
#define EDID_HSYNC_NEG		0b00000000
#define EDID_VSYNC_POS		0b00000100
#define EDID_VSYNC_NEG		0b00000000
#define EDID_INTERLACE		0b10000000
#define EDID_DIGITAL		0b00011000

static const struct {
        const char* string;
        unsigned long flag;
} timing_mode_flags[] = {
        { "+HSync", EDID_HSYNC_POS },
        { "-HSync", EDID_HSYNC_NEG },
        { "+VSync", EDID_VSYNC_POS },
        { "-VSync", EDID_VSYNC_NEG },
        { "Interlace", EDID_INTERLACE },
        { 0, 0 }
};

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
	const struct video_timing *timing,
	const struct video_timing *secondary_timing);

unsigned calculate_refresh_rate(const struct video_timing* video_mode);


#endif
