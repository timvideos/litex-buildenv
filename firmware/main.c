#include <stdbool.h>
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
#include "config.h"
#include "encoder.h"
#include "etherbone.h"
#include "ethernet.h"
#include "fx2.h"
#include "hdmi_out0.h"
#include "hdmi_out1.h"
#include "mdio.h"
#include "opsis_eeprom.h"
#include "pattern.h"
#include "processor.h"
#include "telnet.h"
#include "tofe_eeprom.h"
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
static const unsigned char mac_addr[6] = {0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00};
static const unsigned char ip_addr[4] = {LOCALIP1, LOCALIP2, LOCALIP3, LOCALIP4};
#endif

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nOpsis CPU testing software built "__DATE__" "__TIME__);
	print_version();

#ifdef CSR_INFO_OPSIS_EEPROM_W_ADDR
	opsis_eeprom_i2c_init();
#endif
#ifdef CSR_TOFE_I2C_W_ADDR
	tofe_eeprom_i2c_init();
#endif

	config_init();
	time_init();

#ifdef CSR_ETHPHY_MDIO_W_ADDR
	mdio_status();
#endif

#ifdef ETHMAC_BASE
	ethernet_init(mac_addr, ip_addr);
	etherbone_init();
	telnet_init();
#endif

	processor_init(config_get(CONFIG_KEY_RES_SECONDARY));

#ifdef CSR_HDMI_OUT0_I2C_W_ADDR
	hdmi_out0_i2c_init();
#endif
#ifdef CSR_HDMI_OUT0_BASE
	processor_set_hdmi_out0_source(VIDEO_IN_PATTERN);
#endif

#ifdef CSR_HDMI_OUT1_I2C_W_ADDR
	hdmi_out1_i2c_init();
#endif
#ifdef CSR_HDMI_OUT1_BASE
	processor_set_hdmi_out1_source(VIDEO_IN_PATTERN);
#endif
	processor_update();
	processor_start(config_get(CONFIG_KEY_RES_PRIMARY));

	// Reboot the FX2 chip into HDMI2USB mode
#ifdef CSR_FX2_RESET_OUT_ADDR
	fx2_init();
#endif
#ifdef ENCODER_BASE
	processor_set_encoder_source(VIDEO_IN_PATTERN);
	encoder_enable(1);
#endif

	ci_prompt();
	while(1) {
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

		pattern_service();
	}

	return 0;
}
