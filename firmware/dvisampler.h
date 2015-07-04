#ifndef __DVISAMPLER_H
#define __DVISAMPLER_H

extern int dvisampler_debug;

void dvisampler_isr(void);
void dvisampler_init_video(int hres, int vres);
void dvisampler_disable(void);
void dvisampler_clear_framebuffers(void);
void dvisampler_print_status(void);
int dvisampler_calibrate_delays(void);
int dvisampler_adjust_phase(void);
int dvisampler_init_phase(void);
int dvisampler_phase_startup(void);
void dvisampler_service(void);

#endif
