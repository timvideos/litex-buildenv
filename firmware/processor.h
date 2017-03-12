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

#ifndef __PROCESSOR_H
#define __PROCESSOR_H

#include "edid.h"

#define PROCESSOR_MODE_DESCLEN 64

#define PROCESSOR_MODE_CUSTOM -1

enum {
	PROCESSOR_MODE_640_480_72,
	PROCESSOR_MODE_640_480_75,
	PROCESSOR_MODE_800_600_56,
	PROCESSOR_MODE_800_600_60,
	PROCESSOR_MODE_800_600_72,
	PROCESSOR_MODE_800_600_75,
	PROCESSOR_MODE_1024_768_60,
	PROCESSOR_MODE_1024_768_70,
	PROCESSOR_MODE_1024_768_75,
	PROCESSOR_MODE_720p_60,
	PROCESSOR_MODE_720p_50,
	PROCESSOR_MODE_1920_1080_30,
	PROCESSOR_MODE_1920_1080_60,
	PROCESSOR_MODE_720_480_60,
	PROCESSOR_MODE_720_576_50,

	PROCESSOR_MODE_COUNT
};

enum {
	VIDEO_IN_HDMI_IN0=0,
	VIDEO_IN_HDMI_IN1,
	VIDEO_IN_PATTERN
};

enum {
	VIDEO_OUT_HDMI_OUT0=0,
	VIDEO_OUT_HDMI_OUT1,
	VIDEO_OUT_ENCODER
};

extern int processor_mode;
extern int processor_secondary_mode;
int processor_h_active;
int processor_v_active;
int processor_refresh;
int processor_hdmi_out0_source;
int processor_hdmi_out1_source;
int processor_encoder_source;
char processor_buffer[16];

void processor_list_modes(char *mode_descriptors);
void processor_describe_mode(char *mode_descriptor, int mode);
void processor_init(int sec_mode);
void processor_start(int mode);
void processor_set_hdmi_out0_source(int source);
void processor_set_hdmi_out1_source(int source);
void processor_set_encoder_source(int source);
char* processor_get_source_name(int source);
void processor_update(void);
void processor_service(void);
struct video_timing* processor_get_custom_mode(void);
void processor_set_custom_mode(void);
void processor_set_secondary_mode(int mode);

#endif /* __PROCESSOR_H */
