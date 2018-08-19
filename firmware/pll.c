#include <generated/csr.h>

#include "pll.h"
#include "stdio_wrap.h"

/*
 * Despite varying pixel clocks, we must keep the PLL VCO operating
 * in the specified range of 400MHz - 1000MHz.
 * This code can program two sets of DRP data:
 * 1. with VCO operating at 20x the pixel clock (for 20MHz - 50MHz pixel clock)
 * 2. with VCO operating at 10x the pixel clock (for 40MHz - 100MHz pixel clock)
 */

static const unsigned short int pll_config_20x[32] = {
	0x0006, 0x0008, 0x0000, 0x4400, 0x1708, 0x0097, 0x0501, 0x8288,
	0x4201, 0x0d90, 0x00a1, 0x0111, 0x1004, 0x2028, 0x0802, 0x2800,
	0x0288, 0x8058, 0x020c, 0x0200, 0x1210, 0x400b, 0xfc21, 0x0b21,
	0x7f5f, 0xc0eb, 0x472a, 0xc02a, 0x20b6, 0x0e96, 0x1002, 0xd6ce
};

static const unsigned short int pll_config_10x[32] = {
	0x0006, 0x0008, 0x0000, 0x4400, 0x1708, 0x0097, 0x0901, 0x8118,
	0x4181, 0x0d60, 0x00a1, 0x0111, 0x1004, 0x2028, 0x0802, 0x0608,
	0x0148, 0x8018, 0x020c, 0x0200, 0x1210, 0x400b, 0xfc21, 0x0b22,
	0x5fdf, 0x40eb, 0x472b, 0xc02a, 0x20b6, 0x0e96, 0x1002, 0xd6ce
};

static void program_data(const unsigned short *data)
{
#if defined(CSR_HDMI_OUT0_BASE) || defined(CSR_HDMI_IN0_BASE) || defined(CSR_HDMI_IN1_BASE)
	int i;
#endif
	/*
	 * Some bits of words 4 and 5 appear to depend on PLL location,
	 * so we start at word 6.
	 * PLLs also seem to dislike any write to the last words.
	 */
#ifdef CSR_HDMI_OUT0_DRIVER_CLOCKING_PLL_RESET_ADDR
	for(i=6;i<32-5;i++) {
		hdmi_out0_driver_clocking_pll_adr_write(i);
		hdmi_out0_driver_clocking_pll_dat_w_write(data[i]);
		hdmi_out0_driver_clocking_pll_write_write(1);
		while(!hdmi_out0_driver_clocking_pll_drdy_read());
	}
#endif
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
	for(i=6;i<32-5;i++) {
		hdmi_in0_clocking_pll_adr_write(i);
		hdmi_in0_clocking_pll_dat_w_write(data[i]);
		hdmi_in0_clocking_pll_write_write(1);
		while(!hdmi_in0_clocking_pll_drdy_read());
	}
#endif
#ifdef CSR_HDMI_IN1_CLOCKING_PLL_RESET_ADDR
	for(i=6;i<32-5;i++) {
		hdmi_in1_clocking_pll_adr_write(i);
		hdmi_in1_clocking_pll_dat_w_write(data[i]);
		hdmi_in1_clocking_pll_write_write(1);
		while(!hdmi_in1_clocking_pll_drdy_read());
	}
#endif
}

void pll_config_for_clock(int freq)
{
	/*
	 * FIXME:
	 * 10x configuration causes random IDELAY lockups (at high frequencies it seems)
	 * 20x configuration seems to always work, even with overclocked VCO
	 * Reproducible both with DRP and initial reconfiguration.
	 * Until this spartan6 weirdness is sorted out, just stick to 20x.
	 */

	(void) pll_config_10x[0]; // Dummy access to suppress to suppress -Werror=unused-const-variable.
	program_data(pll_config_20x);
#ifdef XILINX_SPARTAN6_WORKS_AMAZINGLY_WELL
	if(freq < 2000)
		wprintf("Frequency too low for PLLs\n");
	else if(freq < 4500)
		program_data(pll_config_20x);
	else if(freq < 10000)
		program_data(pll_config_10x);
	else
		wprintf("Frequency too high for PLLs\n");
#endif
}

void pll_dump(void)
{
#if defined(CSR_HDMI_OUT0_BASE) || defined(CSR_HDMI_IN0_BASE) || defined(CSR_HDMI_IN1_BASE)
	int i;
#endif
#ifdef CSR_HDMI_OUT0_DRIVER_CLOCKING_PLL_RESET_ADDR
	wprintf("framebuffer PLL:\n");
	for(i=0;i<32;i++) {
		hdmi_out0_driver_clocking_pll_adr_write(i);
		hdmi_out0_driver_clocking_pll_read_write(1);
		while(!hdmi_out0_driver_clocking_pll_drdy_read());
		wprintf("%04x ", hdmi_out0_driver_clocking_pll_dat_r_read());
	}
	wputchar('\n');
#endif
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
	wprintf("dvisampler0 PLL:\n");
	for(i=0;i<32;i++) {
		hdmi_in0_clocking_pll_adr_write(i);
		hdmi_in0_clocking_pll_read_write(1);
		while(!hdmi_in0_clocking_pll_drdy_read());
		wprintf("%04x ", hdmi_in0_clocking_pll_dat_r_read());
	}
	wputchar('\n');
#endif
#ifdef CSR_HDMI_IN1_CLOCKING_PLL_RESET_ADDR
	wprintf("dvisampler1 PLL:\n");
	for(i=0;i<32;i++) {
		hdmi_in1_clocking_pll_adr_write(i);
		hdmi_in1_clocking_pll_read_write(1);
		while(!hdmi_in1_clocking_pll_drdy_read());
		wprintf("%04x ", hdmi_in1_clocking_pll_dat_r_read());
	}
	wputchar('\n');
#endif
}
