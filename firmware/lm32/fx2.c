#include <generated/csr.h>

#include "fx2.h"

#ifdef CSR_FX2_RESET_OUT_ADDR
#include <stdio.h>

#define FX2_HACK_SLAVE_ADDRESS 0x40
#define FX2_HACK_SHIFT_REG_FULL  1
#define FX2_HACK_SHIFT_REG_EMPTY 2
#define FX2_HACK_STATUS_READY 0

#define FX2_FIRMWARE fx2_mbfw_usbjtag
#include "fx2_fw_usbjtag.c"

static void fx2_wait(void) {
	unsigned int i;
	for(i=0;i<1000;i++) __asm__("nop");
}

inline uint8_t fx2_fw_get_value(size_t addr) {
	uint8_t r = 0xff;
	if (addr < sizeof(FX2_FIRMWARE)) {
		r = FX2_FIRMWARE.bytes[addr];
	} else {
		printf("fx2: Read from invalid address %02X\n", addr);
	}
	return r;
}

#define FX2_REPORT_PERIOD (1 << 22)
#define FX2_WAIT_PERIOD FX2_REPORT_PERIOD*10

static size_t next_read_addr;
static void fx2_init(void)
{
	next_read_addr = 0;
	fx2_hack_slave_addr_write(FX2_HACK_SLAVE_ADDRESS);
	fx2_hack_shift_reg_write(fx2_fw_get_value(0));
	fx2_hack_status_write(FX2_HACK_STATUS_READY);
}

static void fx2_load(void)
{
	fx2_init();
	printf("fx2: Waiting for FX2 to load firmware.\n");

	uint64_t i = 0;
	while((i < FX2_WAIT_PERIOD)) {
		i++;
		if (fx2_service(false)) {
			i = 0;
			if (next_read_addr == 0) {
				break;
			}
		} else if ((i % FX2_REPORT_PERIOD) == 0) {
			printf("fx2: Waiting at %02X (end: %02X)\n", next_read_addr, FX2_FIRMWARE_END);
		}
	}
	if (i > 0) {
		printf("fx2: Timeout loading!\n");
	} else {
		printf("fx2: Booted.\n");
	}
}

bool fx2_service(bool verbose)
{
	unsigned char status = fx2_hack_status_read();
	if(status == FX2_HACK_SHIFT_REG_EMPTY) { // there's been a master READ
		if (verbose) {
			printf("fx2: read %02X (end: %02X)\n", next_read_addr, FX2_FIRMWARE_END);
		}
		if (next_read_addr < FX2_FIRMWARE_END) {
			// Load next value into the system
			fx2_hack_shift_reg_write(fx2_fw_get_value(next_read_addr+1));
			fx2_hack_status_write(FX2_HACK_STATUS_READY);
			next_read_addr++;
		} else {
			printf("fx2: Finished loading firmware.\n");
			fx2_init();
		}
		return true;
	} else if (status != 0) {
		printf("fx2: Bad status %02X\n", status);
	}
	return false;
}

void fx2_reboot(void)
{
	printf("fx2: Turning off.\n");
	fx2_reset_out_write(0);
	fx2_wait();
	fx2_reset_out_write(1);
	printf("fx2: Turning on.\n");
	fx2_load();
}

#endif
