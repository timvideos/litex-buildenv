#ifndef __HEARTBEAT_H
#define __HEARTBEAT_H

#include <stdbool.h>

void hb_status(bool val);
void hb_service(int sink) ;
void hb_fill(bool color_v, int sink);

#endif /* __HEARTBEAT_H */
