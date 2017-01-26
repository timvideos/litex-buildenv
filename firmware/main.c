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

static void hdmi_out_config_1080p60(void) {
    hdmi_out_write_mmcm_reg(0x8, 0x1000 + (2 << 6) + 3);
    hdmi_out_write_mmcm_reg(0xa, 0x1000 + (1 << 6) + 1);

    hdmi_out_core_initiator_hres_write(1920);
    hdmi_out_core_initiator_hsync_start_write(1920+88);
    hdmi_out_core_initiator_hsync_end_write(1920+88+44);
    hdmi_out_core_initiator_hscan_write(2200);

	hdmi_out_core_initiator_vres_write(1080);
    hdmi_out_core_initiator_vsync_start_write(1080+4);
    hdmi_out_core_initiator_vsync_end_write(1080+4+5);
    hdmi_out_core_initiator_vscan_write(1125);

    hdmi_out_core_initiator_enable_write(0);
    hdmi_out_core_initiator_base_write(0x00200000);
    hdmi_out_core_initiator_length_write(1920*1080*2);

    hdmi_out_core_initiator_enable_write(1);
}

/* hdmi_out functions */

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nNeTV2 CPU testing software built "__DATE__" "__TIME__);

	pattern_fill_framebuffer(1920, 1080);
	hdmi_out_config_1080p60();

	time_init();
	ci_prompt();
	while(1) {
		ci_service();
		pattern_service();
	}

	return 0;
}

