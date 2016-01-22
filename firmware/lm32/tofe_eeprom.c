#include <generated/csr.h>
#ifdef CSR_TOFE_EEPROM_I2C_BASE
#include <stdio.h>
#include "i2c.h"
#include "tofe_eeprom.h"

#ifdef CSR_TOFE_EEPROM_I2C_W_ADDR
/* I2C bit banging */
int tofe_eeprom_i2c_started;
int tofe_eeprom_debug_enabled = 0;

int tofe_eeprom_i2c_init(void)
{
	unsigned int timeout;

	tofe_eeprom_i2c_started = 0;
	tofe_eeprom_i2c_w_write(I2C_SCL);
	/* Check the I2C bus is ready */
	timeout = 1000;
	while((timeout > 0) && (!(tofe_eeprom_i2c_r_read() & I2C_SDAIN))) timeout--;
	return timeout;
}

static void tofe_eeprom_i2c_delay(void)
{
	unsigned int i;

	for(i=0;i<1000;i++) __asm__("nop");
}

/* I2C bit-banging functions from http://en.wikipedia.org/wiki/I2c */
static unsigned int tofe_eeprom_i2c_read_bit(void)
{
	unsigned int bit;

	/* Let the slave drive data */
	tofe_eeprom_i2c_w_write(0);
	tofe_eeprom_i2c_delay();
	tofe_eeprom_i2c_w_write(I2C_SCL);
	tofe_eeprom_i2c_delay();
	bit = tofe_eeprom_i2c_r_read() & I2C_SDAIN;
	tofe_eeprom_i2c_delay();
	tofe_eeprom_i2c_w_write(0);
	return bit;
}

static void tofe_eeprom_i2c_write_bit(unsigned int bit)
{
	if(bit) {
		tofe_eeprom_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
	} else {
		tofe_eeprom_i2c_w_write(I2C_SDAOE);
	}
	tofe_eeprom_i2c_delay();
	/* Clock stretching */
	tofe_eeprom_i2c_w_write(tofe_eeprom_i2c_w_read() | I2C_SCL);
	tofe_eeprom_i2c_delay();
	tofe_eeprom_i2c_w_write(tofe_eeprom_i2c_w_read() & ~I2C_SCL);
}

static void tofe_eeprom_i2c_start_cond(void)
{
	if(tofe_eeprom_i2c_started) {
		/* set SDA to 1 */
		tofe_eeprom_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
		tofe_eeprom_i2c_delay();
		tofe_eeprom_i2c_w_write(tofe_eeprom_i2c_w_read() | I2C_SCL);
		tofe_eeprom_i2c_delay();
	}
	/* SCL is high, set SDA from 1 to 0 */
	tofe_eeprom_i2c_w_write(I2C_SDAOE|I2C_SCL);
	tofe_eeprom_i2c_delay();
	tofe_eeprom_i2c_w_write(I2C_SDAOE);
	tofe_eeprom_i2c_started = 1;
}

static void tofe_eeprom_i2c_stop_cond(void)
{
	/* set SDA to 0 */
	tofe_eeprom_i2c_w_write(I2C_SDAOE);
	tofe_eeprom_i2c_delay();
	/* Clock stretching */
	tofe_eeprom_i2c_w_write(I2C_SDAOE | I2C_SCL);
	/* SCL is high, set SDA from 0 to 1 */
	tofe_eeprom_i2c_w_write(I2C_SCL);
	tofe_eeprom_i2c_delay();
	tofe_eeprom_i2c_started = 0;
}

static unsigned int tofe_eeprom_i2c_write(unsigned char byte)
{
	unsigned int bit;
	unsigned int ack;

	for(bit = 0; bit < 8; bit++) {
		tofe_eeprom_i2c_write_bit(byte & 0x80);
		byte <<= 1;
	}
	ack = !tofe_eeprom_i2c_read_bit();
	return ack;
}

static unsigned char tofe_eeprom_i2c_read(int ack)
{
	unsigned char byte = 0;
	unsigned int bit;

	for(bit = 0; bit < 8; bit++) {
		byte <<= 1;
		byte |= tofe_eeprom_i2c_read_bit();
	}
	tofe_eeprom_i2c_write_bit(!ack);
	return byte;
}

void tofe_eeprom_dump(void) {
    int tofe_eeprom_addr = 0;
    unsigned char b;

    tofe_eeprom_i2c_start_cond();
    b = tofe_eeprom_i2c_write(0xa0);
    if (!b && tofe_eeprom_debug_enabled)
        printf("tofe_eeprom: NACK while writing slave address!\n");
    b = tofe_eeprom_i2c_write(0x00);
    if (!b && tofe_eeprom_debug_enabled)
        printf("tofe_eeprom: NACK while writing tofe_eeprom address!\n");

    tofe_eeprom_i2c_start_cond();
    b = tofe_eeprom_i2c_write(0xa1);
    if (!b && tofe_eeprom_debug_enabled)
        printf("tofe_eeprom: NACK while writing slave address (2)!\n");

    for (tofe_eeprom_addr = 0 ; tofe_eeprom_addr < 256 ; tofe_eeprom_addr++) {
        b = tofe_eeprom_i2c_read(1);
        printf("%02X ", b);
        if(!((tofe_eeprom_addr+1) % 16))
            printf("\n");
    }
    tofe_eeprom_i2c_stop_cond();
}

#endif

#endif
