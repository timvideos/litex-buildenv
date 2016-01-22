#include <generated/csr.h>
#ifdef CSR_XI2C_BASE
#include "Xi2c.h"

/* I2C bit banging */
int Xi2c_started;

int Xi2c_init(void)
{
	unsigned int timeout;

	Xi2c_started = 0;
	Xi2c_w_write(XI2C_SCL);
	/* Check the I2C bus is ready */
	timeout = 1000;
	while((timeout > 0) && (!(Xi2c_r_read() & XI2C_SDAIN))) timeout--;

	return timeout;
}

void Xi2c_delay(void)
{
	unsigned int i;

	for(i=0;i<1000;i++) __asm__("nop");
}

/* I2C bit-banging functions from http://en.wikipedia.org/wiki/I2c */
unsigned int Xi2c_read_bit(void)
{
	unsigned int bit;

	/* Let the slave drive data */
	Xi2c_w_write(0);
	Xi2c_delay();
	Xi2c_w_write(XI2C_SCL);
	Xi2c_delay();
	bit = Xi2c_r_read() & XI2C_SDAIN;
	Xi2c_delay();
	Xi2c_w_write(0);
	return bit;
}

void Xi2c_write_bit(unsigned int bit)
{
	if(bit) {
		Xi2c_w_write(XI2C_SDAOE | XI2C_SDAOUT);
	} else {
		Xi2c_w_write(XI2C_SDAOE);
	}
	Xi2c_delay();
	/* Clock stretching */
	Xi2c_w_write(Xi2c_w_read() | XI2C_SCL);
	Xi2c_delay();
	Xi2c_w_write(Xi2c_w_read() & ~XI2C_SCL);
}

void Xi2c_start_cond(void)
{
	if(Xi2c_started) {
		/* set SDA to 1 */
		Xi2c_w_write(XI2C_SDAOE | XI2C_SDAOUT);
		Xi2c_delay();
		Xi2c_w_write(Xi2c_w_read() | XI2C_SCL);
		Xi2c_delay();
	}
	/* SCL is high, set SDA from 1 to 0 */
	Xi2c_w_write(XI2C_SDAOE|XI2C_SCL);
	Xi2c_delay();
	Xi2c_w_write(XI2C_SDAOE);
	Xi2c_started = 1;
}

void Xi2c_stop_cond(void)
{
	/* set SDA to 0 */
	Xi2c_w_write(XI2C_SDAOE);
	Xi2c_delay();
	/* Clock stretching */
	Xi2c_w_write(XI2C_SDAOE | XI2C_SCL);
	/* SCL is high, set SDA from 0 to 1 */
	Xi2c_w_write(XI2C_SCL);
	Xi2c_delay();
	Xi2c_started = 0;
}

unsigned int Xi2c_write(unsigned char byte)
{
	unsigned int bit;
	unsigned int ack;

	for(bit = 0; bit < 8; bit++) {
		Xi2c_write_bit(byte & 0x80);
		byte <<= 1;
	}
	ack = !Xi2c_read_bit();
	return ack;
}

unsigned char Xi2c_read(int ack)
{
	unsigned char byte = 0;
	unsigned int bit;

	for(bit = 0; bit < 8; bit++) {
		byte <<= 1;
		byte |= Xi2c_read_bit();
	}
	Xi2c_write_bit(!ack);
	return byte;
}

#endif
