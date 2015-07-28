#include <stdio.h>

#include <console.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <time.h>

#include "config.h"
#include "dvisampler.h"
#include "processor.h"
#include "pll.h"
#include "ci.h"
#include "encoder.h"

int system_status_enabled;

#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
static void print_mem_bandwidth(void)
{
	unsigned long long int nr, nw;
	unsigned long long int f;
	unsigned int rdb, wrb;

	sdram_controller_bandwidth_update_write(1);
	nr = sdram_controller_bandwidth_nreads_read();
	nw = sdram_controller_bandwidth_nwrites_read();
	f = identifier_frequency_read();
	rdb = (nr*f >> (24 - 7))/1000000ULL;
	wrb = (nw*f >> (24 - 7))/1000000ULL;
	printf("read:%5dMbps  write:%5dMbps  all:%5dMbps\n", rdb, wrb, rdb + wrb);
}
#endif

static void help(void)
{
    puts("Available commands:");
    puts("h               - this message");
    puts("D/d             - enable/disable DVI debug");
    puts("E/e             - enable/disable Encoder");
    puts("F/f             - enable/disable Framebuffer");
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
    puts("m               - show memory bandwidth");
#endif
    puts("p               - dump plls configuration");
    puts("r               - reboot CPU");
    puts("S/s             - enable/disable system status");
    puts("v               - show gateware/firmware versions");
    puts("");
}

static void list_video_modes(void)
{
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];
	int i;

	processor_list_modes(mode_descriptors);
	printf("Available video modes:\n");
	for(i=0;i<PROCESSOR_MODE_COUNT;i++)
		printf("mode %d: %s\n", i, &mode_descriptors[i*PROCESSOR_MODE_DESCLEN]);
	printf("\n");
}

static void version(void)
{
	printf("Gateware:\n");
	printf("  revision %08x\n", identifier_revision_read());
	printf("Firmware:\n");
	printf("  revision %08x built "__DATE__" "__TIME__"\n", MSC_GIT_ID);
}

static void system_status(void)
{
	printf("dvi_in: %dx%d",	dvisampler_resdetection_hres_read(),
							dvisampler_resdetection_vres_read());
	printf(" | ");
	if(fb_fi_enable_read())
		printf("dvi_out: %dx%d", processor_h_active,
		    						processor_v_active);
	else
		printf("dvi_out: OFF");
	printf(" | ");
	if(encoder_enabled)
		printf("encoder: %d fps, q: %d", encoder_fps, encoder_quality);
	else
		printf("encoder: OFF");
	printf("\n");
}

void ci_service(void)
{
	int c;
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];

	static int last_event;

	if(elapsed(&last_event, identifier_frequency_read())) {
		if(system_status_enabled)
			system_status();
	}

	if(readchar_nonblock()) {
		c = readchar();
		if((c >= '0') && (c <= '9')) {
			int m;

			m = c - '0';
			if(m < PROCESSOR_MODE_COUNT) {
				processor_list_modes(mode_descriptors);
				printf("Setting video mode to %s\n", &mode_descriptors[m*PROCESSOR_MODE_DESCLEN]);
				config_set(CONFIG_KEY_RESOLUTION, m);
				processor_start(m);
			}
		}
		switch(c) {
			case 'l':
				list_video_modes();
				break;
			case 'D':
				dvisampler_debug = 1;
				printf("DVI sampler debug is ON\n");
				break;
			case 'd':
				dvisampler_debug = 0;
				printf("DVI sampler debug is OFF\n");
				break;
#ifdef ENCODER_BASE
			case 'E':
				encoder_enable(1);
				printf("Encoder is ON\n");
				break;
			case 'e':
				encoder_enable(0);
				printf("Encoder is OFF\n");
				break;
#endif
			case 'F':
				fb_fi_enable_write(1);
				printf("framebuffer is ON\n");
				break;
			case 'f':
				fb_fi_enable_write(0);
				printf("framebuffer is OFF\n");
				break;
			case 'h':
				help();
				break;
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
			case 'm':
				print_mem_bandwidth();
				break;
#endif
			case 'p':
				pll_dump();
				break;
			case 'r':
				asm("call r0");
				break;
			case 'S':
				system_status_enabled = 1;
				printf("Status is ON\n");
				break;
			case 's':
				system_status_enabled = 0;
				printf("Status is OFF\n");
				break;
			case 'v':
				version();
				break;
			case '+':
				encoder_increase_quality();
				printf("Setting encoder quality to %d\n", encoder_quality);
				break;
			case '-':
				encoder_decrease_quality();
				printf("Setting encoder quality to %d\n", encoder_quality);
				break;
		}
	}
}
