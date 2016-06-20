
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <system.h>
#include <time.h>

#include "heartbeat.h"
#include "processor.h"
#include "hdmi_in0.h"
#include "hdmi_in1.h"
#include "pattern.h"

static const unsigned int color_bar[8] = {
	YCBCR422_WHITE,
	YCBCR422_YELLOW,
	YCBCR422_CYAN,
	YCBCR422_GREEN,
	YCBCR422_PURPLE,
	YCBCR422_RED,
	YCBCR422_BLUE,
	YCBCR422_BLACK
};

static int heartbeat_status = 0;

void hb_status(int val)
{
	if(val==1) { 
		heartbeat_status = 1; 
	}
	else {
		heartbeat_status = 0;
	}		
}

void hb_service(int source)
{
	static int last_event;
	static int counter;		
	
	if (heartbeat_status==1) {	

		if(elapsed(&last_event, identifier_frequency_read()/5)) {
			hb_fill(counter, source);
			counter = (counter+1)%8	;
		}
	}
}

void hb_fill(int color_v, int source)
{
	int addr, i, j;
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + pattern_framebuffer_base());

#ifdef CSR_HDMI_IN0_BASE
	if (source == VIDEO_IN_HDMI_IN0) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + hdmi_in0_framebuffer_base(hdmi_in0_fb_index));
	}
#endif
#ifdef CSR_HDMI_IN1_BASE
	if (source == VIDEO_IN_HDMI_IN1) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + hdmi_in1_framebuffer_base(hdmi_in1_fb_index));
	}
#endif
	if (source == VIDEO_IN_PATTERN) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + pattern_framebuffer_base());
	}
	/*
	8x8 pixel square at right bottom corner
	8 pixel = 4 memory locations in horizoantal
	8 pixel = 8 memory locations in vertical
	Toggles between red and blue
	*/
	addr = 0 + (processor_h_active/2)*(processor_v_active-8) + (processor_h_active/2) - 4;
	
	for (i=0; i<4; i++){
		for (j=0; j<8; j++){
			framebuffer[addr+i+(processor_h_active/2)*j] = color_bar[color_v];
/*			if(color_v==1)	
				framebuffer[addr+i+(processor_h_active/2)*j] = YCBCR422_RED;
			else if (color_v==0) 
				framebuffer[addr+i+(processor_h_active/2)*j] = YCBCR422_BLUE;
*/
		}
	}	
}
