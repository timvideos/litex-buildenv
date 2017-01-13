/*
 * Copyright 2015 / TimVideo.us
 * Copyright 2015 / EnjoyDigital
 * Copyright 2016 Joel Stanley <joel@jms.id.au>
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

#include <stdint.h>
#include <string.h>

#include "edid.h"

struct edid {
	uint8_t header[8];

	uint8_t manufacturer[2];
	uint8_t product_code[2];
	uint8_t serial_number[4];
	uint8_t manufacture_week;
	uint8_t manufacture_year;

	uint8_t edid_version;
	uint8_t edid_revision;

	uint8_t video_input;
	uint8_t h_image_size;
	uint8_t v_image_size;
	uint8_t gamma;
	uint8_t feature_support;

	uint8_t cc_rg_l;
	uint8_t cc_bw_l;
	uint8_t cc_rx_h;
	uint8_t cc_ry_h;
	uint8_t cc_gx_h;
	uint8_t cc_gy_h;
	uint8_t cc_bx_h;
	uint8_t cc_by_h;
	uint8_t cc_wx_h;
	uint8_t cc_wy_h;

	uint8_t est_timings_1;
	uint8_t est_timings_2;
	uint8_t rsv_timings;

	uint8_t timings_std[16];

	uint8_t data_blocks[4][18];

	uint8_t ext_block_count;

	uint8_t checksum;
} __attribute__((packed));

struct edid_timing {
	uint8_t pixel_clock[2];

	uint8_t h_active_l;
	uint8_t h_blanking_l;
	uint8_t h_active_blanking_h;

	uint8_t v_active_l;
	uint8_t v_blanking_l;
	uint8_t v_active_blanking_h;

	uint8_t h_sync_offset_l;
	uint8_t h_sync_width_l;
	uint8_t v_sync_offset_width_l;
	uint8_t hv_sync_offset_width_h;

	uint8_t h_image_size_l;
	uint8_t v_image_size_l;
	uint8_t hv_image_size_h;

	uint8_t h_border;
	uint8_t v_border;

	uint8_t flags;
} __attribute__((packed));

struct edid_descriptor {
	uint8_t flag0;
	uint8_t flag1;
	uint8_t flag2;
	uint8_t data_type;
	uint8_t flag3;
	uint8_t data[MAX_DESCRIPTOR_DATA_LEN];
} __attribute__((packed));

struct monitor_range_data {
	uint8_t min_vertical_field_rate;
	uint8_t max_vertical_field_rate;
	uint8_t min_horizontal_line_rate;
	uint8_t max_horizontal_line_rate;
	uint8_t max_pixel_clock_rate;
	uint8_t extended_timing_type;
	union {
		struct {
			uint8_t reserved;
			uint8_t start_frequency;
			uint8_t gtf_c[2];
			uint8_t gtf_m;
			uint8_t gtf_k;
			uint8_t gtf_j;
		};
		uint8_t padding[7];
	};
} __attribute__((packed));

static const char correct_header[8] = {0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00};

static uint8_t compute_checksum(struct edid *e)
{
	uint8_t *p = (uint8_t *)e;
	uint8_t sum;
	int i;

	sum = 0;
	for(i=0;i<127;i++)
		sum += p[i];
	return -sum;
}

int validate_edid(const void *buf)
{
	struct edid *e = (struct edid *)buf;

	if(memcmp(e->header, correct_header, 8) != 0)
		return 0;
	if(compute_checksum(e) != e->checksum)
		return 0;
	return 1;
}

static void generate_edid_timing(uint8_t *data_block, const struct video_timing *timing)
{
	struct edid_timing *t = (struct edid_timing *)data_block;
	unsigned int h_image_size, v_image_size;

	t->pixel_clock[0] = timing->pixel_clock & 0xff;
	t->pixel_clock[1] = timing->pixel_clock >> 8;

	t->h_active_l = timing->h_active & 0xff;
	t->h_blanking_l = timing->h_blanking & 0xff;
	t->h_active_blanking_h = ((timing->h_active >> 8) << 4) | (timing->h_blanking >> 8);

	t->v_active_l = timing->v_active & 0xff;
	t->v_blanking_l = timing->v_blanking & 0xff;
	t->v_active_blanking_h = ((timing->v_active >> 8) << 4) | (timing->v_blanking >> 8);

	t->h_sync_offset_l = timing->h_sync_offset & 0xff;
	t->h_sync_width_l = timing->h_sync_width & 0xff;
	t->v_sync_offset_width_l = timing->v_sync_offset & 0xff;
	t->hv_sync_offset_width_h = ((timing->h_sync_offset >> 8) << 6) | ((timing->h_sync_width >> 8) << 4)
	 | ((timing->v_sync_offset >> 8) << 2) | (timing->v_sync_width >> 8);

	h_image_size = 10*timing->h_active/64;
	v_image_size = 10*timing->v_active/64;
	t->h_image_size_l = h_image_size & 0xff;
	t->v_image_size_l = v_image_size & 0xff;
	t->hv_image_size_h = ((h_image_size >> 8) << 4) | (v_image_size >> 8);

	t->h_border = 0;
	t->v_border = 0;

	t->flags = timing->flags;
}

static void set_descriptor_header(struct edid_descriptor *d, uint8_t data_type)
{
	d->flag0 = d->flag1 = d->flag2 = d->flag3 = 0;
	d->data_type = data_type;
}

static void generate_descriptor_padding(struct edid_descriptor *d, uint8_t start_pos)
{
	if (start_pos >= MAX_DESCRIPTOR_DATA_LEN) return;

	d->data[start_pos++] = 0x0a;
	for(;start_pos<MAX_DESCRIPTOR_DATA_LEN;start_pos++)
		d->data[start_pos] = 0x20;
}

static void generate_monitor_name(uint8_t *data_block, const char *name)
{
	struct edid_descriptor *d = (struct edid_descriptor *)data_block;
	int i;

	set_descriptor_header(d, DESCRIPTOR_MONITOR_NAME);

	for(i=0;i<MAX_DESCRIPTOR_DATA_LEN;i++) {
		if(!name[i])
			break;
		d->data[i] = name[i];
	}

	generate_descriptor_padding(d, i);
}

static void generate_monitor_range_descriptor(uint8_t *data_block,
		const struct video_timing *timing)
{
	struct edid_descriptor *d = (struct edid_descriptor *)data_block;
	struct monitor_range_data *data = (struct monitor_range_data *)d->data;

	set_descriptor_header(d, DESCRIPTOR_MONITOR_RANGE);

	// Fixme: set from mode?
	data->min_vertical_field_rate = 50;  // 50Hz
	data->max_vertical_field_rate = 60;  // 60Hz
	data->min_horizontal_line_rate = 31; // 720p50 is 37.05kHz
	data->max_horizontal_line_rate = 68; // 1080p60 is 67.08kHz
	//TODO: Set this to be ~5Mhz above current dotclock
	data->max_pixel_clock_rate = 8; // 80 MHz => 80 / 10 = 8
	data->extended_timing_type = 0x00;

	generate_descriptor_padding(d, 6);
}

static void generate_unused(uint8_t *data_block)
{
	struct edid_descriptor *d = (struct edid_descriptor *)data_block;

	memset(d, 0, sizeof(struct edid_descriptor));
	d->data_type = DESCRIPTOR_DUMMY;
}

void generate_edid(void *out,
	const char mfg_name[3], const char product_code[2], int year,
	const char *name,
	const struct video_timing *timing,
	const struct video_timing *secondary_timing)
{
	struct edid *e = (struct edid *)out;
	int i, j, k, db;

	memcpy(e->header, correct_header, 8);

	i = mfg_name[0] - 'A' + 1;
	j = mfg_name[1] - 'A' + 1;
	k = mfg_name[2] - 'A' + 1;
	e->manufacturer[0] = (i << 2) | (j >> 3);
	e->manufacturer[1] = ((j & 0x07) << 5) | k;
	e->product_code[0] = product_code[0]; e->product_code[1] = product_code[1];
	e->serial_number[0] = e->serial_number[1] = e->serial_number[2] = e->serial_number[3] = 0;
	e->manufacture_week = 0;
	e->manufacture_year = year - 1990;

	e->edid_version = 1;
	e->edid_revision = 3;

	e->video_input = 0x80; /* digital */
	e->h_image_size = timing->h_active/64;
	e->v_image_size = timing->v_active/64;
	e->gamma = 0x50; // 1.8 => (gamma * 100) - 100
	e->feature_support = 0x06;

	e->cc_rg_l = 0;
	e->cc_bw_l = 0;
	e->cc_rx_h = 0;
	e->cc_ry_h = 0;
	e->cc_gx_h = 0;
	e->cc_gy_h = 0;
	e->cc_bx_h = 0;
	e->cc_by_h = 0;
	e->cc_wx_h = 0;
	e->cc_wy_h = 0;

	e->est_timings_1 = timing->established_timing >> 8;
	e->est_timings_2 = timing->established_timing & 0xff;
	e->rsv_timings = 0;
	memset(e->timings_std, 0x01, 16);

	db = 0;
	generate_edid_timing(e->data_blocks[db++], timing);
	if (secondary_timing != NULL)
		generate_edid_timing(e->data_blocks[db++], secondary_timing);
	generate_monitor_name(e->data_blocks[db++], name);
	generate_monitor_range_descriptor(e->data_blocks[db++], timing);
	if (secondary_timing == NULL)
		generate_unused(e->data_blocks[db++]);

	e->ext_block_count = 0;

	e->checksum = compute_checksum(e);
}

/**
 * Calculate refresh rate for a video timing mode.
 * Rate is in Hz * 100, which allows for two decimal places of precision.
 */
unsigned calculate_refresh_rate(const struct video_timing* mode)
{
	unsigned refresh_span = (mode->h_active + mode->h_blanking)*(mode->v_active + mode->v_blanking);
	uint64_t clock = mode->pixel_clock;
	clock *= 10000 * 100; // Multiply by 100 to get 2 decimal places
	unsigned refresh_rate = clock / refresh_span;
	return refresh_rate;
}
