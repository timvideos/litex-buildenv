#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <console.h>
#include <system.h>

#include "ci.h"
#include "ethernet.h"
#include "etherbone.h"
#include "telnet.h"
#include "mdio.h"


static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {192, 168, 1, 50};

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nArty CPU testing software built "__DATE__" "__TIME__);

	time_init();

#ifdef CSR_ETHPHY_MDIO_W_ADDR
	mdio_status();
#endif

#ifdef ETHMAC_BASE
	ethernet_init(mac_addr, ip_addr);
	etherbone_init();
	telnet_init();
#endif
	ci_prompt();
	while(1) {
		ci_service();
#ifdef ETHMAC_BASE
		ethernet_service();
#endif
	}

	return 0;
}

