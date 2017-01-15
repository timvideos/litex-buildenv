#ifndef __CI_H
#define __CI_H

void ci_prompt(void);
void ci_service(void);

#ifdef CSR_HDMI_OUT0_BASE
void output0_on(void);
void output0_off(void);
#endif

#ifdef CSR_HDMI_OUT1_BASE
void output1_on(void);
void output1_off(void);
#endif

#ifdef CSR_HDMI_IN0_BASE
void input0_on(void);
void input0_off(void);
#endif

#ifdef CSR_HDMI_IN1_BASE
void input1_on(void);
void input1_off(void);
#endif

#ifdef ENCODER_BASE
void encoder_on(void);
void encoder_configure_quality(int quality);
void encoder_configure_fps(int fps);
void encoder_off(void);
#endif

#endif
