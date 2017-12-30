#include <stdbool.h>
#include "framebuffer.h"

#ifndef __HDMI_IN0_H
#define __HDMI_IN0_H

#ifdef HDMI_IN0_INDEX
#error "HDMI_IN0_INDEX already defined!"
#endif

#define HDMI_IN0_INDEX 			0
#define HDMI_IN0_FRAMEBUFFERS_BASE 	FRAMEBUFFER_BASE_HDMI_INPUT(HDMI_IN0_INDEX)

extern int hdmi_in0_debug;
extern int hdmi_in0_fb_index;

fb_ptrdiff_t hdmi_in0_framebuffer_base(char n);

void hdmi_in0_isr(void);
void hdmi_in0_init_video(int hres, int vres);
void hdmi_in0_enable(void);
bool hdmi_in0_status(void);
void hdmi_in0_disable(void);
void hdmi_in0_clear_framebuffers(void);
void hdmi_in0_print_status(void);
int hdmi_in0_calibrate_delays(int freq);
int hdmi_in0_adjust_phase(void);
int hdmi_in0_init_phase(void);
int hdmi_in0_phase_startup(int freq);
void hdmi_in0_service(int freq);

#endif
