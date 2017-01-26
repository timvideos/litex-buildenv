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
#include "pattern.h"

/* hdmi_out functions */

static void hdmi_out_write_mmcm_reg(unsigned int address, unsigned int data) {
	hdmi_out_driver_clocking_drp_addr_write(address);
    hdmi_out_driver_clocking_drp_di_write(data);
    hdmi_out_driver_clocking_drp_dwe_write(1);
    hdmi_out_driver_clocking_drp_den_write(1);
}

static void hdmi_out_config_720p60(void) {
    hdmi_out_write_mmcm_reg(0x8, 0x1000 + (4 << 6)  + 6);
    hdmi_out_write_mmcm_reg(0xa, 0x1000 + (2  << 6) + 2);

    hdmi_out_core_initiator_hres_write(1280);
    hdmi_out_core_initiator_hsync_start_write(1390);
    hdmi_out_core_initiator_hsync_end_write(1430);
    hdmi_out_core_initiator_hscan_write(1650);

	hdmi_out_core_initiator_vres_write(720);
    hdmi_out_core_initiator_vsync_start_write(725);
    hdmi_out_core_initiator_vsync_end_write(730);
    hdmi_out_core_initiator_vscan_write(750);

    hdmi_out_core_initiator_enable_write(0);
    hdmi_out_core_initiator_base_write(0x00200000);
    hdmi_out_core_initiator_length_write(1280*720*2);

    hdmi_out_core_initiator_enable_write(1);
}

/* hdmi_out functions */

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nNeTV2 CPU testing software built "__DATE__" "__TIME__);

	pattern_fill_framebuffer(1280, 720);
	hdmi_out_config_720p60();

	time_init();
	ci_prompt();
	while(1) {
		ci_service();
		pattern_service();
	}

	return 0;
}

