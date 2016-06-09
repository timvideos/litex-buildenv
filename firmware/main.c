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

#include "config.h"
#include "ci.h"
#include "ethernet.h"
#include "etherbone.h"
#include "telnet.h"
#include "processor.h"
#include "pattern.h"
#include "mdio.h"

#define HDD_LED   0x01
#define POWER_LED 0x02

#define POWER_SW  0x01

#ifdef CSR_FRONT_PANEL_BASE
static void front_panel_service(void) {
	if(front_panel_switches_in_read() & POWER_SW)
		front_panel_leds_out_write(HDD_LED | POWER_LED);
	else
		front_panel_leds_out_write(0);
}
#endif

static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {192, 168, 1, 50};

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();
#ifdef CSR_HDMI_OUT0_I2C_W_ADDR
	hdmi_out0_i2c_init();
#endif
#ifdef CSR_HDMI_OUT1_I2C_W_ADDR
	hdmi_out1_i2c_init();
#endif

	puts("\nOpsis CPU testing software built "__DATE__" "__TIME__);

	config_init();
	time_init();
	processor_init();
	processor_start(config_get(CONFIG_KEY_RESOLUTION));

#ifdef CSR_ETHPHY_MDIO_W_ADDR
	mdio_status();
#endif

#ifdef ETHMAC_BASE
	ethernet_init(mac_addr, ip_addr);
	etherbone_init();
	telnet_init();
#endif

#ifdef CSR_HDMI_OUT0_BASE
	processor_set_hdmi_out0_source(VIDEO_IN_PATTERN);
#endif
#ifdef CSR_HDMI_OUT1_BASE
	processor_set_hdmi_out1_source(VIDEO_IN_PATTERN);
#endif
	processor_update();
#ifdef ENCODER_BASE
	processor_set_encoder_source(VIDEO_IN_PATTERN);
	encoder_enable(1);
	processor_update();
#endif
#if 0
	// draw a pattern
	int inc_color(int color) {
		color++;
		return color%8;
	}

	static const unsigned int color_bar[8] = {
		RGB_WHITE,
		RGB_YELLOW,
		RGB_CYAN,
		RGB_GREEN,
		RGB_PURPLE,
		RGB_RED,
		RGB_BLUE,
		RGB_BLACK
	};

	int i;
	int color;
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE);
	flush_l2_cache();
	color = -1;
	for(i=0; i<640*64; i++) {
		if(i%(640/8) == 0)
			color = inc_color(color);
		if(color >= 0)
			framebuffer[i] = color_bar[color];
	}

	// init framebuffer
	video_out_initiator_hres_write(640);
	video_out_initiator_hsync_start_write(664);
	video_out_initiator_hsync_end_write(704);
	video_out_initiator_hscan_write(832);
	video_out_initiator_vres_write(480);
	video_out_initiator_vsync_start_write(489);
	video_out_initiator_vsync_end_write(491);
	video_out_initiator_vscan_write(520);
	video_out_initiator_base_write(0);
	video_out_initiator_end_write(640*480-1);
	video_out_initiator_enable_write(1);
#endif

	ci_prompt();
	while(1) {
		processor_service();
		ci_service();
#ifdef ETHMAC_BASE
		ethernet_service();
#endif
#ifdef CSR_FRONT_PANEL_BASE
		front_panel_service();
#endif
	}

	return 0;
}
