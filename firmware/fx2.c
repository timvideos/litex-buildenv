#include "fx2.h"

#include "asm.h"
#include "stdio_wrap.h"

#ifdef CSR_OPSIS_I2C_FX2_RESET_OUT_ADDR

#define FX2_HACK_SLAVE_ADDRESS 0x40
#define FX2_HACK_SHIFT_REG_FULL  1
#define FX2_HACK_SHIFT_REG_EMPTY 2
#define FX2_HACK_STATUS_READY 0

#include "fx2_fw_usbjtag.c"
#ifdef ENCODER_BASE
#include "fx2_fw_hdmi2usb.c"
#endif

enum fx2_fw_version fx2_fw_active;


static unsigned next_read_addr;
static unsigned end_addr;

static inline uint8_t fx2_fw_get_value(unsigned addr) {
	uint8_t r = 0xff;
	if (addr <= end_addr) {
		switch(fx2_fw_active) {
		case FX2FW_USBJTAG:
			r = fx2_mbfw_usbjtag.bytes[addr];
			break;
#ifdef ENCODER_BASE
		case FX2FW_HDMI2USB:
			r = fx2_mbfw_hdmi2usb.bytes[addr];
			break;
#endif
		}
	} else {
		wprintf("fx2: Read from invalid address %02X (end: %02X)\n", addr, end_addr);
	}
	return r;
}

// FIXME: These should be in microseconds and scaled based on CPU frequency or
// something.
#define FX2_REPORT_PERIOD (1 << 20)
#define FX2_WAIT_PERIOD FX2_REPORT_PERIOD*5
#define FX2_RESET_PERIOD (1 << 16)

static void fx2_load_init(void)
{
	next_read_addr = 0;
	switch(fx2_fw_active) {
	case FX2FW_USBJTAG:
		end_addr = FX2_MBFW_USBJTAG_END;
		break;
#ifdef ENCODER_BASE
	case FX2FW_HDMI2USB:
		end_addr = FX2_MBFW_HDMI2USB_END;
		break;
#endif
	}

	opsis_i2c_fx2_hack_slave_addr_write(FX2_HACK_SLAVE_ADDRESS);
	opsis_i2c_fx2_hack_shift_reg_write(fx2_fw_get_value(0));
	opsis_i2c_fx2_hack_status_write(FX2_HACK_STATUS_READY);
}

static void fx2_load(void)
{
	fx2_load_init();
	wprintf("fx2: Waiting for FX2 to load firmware.\n");

	uint64_t i = 0;
	while((i < FX2_WAIT_PERIOD)) {
		i++;
		if (fx2_service(false)) {
			i = 0;
			if (next_read_addr == 0) {
				break;
			}
		} else if ((i % FX2_REPORT_PERIOD) == 0) {
			wprintf("fx2: Waiting at %02X (end: %02X)\n", next_read_addr, end_addr);
		}
	}
	if (i > 0) {
		wprintf("fx2: Timeout loading!\n");
	} else {
		wprintf("fx2: Booted.\n");
	}
}

bool fx2_service(bool verbose)
{
	unsigned char status = opsis_i2c_fx2_hack_status_read();
	if(status == FX2_HACK_SHIFT_REG_EMPTY) { // there's been a master READ
		if (verbose) {
			wprintf("fx2: read %02X (end: %02X)\n", next_read_addr, end_addr);
		}
		if (next_read_addr < end_addr) {
			// Load next value into the system
			opsis_i2c_fx2_hack_shift_reg_write(fx2_fw_get_value(next_read_addr+1));
			opsis_i2c_fx2_hack_status_write(FX2_HACK_STATUS_READY);
			next_read_addr++;
		} else {
			wprintf("fx2: Finished loading firmware.\n");
			fx2_load_init();
		}
		return true;
	} else if (status != 0) {
		wprintf("fx2: Bad status %02X\n", status);
	}
	return false;
}

void fx2_reboot(enum fx2_fw_version fw)
{
	OPSIS_I2C_ACTIVE(OPSIS_I2C_FX2HACK);
	unsigned int i;
	fx2_fw_active = fw;
	wprintf("fx2: Turning off.\n");
	opsis_i2c_fx2_reset_out_write(1);
	for(i=0;i<FX2_RESET_PERIOD;i++) NOP;
	opsis_i2c_fx2_reset_out_write(0);
	wprintf("fx2: Turning on.\n");
	fx2_load();
}

void fx2_debug(void) {
	wprintf("Possible FX2 Firmware:\n");
	wprintf(" [%s] usbjtag (%02X) (IXO USB JTAG Mode)\n", fx2_fw_active == FX2FW_USBJTAG ? "*" : " ", (unsigned int)FX2_MBFW_USBJTAG_END);
#ifdef ENCODER_BASE
	wprintf(" [%s] hdmi2usb (%02X) (HDMI2USB Video Capture Mode)\n", fx2_fw_active == FX2FW_HDMI2USB ? "*" : " ", (unsigned int)FX2_MBFW_HDMI2USB_END);
#endif
}

void fx2_init(void)
{
#ifdef ENCODER_BASE
	fx2_reboot(FX2FW_HDMI2USB);
#else
	fx2_reboot(FX2FW_USBJTAG);
#endif
}

#endif
