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

#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/mem.h>

#include <hw/flags.h>
#include <time.h>
#include <console.h>

#include "asm.h"
#include "bist.h"
#include "ci.h"
#include "config.h"
#include "edid.h"
#include "encoder.h"
#include "fx2.h"
#include "hdmi_in0.h"
#include "hdmi_in1.h"
#include "hdmi_out0.h"
#include "hdmi_out1.h"
#include "heartbeat.h"
#include "mdio.h"
#include "mmcm.h"
#include "opsis_eeprom.h"
#include "pattern.h"
#include "pll.h"
#include "processor.h"
#include "reboot.h"
#include "stdio_wrap.h"
#include "telnet.h"
#include "tofe_eeprom.h"
#include "uptime.h"
#include "version.h"

#include "ci.h"

int status_enabled;
int status_short_enabled;

static void help_video_matrix(void)
{
	wputs("video_matrix commands (alias: 'x')");
	wputs("  video_matrix list              - list available video sinks and sources");
	wputs("  x l                            - list available video sinks and sources");
	wputs("  video_matrix connect <source>  - connect video source to video sink");
	wputs("                       <sink>");
	wputs("  x c <source> <sink>            - connect video source to video sink");
}

static void help_video_mode(void)
{
	wputs("video_mode commands (alias: 'm')");
	wputs("  video_mode list                - list available video modes");
	wputs("  m l                            - list available video modes");
	wputs("  video_mode <mode>              - select video mode");
	wputs("  video_mode custom <modeline>   - set custom video mode");
	wputs("  video_mode secondary <mode>    - select secondary video mode");
	wputs("  video_mode s <mode>            - select secondary video mode");
	wputs("  video_mode secondary off       - turn off secondary video mode");
}

static void help_hdp_toggle(void)
{
	wputs("hdp_toggle <source>              - toggle HDP on source for EDID rescan");
}

static void help_status(void)
{
	wputs("status commands (alias: 's')");
	wputs("  status                         - print status message once");
	wputs("  status short                   - print status (short) message once");
	wputs("  status <on/off>                - repeatedly print status message");
	wputs("  status short <on/off>          - repeatedly print (short) status message");
}

static void help_heartbeat(void)
{
	wputs("change heartbeat status (alias: 'h')");
	wputs("  heartbeat <on/off>             - Turn on/off heartbeat feature");
}

static void heartbeat_enable(void)
{
	hb_status(true);
	wprintf("Heartbeat enabled\n");
}

static void heartbeat_disable(void)
{
	hb_status(false);
	wprintf("Heartbeat disabled\n");
}

#ifdef CSR_HDMI_OUT0_BASE
static void help_output0(void)
{
	wputs("output0 commands (alias: 'o0')");
	wputs("  output0 on                     - enable output0");
	wputs("  output0 off                    - disable output0");
}
#endif

#ifdef CSR_HDMI_OUT1_BASE
static void help_output1(void)
{
	wputs("output1 commands (alias: 'o1')");
	wputs("  output1 on                     - enable output1");
	wputs("  output1 off                    - disable output1");
}
#endif

#ifdef CSR_HDMI_IN0_BASE
static void help_input0(void)
{
	wputs("input0 commands (alias: 'i0')");
	wputs("  input0 on                     - enable input0");
	wputs("  input0 off                    - disable input0");
}
#endif

#ifdef CSR_HDMI_IN1_BASE
static void help_input1(void)
{
	wputs("input1 commands (alias: 'i1')");
	wputs("  input1 on                     - enable input1");
	wputs("  input1 off                    - disable input1");
}
#endif

#ifdef ENCODER_BASE
static void help_encoder(void)
{
	wputs("encoder commands (alias: 'e')");
	wputs("  encoder on                     - enable encoder");
	wputs("  encoder off                    - disable encoder");
	wputs("  encoder quality <quality>      - select quality");
	wputs("  encoder fps <fps>              - configure target fps");
}
#endif

static void help_debug(void)
{
	wputs("debug commands (alias 'd')");
#ifdef CSR_GENERATOR_BASE
	wputs("  debug sdram_test               - run a memory test");
#endif
	wputs("  debug clocks                   - dump pll/mmcm configuration");
#ifdef CSR_HDMI_IN0_BASE
	wputs("  debug input0 <on/off>          - debug dvisampler0");
#endif
#ifdef CSR_HDMI_IN1_BASE
	wputs("  debug input1 <on/off>          - debug dvisampler1");
#endif
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
	wputs("  debug ddr                      - show DDR bandwidth");
#endif
	wputs("  debug dna                      - show Board's DNA");
	wputs("  debug edid                     - dump monitor EDID");
#ifdef CSR_CAS_BASE
	wputs("  debug cas leds <value>         - change the status LEDs");
	wputs("  debug cas switches             - read the control switches status");
	wputs("  debug cas buttons read         - read the control buttons status");
	wputs("  debug cas buttons clear        - clear any asserted buttons status");
#endif
}

static void ci_help(void)
{
	wputs("help        - this command");
	wputs("reboot      - reboot CPU");
#ifdef CSR_ETHPHY_MDIO_W_ADDR
	wputs("mdio_dump   - dump mdio registers");
	wputs("mdio_status - show mdio status");
#endif
	wputs("pattern (p) - select next pattern");
	wputs("");
	help_status();
	wputs("");
	help_video_matrix();
	wputs("");
	help_video_mode();
	wputs("");
	help_heartbeat();
	wputs("");
	help_hdp_toggle();
	wputs("");
#ifdef CSR_HDMI_OUT0_BASE
	help_output0();
	wputs("");
#endif
#ifdef CSR_HDMI_OUT1_BASE
	help_output1();
	wputs("");
#endif
#ifdef CSR_HDMI_IN0_BASE
	help_input0();
	wputs("");
#endif
#ifdef CSR_HDMI_IN1_BASE
	help_input1();
	wputs("");
#endif
#ifdef ENCODER_BASE
	help_encoder();
	wputs("");
#endif
	help_debug();
}

static char *readstr(void)
{
	char c[2];
	static char s[128]; // Needs to fit a full mode line ~100 chars.
	static int ptr = 0;

	if(telnet_active) {
		if(telnet_readchar_nonblock()) {
			c[0] = telnet_readchar();
			c[1] = 0;
			switch(c[0]) {
				case 0x7f:
				case 0x08:
					if(ptr > 0) {
						ptr--;
					}
					break;
				case 0x07:
					break;
				case '\r':
					break;
				case '\n':
					s[ptr] = 0x00;
					ptr = 0;
					return s;
				default:
					if(ptr >= (sizeof(s) - 1))
						break;
					s[ptr] = c[0];
					ptr++;
					break;
			}
		}
	} else {
		if(readchar_nonblock()) {
			c[0] = readchar();
			c[1] = 0;
			switch(c[0]) {
				case 0x7f:
				case 0x08:
					if(ptr > 0) {
						ptr--;
						wputsnonl("\x08 \x08");
					}
					break;
				case 0x07:
					break;
				case '\n':
					break;
				case '\r':
					s[ptr] = 0x00;
					wputs("");
					ptr = 0;
					return s;
				default:
					if(ptr >= (sizeof(s) - 1))
						break;
					wputsnonl(c);
					s[ptr] = c[0];
					ptr++;
					break;
			}
		}
	}

	return NULL;
}

static char *get_token_generic(char **str, char delimiter)
{
	char *c, *d;

	c = (char *)strchr(*str, delimiter);
	if(c == NULL) {
		d = *str;
		*str = *str+strlen(*str);
		return d;
	}
	*c = 0;
	d = *str;
	*str = c+1;
	return d;
}

static char *get_token(char **str)
{
	char *t;
	do {
		t = get_token_generic(str, ' ');
		if (*t == '\0' && **str == '\0') {
			break;
		}
	} while (*t == '\0');
	return t;
}

static void status_enable(void)
{
	wprintf("Enabling status\n");
	status_enabled = 1;
}

static void status_disable(void)
{
	wprintf("Disabling status\n");
	status_enabled = 0;
}

static void status_short_enable(void)
{
	wprintf("Enabling short status\n");
	status_short_enabled = 1;
}

static void status_short_disable(void)
{
	wprintf("Disabling status\n");
	status_short_enabled = 0;
}


static void debug_ddr(void);

static void status_short_print(void)
{
	wprintf("status1: ");
	unsigned int underflows;
#ifdef CSR_HDMI_IN0_BASE
	wprintf(
		"in0: %dx%d",
		hdmi_in0_resdetection_hres_read(),
		hdmi_in0_resdetection_vres_read());
#ifdef CSR_HDMI_IN0_FREQ_BASE
	wprintf("@" REFRESH_RATE_PRINTF "MHz, ",
		REFRESH_RATE_PRINTF_ARGS(hdmi_in0_freq_value_read() / 10000));
#endif
#endif

#ifdef CSR_HDMI_IN1_BASE
	wprintf(
		"in1: %dx%d",
		hdmi_in1_resdetection_hres_read(),
		hdmi_in1_resdetection_vres_read());
#ifdef CSR_HDMI_IN1_FREQ_BASE
	wprintf("@" REFRESH_RATE_PRINTF "MHz, ",
		REFRESH_RATE_PRINTF_ARGS(hdmi_in1_freq_value_read() / 10000));
#endif
#endif

#ifdef CSR_HDMI_OUT0_BASE
	wprintf("out0: ");
	if(hdmi_out0_core_initiator_enable_read()) {
		hdmi_out0_core_underflow_enable_write(1);
		hdmi_out0_core_underflow_update_write(1);
		underflows = hdmi_out0_core_underflow_counter_read();
		wprintf(
			"%dx%d@" REFRESH_RATE_PRINTF "Hz %s (uf:%d), ",
			processor_h_active,
			processor_v_active,
			REFRESH_RATE_PRINTF_ARGS(processor_refresh),
			processor_get_source_name(processor_hdmi_out0_source),
			underflows);
		hdmi_out0_core_underflow_enable_write(0);
		hdmi_out0_core_underflow_enable_write(1);
	} else
		wprintf("off, ");
#endif

#ifdef CSR_HDMI_OUT1_BASE
	wprintf("out1: ");
	if(hdmi_out1_core_initiator_enable_read()) {
		hdmi_out1_core_underflow_enable_write(1);
		hdmi_out1_core_underflow_update_write(1);
		underflows = hdmi_out1_core_underflow_counter_read();
		wprintf(
			"%dx%d@" REFRESH_RATE_PRINTF "Hz %s (uf:%d) ",
			processor_h_active,
			processor_v_active,
			REFRESH_RATE_PRINTF_ARGS(processor_refresh),
			processor_get_source_name(processor_hdmi_out1_source),
			underflows);
		hdmi_out1_core_underflow_enable_write(0);
		hdmi_out1_core_underflow_enable_write(1);
	} else
		wprintf("off ");
#endif

	wprintf("\nstatus2: ");
	wprintf("EDID: ");
	wprintf("%dx%d@" REFRESH_RATE_PRINTF "Hz/",
		processor_h_active,
		processor_v_active,
		REFRESH_RATE_PRINTF_ARGS(processor_refresh));

	if (processor_secondary_mode == EDID_SECONDARY_MODE_OFF) {
		wprintf("off, ");
	}
	else {
		char mode_descriptor[PROCESSOR_MODE_DESCLEN];
		processor_describe_mode(mode_descriptor, processor_secondary_mode);
		wprintf("%s, ", mode_descriptor);
	}

#ifdef ENCODER_BASE
	wprintf("enc: ");
	if(encoder_enabled) {
		wprintf(
			"%dx%d@%dfps %s (q:%d), ",
			processor_h_active,
			processor_v_active,
			encoder_fps,
			processor_get_source_name(processor_encoder_source),
			encoder_quality);
	} else
		wprintf("off, ");
#endif
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
	wprintf("ddr: ");
	debug_ddr();
#endif
	wputchar('\n');
}

static void status_print(void)
{
	unsigned int underflows;
#ifdef CSR_HDMI_IN0_BASE
	wprintf(
		"input0:  %dx%d",
		hdmi_in0_resdetection_hres_read(),
		hdmi_in0_resdetection_vres_read());
#ifdef CSR_HDMI_IN0_FREQ_BASE
	wprintf(" (@" REFRESH_RATE_PRINTF " MHz)",
		REFRESH_RATE_PRINTF_ARGS(hdmi_in0_freq_value_read() / 10000));
	if(hdmi_in0_status()) {
		wprintf(" (capturing)");
	} else {
		wprintf(" (disabled)");
	}
#endif
	wputchar('\n');
#endif

#ifdef CSR_HDMI_IN1_BASE
	wprintf(
		"input1:  %dx%d",
		hdmi_in1_resdetection_hres_read(),
		hdmi_in1_resdetection_vres_read());
#ifdef CSR_HDMI_IN1_FREQ_BASE
	wprintf(" (@" REFRESH_RATE_PRINTF " MHz)",
		REFRESH_RATE_PRINTF_ARGS(hdmi_in1_freq_value_read() / 10000));
#endif
	if(hdmi_in1_status()) {
		wprintf(" (capturing)");
	} else {
		wprintf(" (disabled)");
	}
	wputchar('\n');
#endif

#ifdef CSR_HDMI_OUT0_BASE
	wprintf("output0: ");
	if(hdmi_out0_core_initiator_enable_read()) {
		hdmi_out0_core_underflow_enable_write(1);
		hdmi_out0_core_underflow_update_write(1);
		underflows = hdmi_out0_core_underflow_counter_read();
		wprintf(
			"%dx%d@" REFRESH_RATE_PRINTF "Hz from %s (underflows: %d)",
			processor_h_active,
			processor_v_active,
			REFRESH_RATE_PRINTF_ARGS(processor_refresh),
			processor_get_source_name(processor_hdmi_out0_source),
			underflows);
		hdmi_out0_core_underflow_enable_write(0);
		hdmi_out0_core_underflow_enable_write(1);
	} else
		wprintf("off");
	wputchar('\n');
#endif

#ifdef CSR_HDMI_OUT1_BASE
	wprintf("output1: ");
	if(hdmi_out1_core_initiator_enable_read()) {
		hdmi_out1_core_underflow_enable_write(1);
		hdmi_out1_core_underflow_update_write(1);
		underflows = hdmi_out1_core_underflow_counter_read();
		wprintf(
			"%dx%d@" REFRESH_RATE_PRINTF "Hz from %s (underflows: %d)",
			processor_h_active,
			processor_v_active,
			REFRESH_RATE_PRINTF_ARGS(processor_refresh),
			processor_get_source_name(processor_hdmi_out1_source),
			underflows);
		hdmi_out1_core_underflow_enable_write(0);
		hdmi_out1_core_underflow_enable_write(1);
	} else
		wprintf("off");
	wputchar('\n');
#endif

	wprintf("EDID primary mode:   ");
	wprintf("%dx%d@" REFRESH_RATE_PRINTF "Hz",
		processor_h_active,
		processor_v_active,
		REFRESH_RATE_PRINTF_ARGS(processor_refresh));
	wputchar('\n');

	wprintf("EDID secondary mode: ");
	if (processor_secondary_mode == EDID_SECONDARY_MODE_OFF) {
		wprintf("off");
	}
	else {
		char mode_descriptor[PROCESSOR_MODE_DESCLEN];
		processor_describe_mode(mode_descriptor, processor_secondary_mode);
		wprintf("%s", mode_descriptor);
	}
	wputchar('\n');

#ifdef ENCODER_BASE
	wprintf("encoder: ");
	if(encoder_enabled) {
		wprintf(
			"%dx%d @ %dfps from %s (q: %d)",
			processor_h_active,
			processor_v_active,
			encoder_fps,
			processor_get_source_name(processor_encoder_source),
			encoder_quality);
	} else
		wprintf("off");
	wputchar('\n');
#endif
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
	wprintf("ddr: ");
	debug_ddr();
	wputchar('\n');
#endif
}

static void status_service(void)
{
	static int last_event;

	if(elapsed(&last_event, SYSTEM_CLOCK_FREQUENCY)) {
		if(status_enabled) {
			status_print();
			wputchar('\n');
		}
		if(status_short_enabled) {
		    status_short_print();
		}
	}
}

#ifdef CSR_HDMI_IN0_BASE
#ifndef HDMI_IN0_MNEMONIC
#warning "Missing HDMI IN0 mnemonic!"
#define HDMI_IN0_MNEMONIC ""
#endif
#ifndef HDMI_IN0_DESCRIPTION
#warning "Missing HDMI IN0 description!"
#define HDMI_IN0_DESCRIPTION ""
#endif
#endif

#ifdef CSR_HDMI_IN1_BASE
#ifndef HDMI_IN1_MNEMONIC
#warning "Missing HDMI IN1 mnemonic!"
#define HDMI_IN1_MNEMONIC ""
#endif
#ifndef HDMI_IN1_DESCRIPTION
#warning "Missing HDMI IN1 description!"
#define HDMI_IN1_DESCRIPTION ""
#endif
#endif

#ifdef CSR_HDMI_OUT0_BASE
#ifndef HDMI_OUT0_MNEMONIC
#warning "Missing HDMI OUT0 mnemonic!"
#define HDMI_OUT0_MNEMONIC ""
#endif
#ifndef HDMI_OUT0_DESCRIPTION
#warning "Missing HDMI OUT0 description!"
#define HDMI_OUT0_DESCRIPTION ""
#endif
#endif

#ifdef CSR_HDMI_OUT1_BASE
#ifndef HDMI_OUT1_MNEMONIC
#warning "Missing HDMI OUT1 mnemonic!"
#define HDMI_OUT1_MNEMONIC ""
#endif
#ifndef HDMI_OUT1_DESCRIPTION
#warning "Missing HDMI OUT1 description!"
#define HDMI_OUT1_DESCRIPTION ""
#endif
#endif

static void video_matrix_list(void)
{
	wprintf("Video sources:\n");
#ifdef CSR_HDMI_IN0_BASE
	wprintf("input0 (0): %s\n", HDMI_IN0_MNEMONIC);
	wputs(HDMI_IN0_DESCRIPTION);
#endif
#ifdef CSR_HDMI_IN1_BASE
	wprintf("input1 (1): %s\n", HDMI_IN1_MNEMONIC);
	wputs(HDMI_IN1_DESCRIPTION);
#endif
	wprintf("pattern (p):\n");
	wprintf("  Video pattern\n");
	wputs(" ");
	wprintf("Video sinks:\n");
#ifdef CSR_HDMI_OUT0_BASE
	wprintf("output0 (0): %s\n", HDMI_OUT0_MNEMONIC);
	wputs(HDMI_OUT0_DESCRIPTION);
#endif
#ifdef CSR_HDMI_OUT1_BASE
	wprintf("output1 (1): %s\n", HDMI_OUT1_MNEMONIC);
	wputs(HDMI_OUT1_DESCRIPTION);
#endif
#ifdef ENCODER_BASE
	wprintf("encoder (e):\n");
	wprintf("  JPEG encoder (USB output)\n");
#endif
	wputs(" ");
}

static void video_matrix_connect(int source, int sink)
{
	if(source >= 0 && source <= VIDEO_IN_PATTERN)
	{
		if(sink >= 0 && sink <= VIDEO_OUT_HDMI_OUT1) {
			wprintf("Connecting %s to output%d\n", processor_get_source_name(source), sink);
			if(sink == VIDEO_OUT_HDMI_OUT0)
#ifdef CSR_HDMI_OUT0_BASE
				processor_set_hdmi_out0_source(source);
#else
				wprintf("hdmi_out0 is missing.\n");
#endif
			else if(sink == VIDEO_OUT_HDMI_OUT1)
#ifdef CSR_HDMI_OUT1_BASE
				processor_set_hdmi_out1_source(source);
#else
				wprintf("hdmi_out1 is missing.\n");
#endif
			processor_update();
		}
#ifdef ENCODER_BASE
		else if(sink == VIDEO_OUT_ENCODER) {
			wprintf("Connecting %s to encoder\n", processor_get_source_name(source));
			processor_set_encoder_source(source);
			processor_update();
		}
#endif
	}
}

static void video_mode_list(void)
{
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];
	int i;

	processor_list_modes(mode_descriptors);
	wprintf("Available video modes:\n");
	for(i=0;i<PROCESSOR_MODE_COUNT;i++)
		wprintf("mode %d: %s\n", i, &mode_descriptors[i*PROCESSOR_MODE_DESCLEN]);
	wputchar('\n');
}

static void video_mode_set(int mode)
{
	char mode_descriptor[PROCESSOR_MODE_DESCLEN];
	if(mode < PROCESSOR_MODE_COUNT) {
		processor_describe_mode(mode_descriptor, mode);
		wprintf("Setting video mode to %s\n", mode_descriptor);
		config_set(CONFIG_KEY_RES_PRIMARY, mode);
		processor_start(mode);
	}
}

static void video_mode_secondary(char *str)
{
	char *token;
	if((token = get_token(&str)) == '\0') return;

	if(strcmp(token, "off") == 0) {
		wprintf("Turning off secondary video mode\n");
		processor_set_secondary_mode(EDID_SECONDARY_MODE_OFF);
	}
	else {
		int mode = atoi(token);
		char mode_descriptor[PROCESSOR_MODE_DESCLEN];
		if (mode < PROCESSOR_MODE_COUNT) {
			processor_describe_mode(mode_descriptor, mode);
			wprintf("Setting secondary video mode to %s\n", mode_descriptor);
			config_set(CONFIG_KEY_RES_SECONDARY, mode);
			processor_set_secondary_mode(mode);
		}
	}
}

#define NEXT_TOKEN_OR_RETURN(s, t)				\
	if(!(t = get_token(&s))) {				\
		wprintf("Parse failed - invalid mode.\n");	\
		return;						\
	}

static void video_mode_custom(char* str)
{
	wprintf("Parsing custom mode...\n");

	char* token;
	// Modeline "String description" Dot-Clock HDisp HSyncStart HSyncEnd HTotal VDisp VSyncStart VSyncEnd VTotal [options]
	// $ xrandr --newmode "1280x1024_60.00"  109.00  1280 1368 1496 1712  1024 1027 1034 1063 -hsync +vsync

	// Based on code from http://cgit.freedesktop.org/xorg/app/xrandr/tree/xrandr.c#n3101

	NEXT_TOKEN_OR_RETURN(str, token);
	char* dotClockInt = get_token_generic(&token, '.');
	char* dotClockDec = get_token(&token);
	if (!dotClockInt || !dotClockDec) return;
	unsigned int dotClock = (atoi(dotClockInt) * 100) + atoi(dotClockDec);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int width = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int hSyncStart = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int hSyncEnd = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int hTotal = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int height = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int vSyncStart = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int vSyncEnd = atoi(token);

	NEXT_TOKEN_OR_RETURN(str, token);
	unsigned int vTotal = atoi(token);

	unsigned int modeFlags = EDID_DIGITAL; // Always Digital Separate
	while (*str != '\0') {
		token = get_token(&str);
		if (*token == '\0' && *str == '\0') break;

		int f;

		for (f = 0; timing_mode_flags[f].string; f++)
			if (strcasecmp(timing_mode_flags[f].string, token) == 0)
				break;

		if (!timing_mode_flags[f].string) {
			if (*token != '\0') {
				wprintf("Skipping flag: %s\n", token);
				continue;
			}
			break;
		}

		modeFlags |= timing_mode_flags[f].flag;
	}

	/*
	 -------------------> Time ------------->

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
	 -----------------\                   /--------
	                  |                   |
	                  \-------\       /---/
	                          |       |
	                          \-------/

	 (a) - h_active
	 (b) - h_blanking
	 (c) - h_sync_offset
	 (d) - h_sync_width
	 (1) - HDisp / width
	 (2) - HSyncStart
	 (3) - HSyncEnd
	 (4) - HTotal
	*/

	if (hTotal <= hSyncEnd || hSyncEnd <= hSyncStart ||
			hSyncStart <= width || vTotal <= vSyncEnd ||
			vSyncEnd <= vSyncStart || vSyncStart <= height) {
		wprintf("Failed to set custom mode - values out of range.\n");
	}

	struct video_timing* mode = processor_get_custom_mode();

	// 640x480 @ 75Hz (VESA) hsync: 37.5kHz
	// Modeline "String des" Dot-Clock HDisp HSyncStart HSyncEnd HTotal VDisp VSyncStart VSyncEnd VTotal [options]
	// ModeLine "640x480"    31.5  640  656  720  840    480  481  484  500
	//                                16   64  <200         1    3   <20

	mode->pixel_clock = dotClock;

	mode->h_active = width;
	mode->h_blanking = hTotal - width;
	mode->h_sync_offset = hSyncStart - hTotal;
	mode->h_sync_width = hSyncEnd - hSyncStart;

	mode->v_active = height;
	mode->v_blanking = vTotal - height;
	mode->v_sync_offset = vSyncStart - height;
	mode->v_sync_width = vSyncEnd - vSyncStart;

	mode->flags = modeFlags;

	processor_set_custom_mode();
	wprintf("Custom video mode set.\n");
}

static void hdp_toggle(int source)
{
#if defined(CSR_HDMI_IN0_BASE) || defined(CSR_HDMI_IN1_BASE)
	int i;
#endif
	wprintf("Toggling HDP on output%d\n", source);
#ifdef CSR_HDMI_IN0_BASE
	if(source == VIDEO_IN_HDMI_IN0) {
		hdmi_in0_edid_hpd_en_write(0);
		for(i=0; i<65536; i++);
		hdmi_in0_edid_hpd_en_write(1);
	}
#else
	wprintf("hdmi_in0 is missing.\n");
#endif
#ifdef CSR_HDMI_IN1_BASE
	if(source == VIDEO_IN_HDMI_IN1) {
		hdmi_in1_edid_hpd_en_write(0);
		for(i=0; i<65536; i++);
		hdmi_in1_edid_hpd_en_write(1);
	}
#else
	wprintf("hdmi_in1 is missing.\n");
#endif
}

#ifdef CSR_HDMI_IN0_BASE
void input0_on(void)
{
	wprintf("Enabling input0\n");
	hdmi_in0_enable();
}

void input0_off(void)
{
	wprintf("Disabling input0\n");
	hdmi_in0_disable();
}
#endif

#ifdef CSR_HDMI_IN1_BASE
void input1_on(void)
{
	wprintf("Enabling input1\n");
	hdmi_in1_enable();
}

void input1_off(void)
{
	wprintf("Disabling input1\n");
	hdmi_in1_disable();
}
#endif

#ifdef CSR_HDMI_OUT0_BASE
void output0_on(void)
{
	wprintf("Enabling output0\n");
	hdmi_out0_core_initiator_enable_write(1);
}

void output0_off(void)
{
	wprintf("Disabling output0\n");
	hdmi_out0_core_initiator_enable_write(0);
}
#endif

#ifdef CSR_HDMI_OUT1_BASE
void output1_on(void)
{
	wprintf("Enabling output1\n");
	hdmi_out1_core_initiator_enable_write(1);
}

void output1_off(void)
{
	wprintf("Disabling output1\n");
	hdmi_out1_core_initiator_enable_write(0);
}
#endif

#ifdef ENCODER_BASE
void encoder_on(void)
{
	wprintf("Enabling encoder\n");
	encoder_enable(1);
}

void encoder_configure_quality(int quality)
{
	wprintf("Setting encoder quality to %d\n", quality);
	encoder_set_quality(quality);
}

void encoder_configure_fps(int fps)
{
	wprintf("Setting encoder fps to %d\n", fps);
	encoder_set_fps(fps);
}

void encoder_off(void)
{
	wprintf("Disabling encoder\n");
	encoder_enable(0);
}
#endif

static void debug_clocks(void)
{
	// Only the active clock system will output anything
	pll_dump();
	mmcm_dump_all();
}

static unsigned int log2(unsigned int v)
{
	unsigned int r = 0;
	while(v>>=1) r++;
	return r;
}

#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
static void debug_ddr(void)
{
	/*
	unsigned long long int nr, nw;
	unsigned long long int f;
	unsigned int rdb, wrb;
	unsigned int burstbits;

	sdram_controller_bandwidth_update_write(1);
	nr = sdram_controller_bandwidth_nreads_read();
	nw = sdram_controller_bandwidth_nwrites_read();
	f = SYSTEM_CLOCK_FREQUENCY;
	burstbits = (2*DFII_NPHASES) << DFII_PIX_DATA_SIZE;
	rdb = (nr*f >> (24 - log2(burstbits)))/1000000ULL;
	wrb = (nw*f >> (24 - log2(burstbits)))/1000000ULL;
	wprintf("read:%5dMbps  write:%5dMbps  all:%5dMbps\n", rdb, wrb, rdb + wrb);
	*/
}
#endif

void ci_prompt(void)
{
	wprintf("H2U %s>", uptime_str());
}

void ci_service(void)
{
	char *str;
	char *token;

	status_service();

	str = readstr();
	if(str == NULL) return;

	token = get_token(&str);

	if(strcmp(token, "help") == 0) {
		wputs("Available commands:");
		token = get_token(&str);
		if(strcmp(token, "video_matrix") == 0)
			help_video_matrix();
		else if(strcmp(token, "video_mode") == 0)
			help_video_mode();
		else if(strcmp(token, "hdp_toggle") == 0)
			help_hdp_toggle();
#ifdef CSR_HDMI_OUT0_BASE
		else if(strcmp(token, "output0") == 0)
			help_output0();
#endif
#ifdef CSR_HDMI_OUT1_BASE
		else if(strcmp(token, "output1") == 0)
			help_output1();
#endif
#ifdef CSR_HDMI_IN0_BASE
		else if(strcmp(token, "input0") == 0)
			help_input0();
#endif
#ifdef CSR_HDMI_IN1_BASE
		else if(strcmp(token, "input1") == 0)
			help_input1();
#endif
#ifdef ENCODER_BASE
		else if(strcmp(token, "encoder") == 0)
			help_encoder();
#endif
		else if(strcmp(token, "debug") == 0)
			help_debug();
		else
			ci_help();
		wputs("");
	}
	else if(strcmp(token, "reboot") == 0) reboot();
	else if(strcmp(token, "uptime") == 0 || strcmp(token, "u") == 0) uptime_print();
#ifdef CSR_ETHPHY_MDIO_W_ADDR
	else if(strcmp(token, "mdio_status") == 0)
		mdio_status();
	else if(strcmp(token, "mdio_dump") == 0)
		mdio_dump();
#endif
	else if((strcmp(token, "video_matrix") == 0) || (strcmp(token, "x") == 0)) {
		token = get_token(&str);
		if((strcmp(token, "list") == 0) || (strcmp(token, "l") == 0)) {
			video_matrix_list();
		}
		else if((strcmp(token, "connect") == 0) || (strcmp(token, "c") == 0)) {
			int source;
			int sink;
			/* get video source */
			token = get_token(&str);
			source = -1;
			if((strcmp(token, "input0") == 0) || (strcmp(token, "0") == 0)) {
				source = VIDEO_IN_HDMI_IN0;
			}
			else if((strcmp(token, "input1") == 0) || (strcmp(token, "1") == 0)) {
				source = VIDEO_IN_HDMI_IN1;
			}
			else if((strcmp(token, "pattern") == 0) || (strcmp(token, "p") == 0)) {
				source = VIDEO_IN_PATTERN;
			}
			else {
				wprintf("Unknown video source: '%s'\n", token);
			}

			/* get video sink */
			token = get_token(&str);
			sink = -1;
			if((strcmp(token, "output0") == 0) || (strcmp(token, "0") == 0)) {
				sink = VIDEO_OUT_HDMI_OUT0;
			}
			else if((strcmp(token, "output1") == 0) || (strcmp(token, "1") == 0)) {
				sink = VIDEO_OUT_HDMI_OUT1;
			}
			else if((strcmp(token, "encoder") == 0) || (strcmp(token, "e") == 0)) {
				sink = VIDEO_OUT_ENCODER;
			}
			else
				wprintf("Unknown video sink: '%s'\n", token);

			if (source >= 0 && sink >= 0)
				video_matrix_connect(source, sink);
			else
				help_video_matrix();
		} else {
			help_video_matrix();
		}
	}
	else if((strcmp(token, "video_mode") == 0) || (strcmp(token, "m") == 0)) {
		token = get_token(&str);
		if((strcmp(token, "list") == 0) || (strcmp(token, "l") == 0))
			video_mode_list();
		else if(strcmp(token, "custom") == 0)
			video_mode_custom(str);
		else if((strcmp(token, "secondary") == 0) || (strcmp(token, "s") == 0))
			video_mode_secondary(str);
		else
			video_mode_set(atoi(token));
	}
	else if((strcmp(token, "heartbeat") == 0) || (strcmp(token, "h") == 0)) {
		token = get_token(&str);
		if((strcmp(token, "on") == 0) )
			heartbeat_enable();
		else if((strcmp(token, "off") == 0) )
			heartbeat_disable();
		else
			help_heartbeat();
	}
	else if(strcmp(token, "hdp_toggle") == 0) {
		token = get_token(&str);
		hdp_toggle(atoi(token));
	}
#ifdef CSR_HDMI_OUT0_BASE
	else if((strcmp(token, "output0") == 0) || (strcmp(token, "o0") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "on") == 0)
			output0_on();
		else if(strcmp(token, "off") == 0)
			output0_off();
		else
			help_output0();
	}
#endif
#ifdef CSR_HDMI_OUT1_BASE
	else if((strcmp(token, "output1") == 0) || (strcmp(token, "o1") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "on") == 0)
			output1_on();
		else if(strcmp(token, "off") == 0)
			output1_off();
		else
			help_output1();
	}
#endif
#ifdef CSR_HDMI_IN0_BASE
	else if((strcmp(token, "input0") == 0) || (strcmp(token, "i0") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "on") == 0)
			input0_on();
		else if(strcmp(token, "off") == 0)
			input0_off();
		else
			help_input0();
	}
#endif
#ifdef CSR_HDMI_IN1_BASE
	else if((strcmp(token, "input1") == 0) || (strcmp(token, "i1") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "on") == 0)
			input1_on();
		else if(strcmp(token, "off") == 0)
			input1_off();
		else
			help_input1();
	}
#endif
#ifdef ENCODER_BASE
	else if((strcmp(token, "encoder") == 0) || (strcmp(token, "e") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "on") == 0)
			encoder_on();
		else if(strcmp(token, "off") == 0)
			encoder_off();
		else if(strcmp(token, "quality") == 0)
			encoder_configure_quality(atoi(get_token(&str)));
		else if(strcmp(token, "fps") == 0)
			encoder_configure_fps(atoi(get_token(&str)));
		else
			help_encoder();
	}
#endif
	else if((strcmp(token, "p") == 0) || (strcmp(token, "p") == 0)) {
		pattern_next();
		wprintf("Pattern now %d\n", pattern);
	}
	else if((strcmp(token, "status") == 0) || (strcmp(token, "s") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "short") == 0) {
			token = get_token(&str);
			if(strcmp(token, "on") == 0)
				status_short_enable();
			else if(strcmp(token, "off") == 0)
				status_short_disable();
			else
				status_short_print();
		}
		else if(strcmp(token, "on") == 0)
			status_enable();
		else if(strcmp(token, "off") == 0)
			status_disable();
		else
			status_print();
	}
	else if((strcmp(token, "debug") == 0) || (strcmp(token, "d") == 0)) {
		token = get_token(&str);
		if(strcmp(token, "clocks") == 0)
			debug_clocks();
#ifdef CSR_GENERATOR_BASE
		else if(strcmp(token, "sdram_test") == 0) bist_test();
#endif
#ifdef CSR_HDMI_IN0_BASE
		else if(strcmp(token, "input0") == 0) {
			token = get_token(&str);
			if(strcmp(token, "off") == 0)
				hdmi_in0_debug = 0;
			else if(strcmp(token, "on") == 0)
				hdmi_in0_debug = 1;
			else
				hdmi_in0_debug = !hdmi_in0_debug;
			wprintf("HDMI Input 0 debug %s\n", hdmi_in0_debug ? "on" : "off");
		}
#endif
#ifdef CSR_HDMI_IN1_BASE
		else if(strcmp(token, "input1") == 0) {
			token = get_token(&str);
			if(strcmp(token, "off") == 0)
				hdmi_in1_debug = 0;
			else if(strcmp(token, "on") == 0)
				hdmi_in1_debug = 1;
			else
				hdmi_in1_debug = !hdmi_in1_debug;
			wprintf("HDMI Input 1 debug %s\n", hdmi_in1_debug ? "on" : "off");
		}
#endif
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
		else if(strcmp(token, "ddr") == 0) {
			debug_ddr();
			wputchar('\n');
		}
#endif
#ifdef CSR_INFO_DNA_ID_ADDR
		else if(strcmp(token, "dna") == 0) {
			print_board_dna();
			wputchar('\n');
		}
#endif
#ifdef CSR_OPSIS_I2C_MASTER_W_ADDR
		else if(strcmp(token, "opsis_eeprom") == 0) {
			opsis_eeprom_dump();
		}
#endif
#ifdef CSR_TOFE_I2C_W_ADDR
		else if(strcmp(token, "tofe_eeprom") == 0) {
			tofe_eeprom_dump();
		}
#endif
#ifdef CSR_OPSIS_I2C_FX2_RESET_OUT_ADDR
		else if(strcmp(token, "fx2_reboot") == 0) {
			token = get_token(&str);
			if(strcmp(token, "usbjtag") == 0) {
				fx2_reboot(FX2FW_USBJTAG);
			}
#ifdef ENCODER_BASE
			else if (strcmp(token, "hdmi2usb") == 0) {
				fx2_reboot(FX2FW_HDMI2USB);
			}
#endif
			else {
				fx2_debug();
			}
		}
#endif
		else if(strcmp(token, "edid") == 0) {
			unsigned int found = 0;
			token = get_token(&str);
#ifdef CSR_HDMI_OUT0_I2C_W_ADDR
			if(strcmp(token, "output0") == 0) {
				found = 1;
				hdmi_out0_print_edid();
			}
#endif
#ifdef CSR_HDMI_OUT1_I2C_W_ADDR
			if(strcmp(token, "output1") == 0) {
				found = 1;
				hdmi_out1_print_edid();
			}
#endif
			if(found == 0)
				wprintf("%s port has no EDID capabilities\n", token);
#ifdef CSR_CAS_BASE
		} else if(strcmp(token, "cas") == 0) {
			token = get_token(&str);
			if (false) { }
#ifdef CSR_CAS_LEDS_OUT_ADDR
			else if(strcmp(token, "leds") == 0) {
				token = get_token(&str);
				cas_leds_out_write(atoi(token));
			}
#endif
#ifdef CSR_CAS_SWITCHES_IN_ADDR
			else if(strcmp(token, "switches") == 0) {
				wprintf("%X\n", (int)cas_switches_in_read());
			}
#endif
#ifdef CSR_CAS_BUTTONS_EV_STATUS_ADDR
			else if(strcmp(token, "buttons") == 0) {
				int status = cas_buttons_ev_status_read();
				int pending = cas_buttons_ev_pending_read();
				wprintf("%X %X\n", status, pending);
				token = get_token(&str);
				if(strcmp(token, "clear") == 0) {
					cas_buttons_ev_pending_write(pending);
				}
			}
#endif
#endif
		} else
			help_debug();

	} else if(strcmp(token, "version") == 0) {
		print_version();
	} else {
		if(status_enabled)
			status_disable();
	}
	ci_prompt();
}
