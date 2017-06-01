#include <stdio.h>
#include <generated/csr.h>

#include "mmcm.h"


void mmcm_dump(void)
{
#if defined(CSR_HDMI_OUT_BASE)
	int i;
#endif
#ifdef CSR_HDMI_OUT_BASE
	printf("framebuffer MMCM:\r\n");
	for(i=0;i<128;i++) {
		hdmi_out_driver_clocking_mmcm_adr_write(i);
		hdmi_out_driver_clocking_mmcm_read_write(1);
		while(!hdmi_out_driver_clocking_mmcm_drdy_read());
		printf("%04x ", hdmi_out_driver_clocking_mmcm_dat_r_read());
	}
	printf("\r\n");
#endif
#ifdef CSR_HDMI_IN_BASE
	printf("dvisampler MMCM:\r\n");
	printf("TODO!");
	printf("\r\n");
#endif
}
