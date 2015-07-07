#include <stdio.h>

#include <console.h>
#include <generated/csr.h>
#include <generated/mem.h>

#include "config.h"
#include "dvisampler.h"
#include "processor.h"
#include "pll.h"
#include "ci.h"
#include "encoder.h"

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

static void list_video_modes(void)
{
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];
	int i;

	processor_list_modes(mode_descriptors);
	printf("==== Available video modes ====\n");
	for(i=0;i<PROCESSOR_MODE_COUNT;i++)
		printf(" %d: %s\n", i, &mode_descriptors[i*PROCESSOR_MODE_DESCLEN]);
	printf("===============================\n");
}

void ci_service(void)
{
	int c;
	char mode_descriptors[PROCESSOR_MODE_COUNT*PROCESSOR_MODE_DESCLEN];

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
			case 'F':
				fb_fi_enable_write(1);
				printf("framebuffer is ON\n");
				break;
			case 'f':
				fb_fi_enable_write(0);
				printf("framebuffer is OFF\n");
				break;
#ifdef CSR_SDRAM_CONTROLLER_BANDWIDTH_UPDATE_ADDR
			case 'm':
				print_mem_bandwidth();
				break;
#endif
			case 'p':
				pll_dump();
				break;
			case 's':
				processor_list_modes(mode_descriptors);
				printf("Revision %08x built "__DATE__" "__TIME__"\n", MSC_GIT_ID);
				printf("Video mode: %s\n", &mode_descriptors[processor_mode*PROCESSOR_MODE_DESCLEN]);
				break;
#ifdef ENCODER_BASE
			case 'e':
				printf("Start Encoding video buffer...");
				encoder_init(luma_rom_50, chroma_rom_50);
				encoder_start(processor_h_active, processor_v_active);
				encoder_reader_ev_pending_write(encoder_reader_ev_pending_read());
				encoder_reader_ev_enable_write(1);
				encoder_reader_dma_base_write(0);
				encoder_reader_dma_length_write(processor_h_active*processor_v_active*4);
				encoder_reader_dma_shoot_write(1);
				while(encoder_reader_dma_busy_read()==1);
				while(encoder_done()==0);
				printf("done\n");
				break;
#endif
			case 'r':
			    asm("call r0");
				break;
		}
	}
}
