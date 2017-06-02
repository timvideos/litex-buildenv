#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include "flags.h"
#include <console.h>
#include <system.h>

#include "config.h"
#include "ci.h"
#include "ethernet.h"
#include "etherbone.h"
#include "telnet.h"
#include "oled.h"
#include "processor.h"
#include "pattern.h"
#include "mdio.h"

static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {192, 168, 1, 50};

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();
#ifdef CSR_HDMI_OUT0_I2C_W_ADDR
	hdmi_out0_i2c_init();
#endif

	puts("\nNexys CPU testing software built "__DATE__" "__TIME__);

#ifdef CSR_OLED_BASE
	oled_init();
	oled_refresh();
	printf("here!");
#endif

	config_init();
	time_init();

#ifdef CSR_ETHPHY_MDIO_W_ADDR
	mdio_status();
#endif

#ifdef ETHMAC_BASE
	ethernet_init(mac_addr, ip_addr);
	etherbone_init();
	telnet_init();
#endif

	processor_init();
#ifdef CSR_HDMI_OUT0_BASE
	processor_set_hdmi_out0_source(VIDEO_IN_PATTERN);
#endif
	processor_update();
	processor_start(config_get(CONFIG_KEY_RESOLUTION));

	ci_prompt();
	while(1) {
		processor_service();
		ci_service();
#ifdef ETHMAC_BASE
		ethernet_service();
#endif
		pattern_service();
	}

	return 0;
}
