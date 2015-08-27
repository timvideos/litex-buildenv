#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/sdram_phy.h>
#include <time.h>

#include "config.h"
#include "hdmi_in0.h"
#include "hdmi_in1.h"
#include "processor.h"
#include "pll.h"
#include "ci.h"
#include "encoder.h"

int status_enabled;

static void help_banner(void)
{
	puts("Available commands:");
}

static void help_video_mode(char banner)
{
	if(banner)
		help_banner();
	puts("video_mode list            - list available video modes");
	puts("video_mode <mode>          - select video mode");
	puts("");
}

static void help_hdp_toggle(char banner)
{
	if(banner)
		help_banner();
	puts("hdp_toggle <source>        - toggle HDP on source for EDID rescan");
	puts("");
}

static void help_hdmi_out0(char banner)
{
	if(banner)
		help_banner();
	puts("hdmi_out0 <source>         - select hdmi_out0 source and enable it");
	puts("hdmi_out0 off              - disable hdmi_out0");
	puts("");
}

static void help_hdmi_out1(char banner)
{
	if(banner)
		help_banner();
	puts("hdmi_out1 <source>         - select hdmi_out1 source and enable it");
	puts("hdmi_out1 off              - disable hdmi_out1");
	puts("");
}

#ifdef ENCODER_BASE
static void help_encoder(char banner)
{
	if(banner)
		help_banner();
	puts("encoder <quality> <source> - select encoder source, quality and enable it");
	puts("encoder off                - disable encode");
	puts("");
}
#endif

static void help_debug(char banner)
{
	if(banner)
		help_banner();
	puts("debug pll                  - dump pll configuration");
	puts("debug ddr                  - show DDR bandwidth");
	puts("");
}

static void help(void)
{
	help_banner();
	puts("help                       - this command");
	puts("version                    - firmware/gateware version");
	puts("reboot                     - reboot CPU");
	puts("status <on/off>            - enable/disable status message (same with by pressing enter)");
	puts("");
	help_video_mode(0);
	help_hdp_toggle(0);
	help_hdmi_out0(0);
	help_hdmi_out1(0);
#ifdef ENCODER_BASE
	help_encoder(0);
#endif
	help_debug(0);
}

static void version(void)
{
	printf("gateware revision: %08x\n", identifier_revision_read());
	printf("firmware revision: %08x, built "__DATE__" "__TIME__"\n", MSC_GIT_ID);
}

static void reboot(void)
{
	asm("call r0");
}

static void status_enable(void)
{
	printf("Enabling status\n");
	status_enabled = 1;
#ifdef ENCODER_BASE
	encoder_nwrites_clear_write(1);
#endif
}

static void status_disable(void)
{
	printf("Disabling status\n");
	status_enabled = 0;
}

static void debug_ddr(void);

static void status_service(void)
{
	static int last_event;

	if(elapsed(&last_event, identifier_frequency_read())) {
		if(status_enabled) {
			printf("\n");
			printf("hdmi_in0:  %dx%d",	hdmi_in0_resdetection_hres_read(),
										hdmi_in0_resdetection_vres_read());
			printf("\n");

			printf("hdmi_in1:  %dx%d",	hdmi_in1_resdetection_hres_read(),
										hdmi_in1_resdetection_vres_read());
			printf("\n");

			printf("hdmi_out0: ");
			if(hdmi_out0_fi_enable_read())
				printf("%dx%d from hdmi_in%d", 	processor_h_active,
												processor_v_active,
												processor_hdmi_out0_source);
			else
				printf("off");
			printf("\n");

			printf("hdmi_out1: ");
			if(hdmi_out1_fi_enable_read())
				printf("%dx%d from hdmi_in%d", 	processor_h_active,
												processor_v_active,
												processor_hdmi_out1_source);
			else
				printf("off");
			printf("\n");

#ifdef ENCODER_BASE
			printf("encoder: ");
			if(encoder_enabled) {
				printf("%dx%d @ %dfps (%dMbps) from hdmi_in%d (q: %d)",
					processor_h_active,
					processor_v_active,
					encoder_fps,
					encoder_nwrites_read()*8/1000000,
					processor_encoder_source,
					encoder_quality);
				encoder_nwrites_clear_write(1);
			} else
				printf("off");
			printf("\n");
#endif
			printf("ddr: ");
			debug_ddr();
		}
	}
}

static void video_mode_list(void)
{
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];
	int i;

	processor_list_modes(mode_descriptors);
	printf("Available video modes:\n");
	for(i=0;i<PROCESSOR_MODE_COUNT;i++)
		printf("mode %d: %s\n", i, &mode_descriptors[i*PROCESSOR_MODE_DESCLEN]);
	printf("\n");
}

static void video_mode_set(int mode)
{
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];
	if(mode < PROCESSOR_MODE_COUNT) {
		processor_list_modes(mode_descriptors);
		printf("Setting video mode to %s\n", &mode_descriptors[mode*PROCESSOR_MODE_DESCLEN]);
		config_set(CONFIG_KEY_RESOLUTION, mode);
		processor_start(mode);
	}
}

static void hdp_toggle(int source)
{
	int i;
	printf("Toggling HDP on hdmi_in%d\n", source);
	if(source ==  VIDEO_IN_HDMI_IN0) {
		hdmi_in0_edid_hpd_en_write(0);
		for(i=0; i<65536; i++);
		hdmi_in0_edid_hpd_en_write(1);
	}
	else if(source == VIDEO_IN_HDMI_IN1) {
		hdmi_in1_edid_hpd_en_write(0);
		for(i=0; i<65536; i++);
		hdmi_in1_edid_hpd_en_write(1);
	}
}

static void hdmi_out0_set(int source)
{
	if(source <= VIDEO_IN_HDMI_IN1)
		printf("Enabling hdmi_out0 from hdmi_in%d\n", source);
		processor_set_hdmi_out0_source(source);
		processor_update();
		hdmi_out0_fi_enable_write(1);
}

static void hdmi_out0_disable(void)
{
	printf("Disabling hdmi_out0\n");
	hdmi_out0_fi_enable_write(0);
}

static void hdmi_out1_set(int source)
{
	if(source <= VIDEO_IN_HDMI_IN1)
		printf("Enabling hdmi_out1 from hdmi_in%d\n", source);
		processor_set_hdmi_out1_source(source);
		processor_update();
		hdmi_out1_fi_enable_write(1);
}

static void hdmi_out1_disable(void)
{
	printf("Disabling hdmi_out1\n");
	hdmi_out1_fi_enable_write(0);
}

#ifdef ENCODER_BASE
static void encoder_set(int quality, int source)
{
	if(source <= VIDEO_IN_HDMI_IN1)
		printf("Enabling encoder from hdmi_in%d with %d quality\n", source, quality);
		processor_set_encoder_source(source);
		processor_update();
		if(encoder_set_quality(quality))
			encoder_enable(1);
}

static void encoder_disable(void)
{
	printf("Disabling encoder\n");
	encoder_enable(0);
}
#endif

static void debug_pll(void)
{
	pll_dump();
}

static unsigned int log2(unsigned int v)
{
	unsigned int r = 0;
	while(v>>=1) r++;
	return r;
}

static void debug_ddr(void)
{
	unsigned long long int nr, nw;
	unsigned long long int f;
	unsigned int rdb, wrb;
	unsigned int burstbits;

	sdram_controller_bandwidth_update_write(1);
	nr = sdram_controller_bandwidth_nreads_read();
	nw = sdram_controller_bandwidth_nwrites_read();
	f = identifier_frequency_read();
	burstbits = (2*DFII_NPHASES) << DFII_PIX_DATA_SIZE;
	rdb = (nr*f >> (24 - log2(burstbits)))/1000000ULL;
	wrb = (nw*f >> (24 - log2(burstbits)))/1000000ULL;
	printf("read:%5dMbps  write:%5dMbps  all:%5dMbps\n", rdb, wrb, rdb + wrb);
}

static char *readstr(void)
{
	char c[2];
	static char s[64];
	static int ptr = 0;

	if(readchar_nonblock()) {
		c[0] = readchar();
		c[1] = 0;
		switch(c[0]) {
			case 0x7f:
			case 0x08:
				if(ptr > 0) {
					ptr--;
					putsnonl("\x08 \x08");
				}
				break;
			case 0x07:
				break;
			case '\r':
			case '\n':
				s[ptr] = 0x00;
				putsnonl("\n");
				ptr = 0;
				return s;
			default:
				if(ptr >= (sizeof(s) - 1))
					break;
				putsnonl(c);
				s[ptr] = c[0];
				ptr++;
				break;
		}
	}
	return NULL;
}

static char *get_token(char **str)
{
	char *c, *d;

	c = (char *)strchr(*str, ' ');
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


void ci_prompt(void)
{
	printf("HDMI2USB>");
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
		token = get_token(&str);
		if(strcmp(token, "video_mode") == 0)
			help_video_mode(1);
		else if(strcmp(token, "hdp_toggle") == 0)
			help_hdp_toggle(1);
		else if(strcmp(token, "hdmi_out0") == 0)
			help_hdmi_out0(1);
		else if(strcmp(token, "hdmi_out1") == 0)
			help_hdmi_out1(1);
#ifdef ENCODER_BASE
		else if(strcmp(token, "encoder") == 0)
			help_encoder(1);
#endif
		else if(strcmp(token, "debug") == 0)
			help_debug(1);
		else
			help();
	}
	else if(strcmp(token, "reboot") == 0) reboot();
	else if(strcmp(token, "version") == 0) version();
	else if(strcmp(token, "video_mode") == 0) {
		token = get_token(&str);
		if(strcmp(token, "list") == 0)
			video_mode_list();
		else
			video_mode_set(atoi(token));
	}
	else if(strcmp(token, "hdp_toggle") == 0) {
		token = get_token(&str);
		hdp_toggle(atoi(token));
	}
	else if(strcmp(token, "hdmi_out0") == 0) {
		token = get_token(&str);
		if(strcmp(token, "off") == 0)
			hdmi_out0_disable();
		else
			hdmi_out0_set(atoi(token));
	}
	else if(strcmp(token, "hdmi_out1") == 0) {
		token = get_token(&str);
		if(strcmp(token, "off") == 0)
			hdmi_out1_disable();
		else
			hdmi_out1_set(atoi(token));
	}
#ifdef ENCODER_BASE
	else if(strcmp(token, "encoder") == 0) {
		token = get_token(&str);
		if(strcmp(token, "off") == 0)
			encoder_disable();
		else
			encoder_set(atoi(token), atoi(get_token(&str)));
	}
#endif
	else if(strcmp(token, "status") == 0) {
		token = get_token(&str);
		if(strcmp(token, "off") == 0)
			status_disable();
		else
			status_enable();
	}
	else if(strcmp(token, "debug") == 0) {
		token = get_token(&str);
		if(strcmp(token, "pll") == 0)
			debug_pll();
		else if(strcmp(token, "ddr") == 0)
			debug_ddr();
	} else {
		if(status_enabled)
			status_disable();
	}

	ci_prompt();
}
