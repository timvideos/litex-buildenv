#ifndef __DVISAMPLER0_H
#define __DVISAMPLER0_H

extern int dvisampler0_debug;
extern int dvisampler0_fb_index;

unsigned int dvisampler0_framebuffer_base(char n);

void dvisampler0_isr(void);
void dvisampler0_init_video(int hres, int vres);
void dvisampler0_disable(void);
void dvisampler0_clear_framebuffers(void);
void dvisampler0_print_status(void);
int dvisampler0_calibrate_delays(void);
int dvisampler0_adjust_phase(void);
int dvisampler0_init_phase(void);
int dvisampler0_phase_startup(void);
void dvisampler0_service(void);

#endif
