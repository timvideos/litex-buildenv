#include <stdbool.h>
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
#include "config.h"
#include "encoder.h"
#include "etherbone.h"
#include "ethernet.h"
#include "fx2.h"
#include "hdmi_out0.h"
#include "hdmi_out1.h"
#include "mdio.h"
#include "oled.h"
#include "opsis_eeprom.h"
#include "pattern.h"
#include "processor.h"
#include "stdio_wrap.h"
#include "telnet.h"
#include "tofe_eeprom.h"
#include "uptime.h"
#include "version.h"

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

#ifdef ETHMAC_BASE
static unsigned char mac_addr[6] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
static unsigned char ip_addr[4] = {0x00, 0x00, 0x00, 0x00};
#endif

int main(void)
{
#ifdef ETHMAC_BASE
	telnet_active = 0;
#endif
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	wputs("HDMI2USB firmware booting...\n");

#ifdef CSR_OPSIS_I2C_MASTER_W_ADDR
	opsis_eeprom_i2c_init();
#endif

	config_init();
	time_init();

	print_version();

#ifdef CSR_TOFE_I2C_W_ADDR
	tofe_eeprom_i2c_init();
#endif

#ifdef CSR_ETHPHY_MDIO_W_ADDR
	mdio_status();
#endif

#ifdef CSR_OLED_BASE
	oled_init();
	oled_refresh();
#endif

#ifdef ETHMAC_BASE
	// Work out the MAC address
	for(int i = 0; i < 6; i++) {
		mac_addr[i] = config_get(CONFIG_KEY_NETWORK_MAC0+i);
	}
#ifdef CSR_OPSIS_I2C_MASTER_W_ADDR
	opsis_eeprom_mac(mac_addr);
#endif
	// Work out the IP address
	for(int i = 0; i < 4; i++) {
		ip_addr[i] = config_get(CONFIG_KEY_NETWORK_IP0+i);
	}
	// Setup the Ethernet
	ethernet_init(mac_addr, ip_addr);
	etherbone_init();
	telnet_init();
#endif

	// Reboot the FX2 chip into HDMI2USB mode
#ifdef CSR_OPSIS_I2C_FX2_RESET_OUT_ADDR
	if (config_get(CONFIG_KEY_FX2_RESET)) {
		fx2_init();
	}
#endif

	// FIXME: Explain why secondary res is in _init and primary in _start
	processor_init(config_get(CONFIG_KEY_RES_SECONDARY));
	processor_update();
	processor_start(config_get(CONFIG_KEY_RES_PRIMARY));
	processor_service();

#ifdef CSR_HDMI_IN0_BASE
	input0_off();
	if (config_get(CONFIG_KEY_INPUT0_ENABLED)) {
		input0_on();
	}
#endif

#ifdef CSR_HDMI_IN1_BASE
	input1_off();
	if (config_get(CONFIG_KEY_INPUT1_ENABLED)) {
		input1_on();
	}
#endif

#ifdef CSR_HDMI_OUT0_I2C_W_ADDR
	hdmi_out0_i2c_init();
#endif
#ifdef CSR_HDMI_OUT0_BASE
	output0_off();
	if (config_get(CONFIG_KEY_OUTPUT0_ENABLED)) {
		output0_on();
		processor_set_hdmi_out0_source(config_get(CONFIG_KEY_OUTPUT0_SOURCE));
	}
#endif

#ifdef CSR_HDMI_OUT1_I2C_W_ADDR
	hdmi_out1_i2c_init();
#endif
#ifdef CSR_HDMI_OUT1_BASE
	output1_off();
	if (config_get(CONFIG_KEY_OUTPUT1_ENABLED)) {
		output1_on();
		processor_set_hdmi_out1_source(config_get(CONFIG_KEY_OUTPUT1_SOURCE));
	}
#endif

#ifdef ENCODER_BASE
	processor_set_encoder_source(config_get(CONFIG_KEY_ENCODER_SOURCE));
	encoder_enable(config_get(CONFIG_KEY_ENCODER_ENABLED));
	encoder_set_quality(config_get(CONFIG_KEY_ENCODER_QUALITY));
	encoder_set_fps(config_get(CONFIG_KEY_ENCODER_FPS));
#endif

	ci_prompt();
	while(1) {
		uptime_service();
		processor_service();
		ci_service();

#ifdef CSR_FX2_RESET_OUT_ADDR
		fx2_service(true);
#endif
#ifdef ETHMAC_BASE
		ethernet_service();
#endif
#ifdef CSR_FRONT_PANEL_BASE
		front_panel_service();
#endif
#ifdef CSR_OLED_BASE
		oled_refresh();
#endif

		pattern_service();
	}

	return 0;
}
