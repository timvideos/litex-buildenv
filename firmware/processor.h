#ifndef __PROCESSOR_H
#define __PROCESSOR_H

#define PROCESSOR_MODE_COUNT 10
#define PROCESSOR_MODE_DESCLEN 32

extern int processor_mode;
int processor_h_active;
int processor_v_active;
void processor_list_modes(char *mode_descriptors);
void processor_start(int mode);
void processor_service(void);

#endif /* __VIDEOMODE_H */
