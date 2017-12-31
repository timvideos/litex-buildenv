#include <stdio.h>
#include <generated/csr.h>

#include "mmcm.h"
#include "stdio_wrap.h"

/*
 * Despite varying pixel clocks, we must keep the PLL VCO operating
 * in the specified range of 600MHz - 1200MHz.
 */
#ifdef CSR_HDMI_OUT0_DRIVER_CLOCKING_MMCM_RESET_ADDR
void hdmi_out0_driver_clocking_mmcm_write(int adr, int data)
{
	hdmi_out0_driver_clocking_mmcm_adr_write(adr);
	hdmi_out0_driver_clocking_mmcm_dat_w_write(data);
	hdmi_out0_driver_clocking_mmcm_write_write(1);
	while(!hdmi_out0_driver_clocking_mmcm_drdy_read());
}

int hdmi_out0_driver_clocking_mmcm_read(int adr)
{
	hdmi_out0_driver_clocking_mmcm_adr_write(adr);
	hdmi_out0_driver_clocking_mmcm_read_write(1);
	while(!hdmi_out0_driver_clocking_mmcm_drdy_read());
	return hdmi_out0_driver_clocking_mmcm_dat_r_read();
}

MMCM hdmi_out0_driver_clocking_mmcm = {
	.write = &hdmi_out0_driver_clocking_mmcm_write,
	.read = &hdmi_out0_driver_clocking_mmcm_read,
};
#endif

#ifdef CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
void hdmi_in0_clocking_mmcm_write(int adr, int data)
{
	hdmi_in0_clocking_mmcm_adr_write(adr);
	hdmi_in0_clocking_mmcm_dat_w_write(data);
	hdmi_in0_clocking_mmcm_write_write(1);
	while(!hdmi_in0_clocking_mmcm_drdy_read());
}

int hdmi_in0_clocking_mmcm_read(int adr)
{
	hdmi_in0_clocking_mmcm_adr_write(adr);
	hdmi_in0_clocking_mmcm_read_write(1);
	while(!hdmi_in0_clocking_mmcm_drdy_read());
	return hdmi_in0_clocking_mmcm_dat_r_read();
}

MMCM hdmi_in0_clocking_mmcm = {
	.write = &hdmi_in0_clocking_mmcm_write,
	.read = &hdmi_in0_clocking_mmcm_read,
};
#endif

static void mmcm_config_30to60mhz(MMCM *mmcm)
{
	mmcm->write(0x14, 0x1000 | (10<<6) | 10); /* clkfbout_mult  = 20 */
	mmcm->write(0x08, 0x1000 | (10<<6) | 10); /* clkout0_divide = 20 */
	mmcm->write(0x0a, 0x1000 |  (8<<6) |  8); /* clkout1_divide = 16 */
	mmcm->write(0x0c, 0x1000 |  (2<<6) |  2); /* clkout2_divide =  4 */
	mmcm->write(0x0d, 0);                     /* clkout2_divide =  4 */
}

static void mmcm_config_60to120mhz(MMCM *mmcm)
{
	mmcm->write(0x14, 0x1000 |  (5<<6) | 5); /* clkfbout_mult  = 10 */
	mmcm->write(0x08, 0x1000 |  (5<<6) | 5); /* clkout0_divide = 10 */
	mmcm->write(0x0a, 0x1000 |  (4<<6) | 4); /* clkout1_divide =  8 */
	mmcm->write(0x0c, 0x1000 |  (1<<6) | 1); /* clkout2_divide =  2 */
	mmcm->write(0x0d, 0);                    /* clkout2_divide =  2 */
}

static void mmcm_config_120to240mhz(MMCM *mmcm)
{
	mmcm->write(0x14, 0x1000 |  (2<<6) | 3);  /* clkfbout_mult  = 5 */
	mmcm->write(0x08, 0x1000 |  (2<<6) | 3);  /* clkout0_divide = 5 */
	mmcm->write(0x0a, 0x1000 |  (2<<6) | 2);  /* clkout1_divide = 4 */
	mmcm->write(0x0c, 0x1000 |  (0<<6) | 0);  /* clkout2_divide = 1 */
	mmcm->write(0x0d, (1<<6));                /* clkout2_divide = 1 */
}

void mmcm_config_for_clock(MMCM *mmcm, int freq)
{
	/*
	 * FIXME: we also need to configure phase detector
	 */
	if(freq < 3000)
		wprintf("Frequency too low for input MMCMs\n");
	else if(freq < 6000)
		mmcm_config_30to60mhz(mmcm);
	else if(freq < 12000)
		mmcm_config_60to120mhz(mmcm);
	else if(freq < 24000)
		mmcm_config_120to240mhz(mmcm);
	else
		wprintf("Frequency too high for input MMCMs\n");
}

void mmcm_dump(MMCM* mmcm)
{
	int i;
	for(i=0;i<128;i++)
		printf("%04x ", mmcm->read(i));

}
void mmcm_dump_all(void)
{
	int i;
#ifdef CSR_HDMI_OUT0_DRIVER_CLOCKING_MMCM_RESET_ADDR
	printf("framebuffer MMCM:\n");
	mmcm_dump(&hdmi_out0_driver_clocking_mmcm);
	printf("\n");
#endif
#ifdef CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
	printf("dvisampler MMCM:\n");
	mmcm_dump(&hdmi_in0_clocking_mmcm);
	printf("\n");
#endif
}
