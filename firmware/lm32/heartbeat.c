
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

void hb_service(int sink)
{
	static int last_event;
	static int counter;		
	static bool color_v;
	if (heartbeat_status==1) {	
		if(elapsed(&last_event, identifier_frequency_read()/120)) {
			counter = counter+1;
			hb_fill(color_v, sink);
			if(counter>60){
				color_v = !color_v;
				counter = 0;
			}
		}
	}
}

void hb_fill(bool color_v, int sink)
{
	int addr, i, j;
	unsigned int color;

	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + pattern_framebuffer_base());

#ifdef CSR_HDMI_OUT0_BASE
	if (sink == VIDEO_OUT_HDMI_OUT0) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + hdmi_out0_fi_base0_read());
	}
#endif
#ifdef CSR_HDMI_OUT1_BASE
	if (sink == VIDEO_OUT_HDMI_OUT1) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + hdmi_out1_fi_base0_read());
	}
#endif
#ifdef ENCODER_BASE
	if (sink == VIDEO_OUT_ENCODER) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + encoder_reader_base_read());
	}
#endif

	/*
	8x8 pixel square at right bottom corner
	8 pixel = 4 memory locations in horizoantal
	8 pixel = 8 memory locations in vertical
	Toggles between the colors defined in color_bar array from pattern.c
	*/
	if (color_v == 0)
    	color = YCBCR422_BLUE;
	else
    	color = YCBCR422_RED;

	addr = 0 + (processor_h_active/2)*(processor_v_active-8) + (processor_h_active/2) - 4;	
	for (i=0; i<4; i++){
		for (j=0; j<8; j++){
			framebuffer[addr+i+(processor_h_active/2)*j] = color;
		}
	}	
}
