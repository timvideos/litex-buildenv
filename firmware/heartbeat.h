#ifndef __HEARTBEAT_H
#define __HEARTBEAT_H

#include <stdbool.h>
#include "framebuffer.h"

void hb_status(bool val);
void hb_service(fb_ptrdiff_t fb_offset) ;
void hb_fill(bool color_v, fb_ptrdiff_t fb_offset);

#endif /* __HEARTBEAT_H */
