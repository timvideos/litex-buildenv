#ifndef __HDMI_IN_H
#define __HDMI_IN_H

extern int hdmi_in_debug;
extern int hdmi_in_fb_index;

#define DVISAMPLER_TOO_LATE		0x1
#define DVISAMPLER_TOO_EARLY	0x2

#define DVISAMPLER_DELAY_RST	0x1
#define DVISAMPLER_DELAY_INC	0x2
#define DVISAMPLER_DELAY_DEC	0x4

#define DVISAMPLER_SLOT_EMPTY	0
#define DVISAMPLER_SLOT_LOADED	1
#define DVISAMPLER_SLOT_PENDING	2

unsigned int hdmi_in_framebuffer_base(char n);

void hdmi_in_isr(void);
void hdmi_in_init_video(int hres, int vres);
void hdmi_in_disable(void);
void hdmi_in_clear_framebuffers(void);
void hdmi_in_print_status(void);
int hdmi_in_calibrate_delays(void);
int hdmi_in_adjust_phase(void);
int hdmi_in_init_phase(void);
int hdmi_in_phase_startup(void);
void hdmi_in_service(void);

#endif
