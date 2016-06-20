#ifndef __HEARTBEAT_H
#define __HEARTBEAT_H

#define HDMI_IN0_SOURCE 0
#define HDMI_IN1_SOURCE 1
#define PATTERN_SOURCE 2

void hb_status(int val);
void hb_service(int source) ;
void hb_fill(int color_v, int source);

#endif /* __HEARTBEAT_H */
