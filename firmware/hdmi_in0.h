#ifndef __HDMI_IN0_H
#define __HDMI_IN0_H

extern int hdmi_in0_debug;
extern int hdmi_in0_fb_index;

#define DVISAMPLER_TOO_LATE		0x1
#define DVISAMPLER_TOO_EARLY	0x2

#define DVISAMPLER_DELAY_RST	0x1
#define DVISAMPLER_DELAY_INC	0x2
#define DVISAMPLER_DELAY_DEC	0x4

#define DVISAMPLER_SLOT_EMPTY	0
#define DVISAMPLER_SLOT_LOADED	1
#define DVISAMPLER_SLOT_PENDING	2

unsigned int hdmi_in0_framebuffer_base(char n);

void hdmi_in0_isr(void);
void hdmi_in0_init_video(int hres, int vres);
void hdmi_in0_disable(void);
void hdmi_in0_clear_framebuffers(void);
void hdmi_in0_print_status(void);
int hdmi_in0_calibrate_delays(void);
int hdmi_in0_adjust_phase(void);
int hdmi_in0_init_phase(void);
int hdmi_in0_phase_startup(void);
void hdmi_in0_service(void);

#endif
