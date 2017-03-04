
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

static bool heartbeat_status = false;

#define HEARTBEAT_FREQUENCY 1	// In Hertz
#define FILL_RATE 120 			// In Hertz, double the standard frame rate

void hb_status(bool val)
{
	heartbeat_status = val;
}

void hb_service(int sink)
{
	static int last_event;
	static int counter;
	static bool color_v;

	if (heartbeat_status==1) {
		if(elapsed(&last_event, SYSTEM_CLOCK_FREQUENCY/FILL_RATE)) {
			counter = counter+1;
			hb_fill(color_v, sink);
			if(counter > FILL_RATE/(HEARTBEAT_FREQUENCY*2)) {
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

	/*
#ifdef CSR_HDMI_OUT0_BASE
	if (sink == VIDEO_OUT_HDMI_OUT0) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + HDMI_IN0_FRAMEBUFFERS_BASE);
	}
#endif
#ifdef CSR_HDMI_OUT1_BASE
	if (sink == VIDEO_OUT_HDMI_OUT1) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + HDMI_IN1_FRAMEBUFFERS_BASE);
	}
#endif
#ifdef ENCODER_BASE
	if (sink == VIDEO_OUT_ENCODER) {
		framebuffer = (unsigned int *)(MAIN_RAM_BASE + encoder_reader_base_read());
	}
#endif
	*/

	/*
	8x8 pixel square at right bottom corner
	8 pixel = 4 memory locations in horizoantal
	8 pixel = 8 memory locations in vertical
	Toggles between BLUE and RED
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
