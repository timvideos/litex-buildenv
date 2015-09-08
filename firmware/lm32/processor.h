#ifndef __PROCESSOR_H
#define __PROCESSOR_H

#define PROCESSOR_MODE_COUNT 11
#define PROCESSOR_MODE_DESCLEN 32

enum {
	VIDEO_IN_HDMI_IN0=0,
	VIDEO_IN_HDMI_IN1,
	VIDEO_IN_PATTERN
};

enum {
	VIDEO_OUT_HDMI_OUT0=0,
	VIDEO_OUT_HDMI_OUT1,
	VIDEO_OUT_ENCODER
};

extern int processor_mode;
int processor_h_active;
int processor_v_active;
int processor_refresh;
int processor_hdmi_out0_source;
int processor_hdmi_out1_source;
int processor_encoder_source;
char processor_buffer[16];

void processor_list_modes(char *mode_descriptors);
void processor_init(void);
void processor_start(int mode);
void processor_set_hdmi_out0_source(int source);
void processor_set_hdmi_out1_source(int source);
void processor_set_encoder_source(int source);
char * processor_get_source_name(int source);
void processor_update(void);
void processor_service(void);

#endif /* __PROCESSOR_H */
