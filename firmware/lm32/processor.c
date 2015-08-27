#include <stdio.h>
#include <stdlib.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <time.h>

#include "hdmi_in0.h"
#include "hdmi_in1.h"
#include "edid.h"
#include "pll.h"
#include "processor.h"

/* reference: http://martin.hinner.info/vga/timing.html */
static const struct video_timing video_modes[PROCESSOR_MODE_COUNT] = {
	{
		.pixel_clock = 3150,

		.h_active = 640,
		.h_blanking = 192,
		.h_sync_offset = 24,
		.h_sync_width = 40,

		.v_active = 480,
		.v_blanking = 40,
		.v_sync_offset = 9,
		.v_sync_width = 3,

		.established_timing = 0x0800
	},
	{
		.pixel_clock = 3150,

		.h_active = 640,
		.h_blanking = 200,
		.h_sync_offset = 16,
		.h_sync_width = 64,

		.v_active = 480,
		.v_blanking = 20,
		.v_sync_offset = 1,
		.v_sync_width = 3,

		.established_timing = 0x0400
	},
	{
		.pixel_clock = 3600,

		.h_active = 800,
		.h_blanking = 224,
		.h_sync_offset = 24,
		.h_sync_width = 72,

		.v_active = 600,
		.v_blanking = 25,
		.v_sync_offset = 1,
		.v_sync_width = 2,

		.established_timing = 0x0200
	},
	{
		.pixel_clock = 4000,

		.h_active = 800,
		.h_blanking = 256,
		.h_sync_offset = 40,
		.h_sync_width = 128,

		.v_active = 600,
		.v_blanking = 28,
		.v_sync_offset = 1,
		.v_sync_width = 4,

		.established_timing = 0x0100
	},
	{
		.pixel_clock = 5000,

		.h_active = 800,
		.h_blanking = 240,
		.h_sync_offset = 56,
		.h_sync_width = 120,

		.v_active = 600,
		.v_blanking = 66,
		.v_sync_offset = 37,
		.v_sync_width = 6,

		.established_timing = 0x0080
	},
	{
		.pixel_clock = 4950,

		.h_active = 800,
		.h_blanking = 256,
		.h_sync_offset = 16,
		.h_sync_width = 80,

		.v_active = 600,
		.v_blanking = 25,
		.v_sync_offset = 1,
		.v_sync_width = 3,

		.established_timing = 0x0040
	},
	{
		.pixel_clock = 6500,

		.h_active = 1024,
		.h_blanking = 320,
		.h_sync_offset = 24,
		.h_sync_width = 136,

		.v_active = 768,
		.v_blanking = 38,
		.v_sync_offset = 3,
		.v_sync_width = 6,

		.established_timing = 0x0008
	},
	{
		.pixel_clock = 7500,

		.h_active = 1024,
		.h_blanking = 304,
		.h_sync_offset = 24,
		.h_sync_width = 136,

		.v_active = 768,
		.v_blanking = 38,
		.v_sync_offset = 3,
		.v_sync_width = 6,

		.established_timing = 0x0004
	},
	{
		.pixel_clock = 7880,

		.h_active = 1024,
		.h_blanking = 288,
		.h_sync_offset = 16,
		.h_sync_width = 96,

		.v_active = 768,
		.v_blanking = 32,
		.v_sync_offset = 1,
		.v_sync_width = 3,

		.established_timing = 0x0002
	},
	{
		.pixel_clock = 7425,

		.h_active = 1280,
		.h_blanking = 370,
		.h_sync_offset = 220,
		.h_sync_width = 40,

		.v_active = 720,
		.v_blanking = 30,
		.v_sync_offset = 20,
		.v_sync_width = 5
	}
};

void processor_list_modes(char *mode_descriptors)
{
	int i;
	unsigned int refresh_span;
	unsigned int refresh_rate;

	for(i=0;i<PROCESSOR_MODE_COUNT;i++) {
		refresh_span = (video_modes[i].h_active + video_modes[i].h_blanking)*(video_modes[i].v_active + video_modes[i].v_blanking);
		refresh_rate = video_modes[i].pixel_clock*10000/refresh_span;
		sprintf(&mode_descriptors[PROCESSOR_MODE_DESCLEN*i],
			"%ux%u @%uHz", video_modes[i].h_active, video_modes[i].v_active, refresh_rate);
	}
}

static void fb_clkgen_write(int cmd, int data)
{
	int word;

	word = (data << 2) | cmd;
	hdmi_out0_driver_clocking_cmd_data_write(word);
	hdmi_out0_driver_clocking_send_cmd_data_write(1);
	while(hdmi_out0_driver_clocking_status_read() & CLKGEN_STATUS_BUSY);
}

static void fb_get_clock_md(unsigned int pixel_clock, unsigned int *best_m, unsigned int *best_d)
{
	unsigned int ideal_m, ideal_d;
	unsigned int bm, bd;
	unsigned int m, d;
	unsigned int diff_current;
	unsigned int diff_tested;

	ideal_m = pixel_clock;
	ideal_d = 5000;

	bm = 1;
	bd = 0;
	for(d=1;d<=256;d++)
		for(m=2;m<=256;m++) {
			/* common denominator is d*bd*ideal_d */
			diff_current = abs(d*ideal_d*bm - d*bd*ideal_m);
			diff_tested = abs(bd*ideal_d*m - d*bd*ideal_m);
			if(diff_tested < diff_current) {
				bm = m;
				bd = d;
			}
		}
	*best_m = bm;
	*best_d = bd;
}

static void fb_set_mode(const struct video_timing *mode)
{
	unsigned int clock_m, clock_d;

	fb_get_clock_md(mode->pixel_clock, &clock_m, &clock_d);

	hdmi_out0_fi_hres_write(mode->h_active);
	hdmi_out0_fi_hsync_start_write(mode->h_active + mode->h_sync_offset);
	hdmi_out0_fi_hsync_end_write(mode->h_active + mode->h_sync_offset + mode->h_sync_width);
	hdmi_out0_fi_hscan_write(mode->h_active + mode->h_blanking);
	hdmi_out0_fi_vres_write(mode->v_active);
	hdmi_out0_fi_vsync_start_write(mode->v_active + mode->v_sync_offset);
	hdmi_out0_fi_vsync_end_write(mode->v_active + mode->v_sync_offset + mode->v_sync_width);
	hdmi_out0_fi_vscan_write(mode->v_active + mode->v_blanking);

	hdmi_out0_fi_length_write(mode->h_active*mode->v_active*2);

	hdmi_out1_fi_hres_write(mode->h_active);
	hdmi_out1_fi_hsync_start_write(mode->h_active + mode->h_sync_offset);
	hdmi_out1_fi_hsync_end_write(mode->h_active + mode->h_sync_offset + mode->h_sync_width);
	hdmi_out1_fi_hscan_write(mode->h_active + mode->h_blanking);
	hdmi_out1_fi_vres_write(mode->v_active);
	hdmi_out1_fi_vsync_start_write(mode->v_active + mode->v_sync_offset);
	hdmi_out1_fi_vsync_end_write(mode->v_active + mode->v_sync_offset + mode->v_sync_width);
	hdmi_out1_fi_vscan_write(mode->v_active + mode->v_blanking);

	hdmi_out1_fi_length_write(mode->h_active*mode->v_active*2);

	fb_clkgen_write(0x1, clock_d-1);
	fb_clkgen_write(0x3, clock_m-1);
	hdmi_out0_driver_clocking_send_go_write(1);
	while(!(hdmi_out0_driver_clocking_status_read() & CLKGEN_STATUS_PROGDONE));
	while(!(hdmi_out0_driver_clocking_status_read() & CLKGEN_STATUS_LOCKED));
}

static void edid_set_mode(const struct video_timing *mode)
{
	unsigned char edid[128];
	int i;

	generate_edid(&edid, "OHW", "TV", 2015, "HDMI2USB 1", mode);
	for(i=0;i<sizeof(edid);i++)
		MMPTR(CSR_HDMI_IN0_EDID_MEM_BASE+4*i) = edid[i];
	generate_edid(&edid, "OHW", "TV", 2015, "HDMI2USB 2", mode);
	for(i=0;i<sizeof(edid);i++)
		MMPTR(CSR_HDMI_IN1_EDID_MEM_BASE+4*i) = edid[i];
}

int processor_mode = 0;
void processor_start(int mode)
{
	const struct video_timing *m = &video_modes[mode];
	processor_mode = mode;
	processor_h_active = m->h_active;
	processor_v_active = m->v_active;

	processor_hdmi_out0_source = VIDEO_IN_HDMI_IN0;
	processor_hdmi_out1_source = VIDEO_IN_HDMI_IN0;
	processor_encoder_source = VIDEO_IN_HDMI_IN0;

	hdmi_out0_fi_enable_write(0);
	hdmi_out1_fi_enable_write(0);
	hdmi_out0_driver_clocking_pll_reset_write(1);
	hdmi_in0_edid_hpd_en_write(0);
	hdmi_in1_edid_hpd_en_write(0);

	hdmi_in0_disable();
	hdmi_in1_disable();
	hdmi_in0_clear_framebuffers();
	hdmi_in1_clear_framebuffers();

	pll_config_for_clock(m->pixel_clock);
	fb_set_mode(m);
	edid_set_mode(m);
	hdmi_in0_init_video(m->h_active, m->v_active);
	hdmi_in1_init_video(m->h_active, m->v_active);

	hdmi_out0_driver_clocking_pll_reset_write(0);
	hdmi_out0_fi_enable_write(1);
	hdmi_out1_fi_enable_write(1);
	hdmi_in0_edid_hpd_en_write(1);
	hdmi_in1_edid_hpd_en_write(1);
}

void processor_set_hdmi_out0_source(int source) {
	processor_hdmi_out0_source = source;
}

void processor_set_hdmi_out1_source(int source) {
	processor_hdmi_out1_source = source;
}

void processor_set_encoder_source(int source) {
	processor_encoder_source = source;
}

void processor_update(void)
{
	/*  hdmi_out0 */
	if(processor_hdmi_out0_source == VIDEO_IN_HDMI_IN0) {
		hdmi_out0_fi_base0_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_index));
	}
	else if(processor_hdmi_out0_source == VIDEO_IN_HDMI_IN1) {
		hdmi_out0_fi_base0_write(hdmi_in1_framebuffer_base(hdmi_in1_fb_index));
	}

	/*  hdmi_out1 */
	if(processor_hdmi_out1_source == VIDEO_IN_HDMI_IN0) {
		hdmi_out1_fi_base0_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_index));
	}
	else if(processor_hdmi_out1_source == VIDEO_IN_HDMI_IN1) {
		hdmi_out1_fi_base0_write(hdmi_in1_framebuffer_base(hdmi_in1_fb_index));
	}

#ifdef ENCODER_BASE
	/*  encoder */
	if(processor_encoder_source == VIDEO_IN_HDMI_IN0) {
		encoder_reader_dma_base_write((hdmi_in0_framebuffer_base(hdmi_in0_fb_index)));
	}
	else if(processor_encoder_source == VIDEO_IN_HDMI_IN1) {
		encoder_reader_dma_base_write((hdmi_in1_framebuffer_base(hdmi_in1_fb_index)));
	}
#endif
}

void processor_service(void)
{
	hdmi_in0_service();
	hdmi_in1_service();
	processor_update();
}
