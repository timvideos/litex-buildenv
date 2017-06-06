#ifndef __HDMI_IN0_H
#define __HDMI_IN0_H

extern int hdmi_in0_debug;
extern int hdmi_in0_fb_index;

unsigned int hdmi_in0_framebuffer_base(char n);

void hdmi_in0_isr(void);
void hdmi_in0_init_video(int hres, int vres);
void hdmi_in0_disable(void);
void hdmi_in0_clear_framebuffers(void);
void hdmi_in0_print_status(void);
int hdmi_in0_calibrate_delays(int freq);
int hdmi_in0_adjust_phase(void);
int hdmi_in0_init_phase(void);
int hdmi_in0_phase_startup(int freq);
void hdmi_in0_service(int freq);

#endif
