#ifndef __HEARTBEAT_H
#define __HEARTBEAT_H

typedef enum { false, true } bool;

void hb_status(int val);
void hb_service(int source) ;
void hb_fill(bool color_v, int source);

#endif /* __HEARTBEAT_H */
