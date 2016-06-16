#include <stdio.h>
#include <stdlib.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <console.h>

#include "config.h"
#include "ci.h"
#include "processor.h"
#include "encoder.h"
#include "pattern.h"
#include "hdmi_out0.h"
#include "hdmi_out1.h"
#include "fx2.h"
#include "version.h"
#include "heartbeat.h"

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

	puts("\r\nHDMI2USB firmware  http://timvideos.us/");
	print_version();

	config_init();
	time_init();
	processor_init();
	processor_start(config_get(CONFIG_KEY_RESOLUTION));

	// Set HDMI Output 0 to be pattern
#ifdef CSR_HDMI_OUT0_BASE
	processor_set_hdmi_out0_source(VIDEO_IN_PATTERN);
#endif
	// Set HDMI Output 1 to be pattern
#ifdef CSR_HDMI_OUT1_BASE
	processor_set_hdmi_out1_source(VIDEO_IN_PATTERN);
#endif
	processor_update();

	// Reboot the FX2 chip into HDMI2USB mode
#ifdef CSR_FX2_RESET_OUT_ADDR
	fx2_init();
#endif

	// Set Encoder to be pattern
#ifdef ENCODER_BASE
	processor_set_encoder_source(VIDEO_IN_PATTERN);
	encoder_enable(1);
	processor_update();
#endif
	ci_prompt();
	while(1) {
		processor_service();
		ci_service();

#ifdef CSR_FX2_RESET_OUT_ADDR
		fx2_service(true);
#endif

/* XXX FIX DDR conflict between DMA and L2 cache */
#if 0
		pattern_service();
#endif
	}

	return 0;
}
