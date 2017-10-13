#include <stdio.h>
#include <generated/csr.h>

#include "mmcm.h"

/*
 * Despite varying pixel clocks, we must keep the PLL VCO operating
 * in the specified range of 600MHz - 1200MHz.
 */
#ifdef CSR_HDMI_OUT0_BASE
#ifdef CSR_HDMI_OUT0_DRIVER_CLOCKING_DRP_DWE_ADDR
void hdmi_out0_mmcm_write(int adr, int data) {
	hdmi_out0_driver_clocking_mmcm_adr_write(adr);
	hdmi_out0_driver_clocking_mmcm_dat_w_write(data);
	hdmi_out0_driver_clocking_mmcm_write_write(1);
	while(!hdmi_out0_driver_clocking_mmcm_drdy_read());
}

int hdmi_out0_mmcm_read(int adr) {
	hdmi_out0_driver_clocking_mmcm_adr_write(adr);
	hdmi_out0_driver_clocking_mmcm_read_write(1);
	while(!hdmi_out0_driver_clocking_mmcm_drdy_read());
	return hdmi_out0_driver_clocking_mmcm_dat_r_read();
}
#endif
#endif

#ifdef CSR_HDMI_IN0_BASE
#ifdef CSR_HDMI_IN0_DRIVER_CLOCKING_DRP_DWE_ADDR
void hdmi_in0_clocking_mmcm_write(int adr, int data) {
	hdmi_in0_clocking_mmcm_adr_write(adr);
	hdmi_in0_clocking_mmcm_dat_w_write(data);
	hdmi_in0_clocking_mmcm_write_write(1);
	while(!hdmi_in0_clocking_mmcm_drdy_read());
}

int hdmi_in0_clocking_mmcm_read(int adr) {
	hdmi_in0_clocking_mmcm_adr_write(adr);
	hdmi_in0_clocking_mmcm_read_write(1);
	while(!hdmi_in0_clocking_mmcm_drdy_read());
	return hdmi_in0_clocking_mmcm_dat_r_read();
}

static void hdmi_in_0_config_30_60mhz(void) {
	hdmi_in0_clocking_mmcm_write(0x14, 0x1000 | (10<<6) | 10); /* clkfbout_mult  = 20 */
	hdmi_in0_clocking_mmcm_write(0x08, 0x1000 | (10<<6) | 10); /* clkout0_divide = 20 */
	hdmi_in0_clocking_mmcm_write(0x0a, 0x1000 |  (8<<6) |  8); /* clkout1_divide = 16 */
	hdmi_in0_clocking_mmcm_write(0x0c, 0x1000 |  (2<<6) |  2); /* clkout2_divide =  4 */
	hdmi_in0_clocking_mmcm_write(0x0d, 0);                     /* clkout2_divide =  4 */
}

static void hdmi_in_0_config_60_120mhz(void) {
	hdmi_in0_clocking_mmcm_write(0x14, 0x1000 |  (5<<6) | 5); /* clkfbout_mult  = 10 */
	hdmi_in0_clocking_mmcm_write(0x08, 0x1000 |  (5<<6) | 5); /* clkout0_divide = 10 */
	hdmi_in0_clocking_mmcm_write(0x0a, 0x1000 |  (4<<6) | 4); /* clkout1_divide =  8 */
	hdmi_in0_clocking_mmcm_write(0x0c, 0x1000 |  (1<<6) | 1); /* clkout2_divide =  2 */
	hdmi_in0_clocking_mmcm_write(0x0d, 0);                    /* clkout2_divide =  2 */
}

static void hdmi_in_0_config_120_240mhz(void) {
	hdmi_in0_clocking_mmcm_write(0x14, 0x1000 |  (2<<6) | 3);  /* clkfbout_mult  = 5 */
	hdmi_in0_clocking_mmcm_write(0x08, 0x1000 |  (2<<6) | 3);  /* clkout0_divide = 5 */
	hdmi_in0_clocking_mmcm_write(0x0a, 0x1000 |  (2<<6) | 2);  /* clkout1_divide = 4 */
	hdmi_in0_clocking_mmcm_write(0x0c, 0x1000 |  (0<<6) | 0);  /* clkout2_divide = 1 */
	hdmi_in0_clocking_mmcm_write(0x0d, (1<<6));                /* clkout2_divide = 1 */
}

void mmcm_config_for_clock(int freq)
{
	/*
	 * FIXME: we also need to configure phase detector
	 */
	if(freq < 3000)
		printf("Frequency too low for input MMCMs\r\n");
	else if(freq < 6000)
		hdmi_in_0_config_30_60mhz();
	else if(freq < 12000)
		hdmi_in_0_config_60_120mhz();
	else if(freq < 24000)
		hdmi_in_0_config_120_240mhz();
	else
		printf("Frequency too high for input MMCMs\r\n");
}
#endif
#endif

void mmcm_dump(void)
{
	int i;
#ifdef CSR_HDMI_OUT0_BASE
	printf("framebuffer MMCM:\r\n");
	for(i=0;i<128;i++)
		printf("%04x ", hdmi_out0_mmcm_read(i));
	printf("\r\n");
#endif
#ifdef CSR_HDMI_IN0_BASE
	printf("dvisampler MMCM:\r\n");
	for(i=0;i<128;i++)
		printf("%04x ", hdmi_in0_clocking_mmcm_read(i));
	printf("\r\n");
#endif
}
