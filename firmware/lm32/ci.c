#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <time.h>

#include "config.h"
#include "dvisampler0.h"
#include "dvisampler1.h"
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

static void help_framebuffer(char banner)
{
	if(banner)
		help_banner();
	puts("framebuffer <source>       - select framebuffer source and enable it");
	puts("framebuffer off            - disable framebuffer");
	puts("");
}

static void help_encoder(char banner)
{
	if(banner)
		help_banner();
	puts("encoder <source> <quality> - select encoder source, quality and enable it");
	puts("encoder off                - disable encode");
	puts("");
}

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
	puts("status <on/off>            - enable/disable status message");
	puts("");
	help_video_mode(0);
	help_framebuffer(0);
	help_encoder(0);
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
			printf("video source 0: %dx%d",	dvisampler0_resdetection_hres_read(),
											dvisampler0_resdetection_vres_read());
			printf("\n");

			printf("video source 1: %dx%d",	dvisampler1_resdetection_hres_read(),
											dvisampler1_resdetection_vres_read());
			printf("\n");

			printf("framebuffer: ");
			if(fb_fi_enable_read())
				printf("%dx%d from video source %d", 	processor_h_active,
														processor_v_active,
														processor_framebuffer_source);
			else
				printf("off");
			printf("\n");

#ifdef ENCODER_BASE
			printf("encoder: ");
			if(encoder_enabled)
				printf("%dx%d @ %dfps from video source %d, q: %d",	processor_h_active,
																	processor_v_active,
																	encoder_fps,
																	processor_framebuffer_source,
																	encoder_quality);
			else
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

static void framebuffer_set(int source)
{
	if(source <= VIDEO_IN_DVISAMPLER1)
		printf("Enabling framebuffer on video source %d\n", source);
		processor_set_framebuffer_source(source);
		processor_update();
		fb_fi_enable_write(1);
}

static void framebuffer_disable(void)
{
	printf("Disabling framebuffer\n");
	fb_fi_enable_write(0);
}

static void encoder_set(int quality, int source)
{
	if(source <= VIDEO_IN_DVISAMPLER1)
		printf("Enabling encoder on video source %d with %d quality\n", source, quality);
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

static void debug_pll(void)
{
	pll_dump();
}

static void debug_ddr(void)
{
	unsigned long long int nr, nw;
	unsigned long long int f;
	unsigned int rdb, wrb;

	sdram_controller_bandwidth_update_write(1);
	nr = sdram_controller_bandwidth_nreads_read();
	nw = sdram_controller_bandwidth_nwrites_read();
	f = identifier_frequency_read();
	rdb = (nr*f >> (24 - 6))/1000000ULL;
	wrb = (nw*f >> (24 - 6))/1000000ULL;
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
		else if (strcmp(token, "framebuffer") == 0)
			help_framebuffer(1);
		else if (strcmp(token, "encoder") == 0)
			help_encoder(1);
		else if (strcmp(token, "debug") == 0)
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
	else if(strcmp(token, "framebuffer") == 0) {
		token = get_token(&str);
		if(strcmp(token, "off") == 0)
			framebuffer_disable();
		else
			framebuffer_set(atoi(token));
	}
	else if(strcmp(token, "encoder") == 0) {
		token = get_token(&str);
		if(strcmp(token, "off") == 0)
			encoder_disable();
		else
			encoder_set(atoi(token), atoi(get_token(&str)));
	}
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
	}

	ci_prompt();
}
