// This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#ifndef __ETHERNET_H
#define __ETHERNET_H

#include "contiki.h"
#include "contiki-net.h"
#include "liteethmac-drv.h"

//#define UIP_DEBUG

#define max(a,b) ((a>b)?a:b)
#define min(a,b) ((a<b)?a:b)

void uip_log(char *msg);
void ethernet_init(const unsigned char * mac_addr, const unsigned char *ip_addr);
void ethernet_service(void);

#endif
