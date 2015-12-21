#include <generated/csr.h>
#ifdef CSR_EEPROM_I2C_BASE
#include <stdio.h>
#include "i2c.h"
#include "eeprom.h"

#ifdef CSR_EEPROM_I2C_W_ADDR
/* I2C bit banging */
int eeprom_i2c_started;
int eeprom_debug_enabled = 0;

int eeprom_i2c_init(void)
{
	unsigned int timeout;

	eeprom_i2c_started = 0;
	eeprom_i2c_w_write(I2C_SCL);
	/* Check the I2C bus is ready */
	timeout = 1000;
	while((timeout > 0) && (!(eeprom_i2c_r_read() & I2C_SDAIN))) timeout--;
	return timeout;
}

static void eeprom_i2c_delay(void)
{
	unsigned int i;

	for(i=0;i<1000;i++) __asm__("nop");
}

/* I2C bit-banging functions from http://en.wikipedia.org/wiki/I2c */
static unsigned int eeprom_i2c_read_bit(void)
{
	unsigned int bit;

	/* Let the slave drive data */
	eeprom_i2c_w_write(0);
	eeprom_i2c_delay();
	eeprom_i2c_w_write(I2C_SCL);
	eeprom_i2c_delay();
	bit = eeprom_i2c_r_read() & I2C_SDAIN;
	eeprom_i2c_delay();
	eeprom_i2c_w_write(0);
	return bit;
}

static void eeprom_i2c_write_bit(unsigned int bit)
{
	if(bit) {
		eeprom_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
	} else {
		eeprom_i2c_w_write(I2C_SDAOE);
	}
	eeprom_i2c_delay();
	/* Clock stretching */
	eeprom_i2c_w_write(eeprom_i2c_w_read() | I2C_SCL);
	eeprom_i2c_delay();
	eeprom_i2c_w_write(eeprom_i2c_w_read() & ~I2C_SCL);
}

static void eeprom_i2c_start_cond(void)
{
	if(eeprom_i2c_started) {
		/* set SDA to 1 */
		eeprom_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
		eeprom_i2c_delay();
		eeprom_i2c_w_write(eeprom_i2c_w_read() | I2C_SCL);
		eeprom_i2c_delay();
	}
	/* SCL is high, set SDA from 1 to 0 */
	eeprom_i2c_w_write(I2C_SDAOE|I2C_SCL);
	eeprom_i2c_delay();
	eeprom_i2c_w_write(I2C_SDAOE);
	eeprom_i2c_started = 1;
}

static void eeprom_i2c_stop_cond(void)
{
	/* set SDA to 0 */
	eeprom_i2c_w_write(I2C_SDAOE);
	eeprom_i2c_delay();
	/* Clock stretching */
	eeprom_i2c_w_write(I2C_SDAOE | I2C_SCL);
	/* SCL is high, set SDA from 0 to 1 */
	eeprom_i2c_w_write(I2C_SCL);
	eeprom_i2c_delay();
	eeprom_i2c_started = 0;
}

static unsigned int eeprom_i2c_write(unsigned char byte)
{
	unsigned int bit;
	unsigned int ack;

	for(bit = 0; bit < 8; bit++) {
		eeprom_i2c_write_bit(byte & 0x80);
		byte <<= 1;
	}
	ack = !eeprom_i2c_read_bit();
	return ack;
}

static unsigned char eeprom_i2c_read(int ack)
{
	unsigned char byte = 0;
	unsigned int bit;

	for(bit = 0; bit < 8; bit++) {
		byte <<= 1;
		byte |= eeprom_i2c_read_bit();
	}
	eeprom_i2c_write_bit(!ack);
	return byte;
}

void eeprom_dump(void) {
    int eeprom_addr = 0;
    unsigned char b;

    eeprom_i2c_start_cond();
    b = eeprom_i2c_write(0xa0);
    if (!b && eeprom_debug_enabled)
        printf("eeprom: NACK while writing slave address!\n");
    b = eeprom_i2c_write(0x00);
    if (!b && eeprom_debug_enabled)
        printf("eeprom: NACK while writing eeprom address!\n");

    eeprom_i2c_start_cond();
    b = eeprom_i2c_write(0xa1);
    if (!b && eeprom_debug_enabled)
        printf("eeprom: NACK while writing slave address (2)!\n");

    for (eeprom_addr = 0 ; eeprom_addr < 256 ; eeprom_addr++) {
        b = eeprom_i2c_read(1);
        printf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            printf("\n");
    }
    eeprom_i2c_stop_cond();
}

#endif

#endif
