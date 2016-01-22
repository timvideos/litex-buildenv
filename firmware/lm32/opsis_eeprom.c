#include <generated/csr.h>
#ifdef CSR_OPSIS_EEPROM_I2C_BASE
#include <stdio.h>
#include "i2c.h"
#include "opsis_eeprom.h"

#ifdef CSR_OPSIS_EEPROM_I2C_W_ADDR
/* I2C bit banging */
int opsis_eeprom_i2c_started;
int opsis_eeprom_debug_enabled = 0;

int opsis_eeprom_i2c_init(void)
{
	unsigned int timeout;

	opsis_eeprom_i2c_started = 0;
	opsis_eeprom_i2c_w_write(I2C_SCL);
	/* Check the I2C bus is ready */
	timeout = 1000;
	while((timeout > 0) && (!(opsis_eeprom_i2c_r_read() & I2C_SDAIN))) timeout--;
	return timeout;
}

static void opsis_eeprom_i2c_delay(void)
{
	unsigned int i;

	for(i=0;i<1000;i++) __asm__("nop");
}

/* I2C bit-banging functions from http://en.wikipedia.org/wiki/I2c */
static unsigned int opsis_eeprom_i2c_read_bit(void)
{
	unsigned int bit;

	/* Let the slave drive data */
	opsis_eeprom_i2c_w_write(0);
	opsis_eeprom_i2c_delay();
	opsis_eeprom_i2c_w_write(I2C_SCL);
	opsis_eeprom_i2c_delay();
	bit = opsis_eeprom_i2c_r_read() & I2C_SDAIN;
	opsis_eeprom_i2c_delay();
	opsis_eeprom_i2c_w_write(0);
	return bit;
}

static void opsis_eeprom_i2c_write_bit(unsigned int bit)
{
	if(bit) {
		opsis_eeprom_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
	} else {
		opsis_eeprom_i2c_w_write(I2C_SDAOE);
	}
	opsis_eeprom_i2c_delay();
	/* Clock stretching */
	opsis_eeprom_i2c_w_write(opsis_eeprom_i2c_w_read() | I2C_SCL);
	opsis_eeprom_i2c_delay();
	opsis_eeprom_i2c_w_write(opsis_eeprom_i2c_w_read() & ~I2C_SCL);
}

static void opsis_eeprom_i2c_start_cond(void)
{
	if(opsis_eeprom_i2c_started) {
		/* set SDA to 1 */
		opsis_eeprom_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
		opsis_eeprom_i2c_delay();
		opsis_eeprom_i2c_w_write(opsis_eeprom_i2c_w_read() | I2C_SCL);
		opsis_eeprom_i2c_delay();
	}
	/* SCL is high, set SDA from 1 to 0 */
	opsis_eeprom_i2c_w_write(I2C_SDAOE|I2C_SCL);
	opsis_eeprom_i2c_delay();
	opsis_eeprom_i2c_w_write(I2C_SDAOE);
	opsis_eeprom_i2c_started = 1;
}

static void opsis_eeprom_i2c_stop_cond(void)
{
	/* set SDA to 0 */
	opsis_eeprom_i2c_w_write(I2C_SDAOE);
	opsis_eeprom_i2c_delay();
	/* Clock stretching */
	opsis_eeprom_i2c_w_write(I2C_SDAOE | I2C_SCL);
	/* SCL is high, set SDA from 0 to 1 */
	opsis_eeprom_i2c_w_write(I2C_SCL);
	opsis_eeprom_i2c_delay();
	opsis_eeprom_i2c_started = 0;
}

static unsigned int opsis_eeprom_i2c_write(unsigned char byte)
{
	unsigned int bit;
	unsigned int ack;

	for(bit = 0; bit < 8; bit++) {
		opsis_eeprom_i2c_write_bit(byte & 0x80);
		byte <<= 1;
	}
	ack = !opsis_eeprom_i2c_read_bit();
	return ack;
}

static unsigned char opsis_eeprom_i2c_read(int ack)
{
	unsigned char byte = 0;
	unsigned int bit;

	for(bit = 0; bit < 8; bit++) {
		byte <<= 1;
		byte |= opsis_eeprom_i2c_read_bit();
	}
	opsis_eeprom_i2c_write_bit(!ack);
	return byte;
}

void opsis_eeprom_dump(void) {
    int opsis_eeprom_addr = 0;
    unsigned char b;

    opsis_eeprom_i2c_start_cond();
    b = opsis_eeprom_i2c_write(0xa0);
    if (!b && opsis_eeprom_debug_enabled)
        printf("opsis_eeprom: NACK while writing slave address!\n");
    b = opsis_eeprom_i2c_write(0x00);
    if (!b && opsis_eeprom_debug_enabled)
        printf("opsis_eeprom: NACK while writing opsis_eeprom address!\n");

    opsis_eeprom_i2c_start_cond();
    b = opsis_eeprom_i2c_write(0xa1);
    if (!b && opsis_eeprom_debug_enabled)
        printf("opsis_eeprom: NACK while writing slave address (2)!\n");

    for (opsis_eeprom_addr = 0 ; opsis_eeprom_addr < 256 ; opsis_eeprom_addr++) {
        b = opsis_eeprom_i2c_read(1);
        printf("%02X ", b);
        if(!((opsis_eeprom_addr+1) % 16))
            printf("\n");
    }
    opsis_eeprom_i2c_stop_cond();
}

#endif

#endif
