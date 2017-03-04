#ifndef __HDMI_IN1_H
#define __HDMI_IN1_H

extern int hdmi_in1_debug;
extern int hdmi_in1_fb_index;

unsigned int hdmi_in1_framebuffer_base(char n);

void hdmi_in1_isr(void);
void hdmi_in1_init_video(int hres, int vres);
void hdmi_in1_disable(void);
void hdmi_in1_clear_framebuffers(void);
void hdmi_in1_print_status(void);
int hdmi_in1_calibrate_delays(void);
int hdmi_in1_adjust_phase(void);
int hdmi_in1_init_phase(void);
int hdmi_in1_phase_startup(void);
void hdmi_in1_service(void);

#endif
