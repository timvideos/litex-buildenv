#ifndef __DVISAMPLER1_H
#define __DVISAMPLER1_H

extern int dvisampler1_debug;
extern int dvisampler1_fb_index;

unsigned int dvisampler1_framebuffer_base(char n);

void dvisampler1_isr(void);
void dvisampler1_init_video(int hres, int vres);
void dvisampler1_disable(void);
void dvisampler1_clear_framebuffers(void);
void dvisampler1_print_status(void);
int dvisampler1_calibrate_delays(void);
int dvisampler1_adjust_phase(void);
int dvisampler1_init_phase(void);
int dvisampler1_phase_startup(void);
void dvisampler1_service(void);

#endif
