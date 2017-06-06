#include "asm.h"
#include "i2c.h"

/* I2C bit banging */
int i2c_init(I2C *i2c)
{
	unsigned int timeout;

	i2c->started = 0;
	i2c->w_write(I2C_SCL);
	/* Check the I2C bus is ready */
	timeout = 1000;
	while((timeout > 0) && (!(i2c->r_read() & I2C_SDAIN))) timeout--;

	return timeout;
}

void i2c_delay(void)
{
	unsigned int i;

	for(i=0;i<1000;i++) NOP;
}

/* I2C bit-banging functions from http://en.wikipedia.org/wiki/I2c */
unsigned int i2c_read_bit(I2C *i2c)
{
	unsigned int bit;

	/* Let the slave drive data */
	i2c->w_write(0);
	i2c_delay();
	i2c->w_write(I2C_SCL);
	i2c_delay();
	bit = i2c->r_read() & I2C_SDAIN;
	i2c_delay();
	i2c->w_write(0);
	return bit;
}

void i2c_write_bit(I2C *i2c, unsigned int bit)
{
	if(bit) {
		i2c->w_write(I2C_SDAOE | I2C_SDAOUT);
	} else {
		i2c->w_write(I2C_SDAOE);
	}
	i2c_delay();
	/* Clock stretching */
	i2c->w_write(i2c->w_read() | I2C_SCL);
	i2c_delay();
	i2c->w_write(i2c->w_read() & ~I2C_SCL);
}

void i2c_start_cond(I2C *i2c)
{
	if(i2c->started) {
		/* set SDA to 1 */
		i2c->w_write(I2C_SDAOE | I2C_SDAOUT);
		i2c_delay();
		i2c->w_write(i2c->w_read() | I2C_SCL);
		i2c_delay();
	}
	/* SCL is high, set SDA from 1 to 0 */
	i2c->w_write(I2C_SDAOE|I2C_SCL);
	i2c_delay();
	i2c->w_write(I2C_SDAOE);
	i2c->started = 1;
}

void i2c_stop_cond(I2C *i2c)
{
	/* set SDA to 0 */
	i2c->w_write(I2C_SDAOE);
	i2c_delay();
	/* Clock stretching */
	i2c->w_write(I2C_SDAOE | I2C_SCL);
	/* SCL is high, set SDA from 0 to 1 */
	i2c->w_write(I2C_SCL);
	i2c_delay();
	i2c->started = 0;
}

unsigned int i2c_write(I2C *i2c, unsigned char byte)
{
	unsigned int bit;
	unsigned int ack;

	for(bit = 0; bit < 8; bit++) {
		i2c_write_bit(i2c, byte & 0x80);
		byte <<= 1;
	}
	ack = !i2c_read_bit(i2c);
	return ack;
}

unsigned char i2c_read(I2C *i2c, int ack)
{
	unsigned char byte = 0;
	unsigned int bit;

	for(bit = 0; bit < 8; bit++) {
		byte <<= 1;
		byte |= i2c_read_bit(i2c);
	}
	i2c_write_bit(i2c, !ack);
	return byte;
}
