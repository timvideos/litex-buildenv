#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <console.h>
#include <system.h>

#include "ci.h"
#include "ethernet.h"
#include "etherbone.h"
#include "telnet.h"
#include "mdio.h"
#include "oled.h"
#include "pattern.h"
#include "hdmi_in.h"
#include "edid.h"

static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {192, 168, 1, 50};

/* hdmi_out functions */

static void hdmi_out_mmcm_write(uint8_t address, uint16_t data) {
	hdmi_out_driver_clocking_mmcm_adr_write(address);
    hdmi_out_driver_clocking_mmcm_dat_w_write(data);
    hdmi_out_driver_clocking_mmcm_write_write(1);
    while (hdmi_out_driver_clocking_mmcm_drdy_read() == 0);
}

static void hdmi_out_config_720p60(void) {
    hdmi_out_mmcm_write(0x8, 0x1000 + (10 << 6)  + 10);
    hdmi_out_mmcm_write(0xa, 0x1000 + (2  << 6) + 2);

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

static void busy_wait(unsigned int ds)
{
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(SYSTEM_CLOCK_FREQUENCY/10*ds);
	timer0_en_write(1);
	timer0_update_value_write(1);
	while(timer0_value_read()) timer0_update_value_write(1);
}

static const struct video_timing video_modes[1] = {
    {
		.pixel_clock = 7425,

		.h_active = 1280,
		.h_blanking = 700,
		.h_sync_offset = 440,
		.h_sync_width = 40,

		.v_active = 720,
		.v_blanking = 30,
		.v_sync_offset = 5,
		.v_sync_width = 5
	}
};

static void edid_set_mode(const struct video_timing *mode)
{
	unsigned char edid[128];
	int i;
	generate_edid(&edid, "OHW", "TV", 2015, "NEXYS 1", mode);
	for(i=0;i<sizeof(edid);i++)
		MMPTR(CSR_HDMI_IN_EDID_MEM_BASE+4*i) = edid[i];
}

static void hdmi_in_init(void) {
	edid_set_mode(&video_modes[0]);
	hdmi_in_init_video(1280, 720);
	hdmi_in_clocking_mmcm_reset_write(0);
	busy_wait(10);
	hdmi_in_phase_startup();

	while(1) {
		printf("hdmi_in freq: %d.%d MHz\n", hdmi_in_freq_value_read() / 1000000,
		                                    (hdmi_in_freq_value_read() / 10000) % 100);
		hdmi_in_service();
		//hdmi_in_adjust_phase();
		hdmi_in_print_status();
		busy_wait(10);
	}
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
	hdmi_in_init();
	while(1) {
		ci_service();
#ifdef ETHMAC_BASE
		ethernet_service();
#endif
		pattern_service();
	}

	return 0;
}
