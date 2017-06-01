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
#include "processor.h"
#include "pattern.h"
#include "mdio.h"

static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {192, 168, 1, 50};

// FIXME
static void hdmi_out_mmcm_write(uint8_t address, uint16_t data) {
	hdmi_out_driver_clocking_mmcm_adr_write(address);
    hdmi_out_driver_clocking_mmcm_dat_w_write(data);
    hdmi_out_driver_clocking_mmcm_write_write(1);
    while (hdmi_out_driver_clocking_mmcm_drdy_read() == 0);
}

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();
#ifdef CSR_HDMI_OUT_I2C_W_ADDR
	hdmi_out_i2c_init();
#endif

	puts("\nOpsis CPU testing software built "__DATE__" "__TIME__);

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

	// FIXME
	hdmi_out_mmcm_write(0x8, 0x1000 + (10 << 6)  + 10);
    hdmi_out_mmcm_write(0xa, 0x1000 + (2  << 6) + 2);

	processor_init();
#ifdef CSR_HDMI_OUT_BASE
	processor_set_hdmi_out_source(VIDEO_IN_PATTERN);
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
