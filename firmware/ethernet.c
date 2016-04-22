// This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#include "ethernet.h"
#include <generated/csr.h>
#include <generated/mem.h>
#include <time.h>

static int uip_periodic_event;
static int uip_periodic_period;

static int uip_arp_event;
static int uip_arp_period;

void uip_log(char *msg)
{
#ifdef UIP_DEBUG
    puts(msg);
#endif
}

#ifdef ETHMAC_BASE

void ethernet_init(const unsigned char * mac_addr, const unsigned char *ip_addr)
{
	int i;
	uip_ipaddr_t ipaddr;

	/* init ethernet mac */
	clock_init();
	liteethmac_init();

	/* uip periods */
	uip_periodic_period = SYSTEM_CLOCK_FREQUENCY/100; /*  10 ms */
	uip_arp_period = SYSTEM_CLOCK_FREQUENCY/10;       /* 100 ms */

	/* init uip */
	process_init();
	process_start(&etimer_process, NULL);
	uip_init();

	/* configure mac / ip */
	for (i=0; i<6; i++) uip_lladdr.addr[i] = mac_addr[i];
	uip_ipaddr(&ipaddr, ip_addr[0], ip_addr[1], ip_addr[2], ip_addr[3]);
	uip_sethostaddr(&ipaddr);

	printf("uIP init done with ip %d.%d.%d.%d\n", ip_addr[0], ip_addr[1], ip_addr[2], ip_addr[3]);
}

void ethernet_service(void) {
	int i;
	struct uip_eth_hdr *buf = (struct uip_eth_hdr *)&uip_buf[0];

	etimer_request_poll();
	process_run();

	uip_len = liteethmac_poll();
	if(uip_len > 0) {
		if(buf->type == uip_htons(UIP_ETHTYPE_IP)) {
			uip_arp_ipin();
			uip_input();
			if(uip_len > 0) {
				uip_arp_out();
				liteethmac_send();
			}
		} else if(buf->type == uip_htons(UIP_ETHTYPE_ARP)) {
			uip_arp_arpin();
			if(uip_len > 0)
				liteethmac_send();
		}
	} else if (elapsed(&uip_periodic_event, uip_periodic_period)) {
		for(i = 0; i < UIP_CONNS; i++) {
			uip_periodic(i);

			if(uip_len > 0) {
				uip_arp_out();
				liteethmac_send();
			}
		}
	}
	if (elapsed(&uip_arp_event, uip_arp_period)) {
		uip_arp_timer();
	}
}

#endif