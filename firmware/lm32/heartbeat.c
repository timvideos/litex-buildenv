
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


void hb_status(int val){
	
	if(val==1)  { heartbeat_status = 1; }
	else heartbeat_status = 0;
		
}


void hb_service(int h_active, int v_active, int source)
{
	if (heartbeat_status==1)
	{
		
		static int last_event;
		static int counter;
		
		if(elapsed(&last_event, identifier_frequency_read()/5)) {
			if(counter==1){
				hb_fill(h_active, v_active, 0, source);
				counter = 0;
			}
			else {
				hb_fill(h_active, v_active, 1, source);
				counter = 1;
			}
		}
	}
}

void hb_fill(int h_active, int v_active, int n, int source)
{
	
	int addr, i, j;
	volatile unsigned int *framebuffer;
	
	if (source == HDMI_IN0_SOURCE) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + hdmi_in0_framebuffer_base(hdmi_in0_fb_index));
	}
	else if (source == HDMI_IN1_SOURCE ) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + hdmi_in1_framebuffer_base(hdmi_in1_fb_index));
	}
	else {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + pattern_framebuffer_base());
	}
	
	/*
	8x8 pixel square at right bottom corner
	Toggles between red and blue
	*/

	addr = 0 + (h_active/2)*(v_active-10) + (h_active/2) - 5;
	
	for (i=0; i<4; i++){
		for (j=0; j<8; j++){
			if(n==1)	
				framebuffer[addr+i+(h_active/2)*j] = YCBCR422_RED;
			else if (n==0) 
				framebuffer[addr+i+(h_active/2)*j] = YCBCR422_BLUE;
		}
	}
	
}