#ifndef __HEARTBEAT_H
#define __HEARTBEAT_H

#define HDMI_IN0_SOURCE 0
#define HDMI_IN1_SOURCE 1
#define PATTERN_SOURCE 2

void hb_status(int val);
void hb_service(int h_active, int v_active, int source) ;
void hb_fill(int h_active, int v_active, int n, int source);

#endif /* __HEARTBEAT_H */
