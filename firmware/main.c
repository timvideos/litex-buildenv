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
#include "oled.h"
#include "pattern.h"

static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {192, 168, 1, 50};

/* hdmi_out functions */

static void hdmi_out_write_mmcm_reg(uint32_t address, uint32_t data) {
	hdmi_out0_driver_clocking_drp_addr_write(address);
    hdmi_out0_driver_clocking_drp_di_write(data);
    hdmi_out0_driver_clocking_drp_dwe_write(1);
    hdmi_out0_driver_clocking_drp_den_write(1);
}

static void hdmi_out_config_720p60(void) {
    hdmi_out_write_mmcm_reg(0x8, 0x1000 + (4 << 6)  + 6);
    hdmi_out_write_mmcm_reg(0xa, 0x1000 + (2  << 6) + 2);

    hdmi_out0_core_initiator_hres_write(1280);
    hdmi_out0_core_initiator_hsync_start_write(1390);
    hdmi_out0_core_initiator_hsync_end_write(1430);
    hdmi_out0_core_initiator_hscan_write(1650);

	hdmi_out0_core_initiator_vres_write(720);
    hdmi_out0_core_initiator_vsync_start_write(725);
    hdmi_out0_core_initiator_vsync_end_write(730);
    hdmi_out0_core_initiator_vscan_write(750);

    hdmi_out0_core_initiator_enable_write(0);
    hdmi_out0_core_initiator_base_write(0x00200000);
    hdmi_out0_core_initiator_length_write(1280*720*2);

    hdmi_out0_core_initiator_enable_write(1);
}

/* hdmi_out functions */

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nNexys CPU testing software built "__DATE__" "__TIME__);

#ifdef CSR_ETHPHY_MDIO_W_ADDR
	mdio_status();
#endif

#ifdef ETHMAC_BASE
	ethernet_init(mac_addr, ip_addr);
	etherbone_init();
	telnet_init();
#endif
#ifdef CSR_OLED_BASE
	oled_init();
	oled_refresh();
#endif
	pattern_fill_framebuffer(1280, 720);
	hdmi_out_config_720p60();
	ci_prompt();
	time_init();
	while(1) {
		ci_service();
#ifdef ETHMAC_BASE
		ethernet_service();
#endif
		pattern_service();
	}

	return 0;
}
