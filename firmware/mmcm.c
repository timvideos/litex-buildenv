#include <stdio.h>
#include <generated/csr.h>

#include "mmcm.h"

static void hdmi_out0_mmcm_write(unsigned char address, unsigned data) {
	hdmi_out0_driver_clocking_mmcm_adr_write(address);
	hdmi_out0_driver_clocking_mmcm_dat_w_write(data);
	hdmi_out0_driver_clocking_mmcm_write_write(1);
	while (hdmi_out0_driver_clocking_mmcm_drdy_read() == 0);
}

void mmcm_config_for_clock(int freq)
{
	/*
	 * FIXME:
	 * hdmi_in pll configured with fixed 10x ratio
	 * --> (60MHz to 120MHz input pix clock)
	 * hdmi_out0 pll configured with fixed 15x ratio from 100MHz reference clock
	 */

	// 75Mhz hdmi out pix clock
	// pix(clkout0) = 1500/20 = 75MHz
	hdmi_out0_mmcm_write(0x8, 0x1000 | (10<<6) | 10);
	// pix5x(clkout1) = 1500/4 = 375MHz
    hdmi_out0_mmcm_write(0xa, 0x1000 | (2<<6) | 2);
}

void mmcm_dump(void)
{
#if defined(CSR_HDMI_OUT_BASE)
	int i;
#endif
#ifdef CSR_HDMI_OUT_BASE
	printf("framebuffer MMCM:\r\n");
	for(i=0;i<128;i++) {
		hdmi_out0_driver_clocking_mmcm_adr_write(i);
		hdmi_out0_driver_clocking_mmcm_read_write(1);
		while(!hdmi_out0_driver_clocking_mmcm_drdy_read());
		printf("%04x ", hdmi_out0_driver_clocking_mmcm_dat_r_read());
	}
	printf("\r\n");
#endif
#ifdef CSR_HDMI_IN_BASE
	printf("dvisampler MMCM:\r\n");
	for(i=0;i<128;i++) {
		hdmi_in_clocking_mmcm_adr_write(i);
		hdmi_in_clocking_mmcm_read_write(1);
		while(!hdmi_in_clocking_mmcm_drdy_read());
		printf("%04x ", hdmi_in_clocking_mmcm_dat_r_read());
	}
	printf("\r\n");
#endif
}
