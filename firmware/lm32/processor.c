#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <time.h>

#include "hdmi_in0.h"
#include "hdmi_in1.h"
#include "pattern.h"
#include "encoder.h"
#include "edid.h"
#include "pll.h"
#include "processor.h"

/*
 ----------------->>> Time ----------->>>

                  +-------------------+
   Video          |  Blanking         |  Video
                  |                   |
 ----(a)--------->|<-------(b)------->|
                  |                   |
                  |       +-------+   |
                  |       | Sync  |   |
                  |       |       |   |
                  |<-(c)->|<-(d)->|   |
                  |       |       |   |
 ----(1)--------->|       |       |   |
 ----(2)----------------->|       |   |
 ----(3)------------------------->|   |
 ----(4)----------------------------->|
                  |       |       |   |

 (a) - h_active ==(1)
 (b) - h_blanking
 (c) - h_sync_offset
 (d) - h_sync_width
 (1) - HDisp / width == (a)
 (2) - HSyncStart
 (3) - HSyncEnd
 (4) - HTotal

 Modeline "String description" Dot-Clock HDisp HSyncStart HSyncEnd HTotal VDisp VSyncStart VSyncEnd VTotal [options]

                            (1|a)    (2)    (3)  (4)
 ModeLine "640x480"    31.5  640    664    704  832    480  489  491  520
                              |\-(c)-/\-(b)-/    |
                              |   24    40       |
                              |                  |
                              \--------(b)-------/
                                       192

References:
 * http://www.arachnoid.com/modelines/
 * http://martin.hinner.info/vga/timing.html
 * VESA Modes - http://cvsweb.xfree86.org/cvsweb/xc/programs/Xserver/hw/xfree86/etc/vesamodes
 * 720p and TV modes - https://www.mythtv.org/wiki/Modeline_Database

*/
static const struct video_timing video_modes[PROCESSOR_MODE_COUNT] = {
	// 640x480 @ 72Hz (VESA) hsync: 37.9kHz
	// ModeLine "640x480"    31.5  640  664  704  832    480  489  491  520
	//                                24   40  <192          9   2   <40
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
	// 640x480 @ 75Hz (VESA) hsync: 37.5kHz
	// ModeLine "640x480"    31.5  640  656  720  840    480  481  484  500
	//                                16   64  <200         1    3   <20
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
	// 800x600 @ 56Hz (VESA) hsync: 35.2kHz
	// ModeLine "800x600"    36.0  800  824  896 1024    600  601  603  625
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
	// 800x600 @ 60Hz (VESA) hsync: 37.9kHz
	// ModeLine "800x600"    40.0  800  840  968 1056    600  601  605  628
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
	// 800x600 @ 72Hz (VESA) hsync: 48.1kHz
	// ModeLine "800x600"    50.0  800  856  976 1040    600  637  643  666
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
	// 800x600 @ 75Hz (VESA) hsync: 46.9kHz
	// ModeLine "800x600"    49.5  800  816  896 1056    600  601  604  625
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
	// 1024x768 @ 60Hz (VESA) hsync: 48.4kHz
	// ModeLine "1024x768"   65.0 1024 1048 1184 1344    768  771  777  806
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
	// 1024x768 @ 70Hz (VESA) hsync: 56.5kHz
	// ModeLine "1024x768"   75.0 1024 1048 1184 1328    768  771  777  806
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
	// 1024x768 @ 75Hz (VESA) hsync: 60.0kHz
	// ModeLine "1024x768"   78.8 1024 1040 1136 1312    768  769  772  800
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
	// 720p @ 60Hz
	//1280	720	60 Hz	45 kHz		ModeLine "1280x720"		74.25  1280 1390 1430 1650 720 725 730 750 +HSync +VSync
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
	},
	// Other 720p60 modes not enabled...
	//1280	720	60 Hz	44.9576 kHz	ModeLine "1280x720"		74.18  1280 1390 1430 1650 720 725 730 750 +HSync +VSync
	//1280	720	59.94			ModeLine "ATSC-720-59.94p"	74.176 1280 1320 1376 1650 720 722 728 750
	//1280	720	60 Hz			ModeLine "ATSC-720-60p"		74.25  1280 1320 1376 1650 720 722 728 750

	// 720p @ 50Hz
	// 19 720p50    16:9     1:1        1280x720p @ 50 Hz
	//1280	720	50 Hz	37.5 kHz	ModeLine "1280x720"		74.25  1280 1720 1760 1980 720 725 730 750 +HSync +VSync
	//                                                                                440   40  <700      5   5   <30
	{
		.pixel_clock = 7425,

		.h_active = 1280,
		.h_blanking = 700,
		.h_sync_offset = 440,
		.h_sync_width = 40,

		.v_active = 720,
		.v_blanking = 30,
		.v_sync_offset = 5,
		.v_sync_width = 5
	}
};

void processor_list_modes(char *mode_descriptors)
{
	int i;
	for(i=0;i<PROCESSOR_MODE_COUNT;i++) {
		sprintf(&mode_descriptors[PROCESSOR_MODE_DESCLEN*i],
			"%ux%u @%uHz", video_modes[i].h_active, video_modes[i].v_active, calculate_refresh_rate(&(video_modes[i])));
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

void processor_init(void)
{
	processor_hdmi_out0_source = VIDEO_IN_HDMI_IN0;
	processor_hdmi_out1_source = VIDEO_IN_HDMI_IN0;
	processor_encoder_source = VIDEO_IN_HDMI_IN0;
#ifdef ENCODER_BASE
		encoder_enable(0);
#endif
}

void processor_start(int mode)
{
	const struct video_timing *m = &video_modes[mode];
	processor_mode = mode;
	processor_h_active = m->h_active;
	processor_v_active = m->v_active;
	processor_refresh = calculate_refresh_rate(m);

	hdmi_out0_fi_enable_write(0);
	hdmi_out1_fi_enable_write(0);
	hdmi_out0_driver_clocking_pll_reset_write(1);
	hdmi_in0_edid_hpd_en_write(0);
	hdmi_in1_edid_hpd_en_write(0);

	hdmi_in0_disable();
	hdmi_in1_disable();
	hdmi_in0_clear_framebuffers();
	hdmi_in1_clear_framebuffers();
	pattern_fill_framebuffer(m->h_active, m->v_active);

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

char * processor_get_source_name(int source) {
	memset(processor_buffer, 0, 16);
	if(source == VIDEO_IN_PATTERN)
		sprintf(processor_buffer, "pattern");
	else
		sprintf(processor_buffer, "input%d", source);
	return processor_buffer;
}

void processor_update(void)
{
	/*  hdmi_out0 */
	if(processor_hdmi_out0_source == VIDEO_IN_HDMI_IN0)
		hdmi_out0_fi_base0_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_index));
	else if(processor_hdmi_out0_source == VIDEO_IN_HDMI_IN1)
		hdmi_out0_fi_base0_write(hdmi_in1_framebuffer_base(hdmi_in1_fb_index));
	else if(processor_hdmi_out0_source == VIDEO_IN_PATTERN)
		hdmi_out0_fi_base0_write(pattern_framebuffer_base());

	/*  hdmi_out1 */
	if(processor_hdmi_out1_source == VIDEO_IN_HDMI_IN0)
		hdmi_out1_fi_base0_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_index));
	else if(processor_hdmi_out1_source == VIDEO_IN_HDMI_IN1)
		hdmi_out1_fi_base0_write(hdmi_in1_framebuffer_base(hdmi_in1_fb_index));
	else if(processor_hdmi_out1_source == VIDEO_IN_PATTERN)
		hdmi_out1_fi_base0_write(pattern_framebuffer_base());

#ifdef ENCODER_BASE
	/*  encoder */
	if(processor_encoder_source == VIDEO_IN_HDMI_IN0) {
		encoder_reader_dma_base_write((hdmi_in0_framebuffer_base(hdmi_in0_fb_index)));
	}
	else if(processor_encoder_source == VIDEO_IN_HDMI_IN1) {
		encoder_reader_dma_base_write((hdmi_in1_framebuffer_base(hdmi_in1_fb_index)));
	}
	else if(processor_encoder_source == VIDEO_IN_PATTERN)
		encoder_reader_dma_base_write(pattern_framebuffer_base());
#endif
}

void processor_service(void)
{
	hdmi_in0_service();
	hdmi_in1_service();
	processor_update();
#ifdef ENCODER_BASE
		encoder_service();
#endif
}
