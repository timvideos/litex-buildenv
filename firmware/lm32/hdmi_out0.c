#include <generated/csr.h>
#ifdef CSR_HDMI_OUT0_BASE
#include <stdio.h>
#include "i2c.h"
#include "hdmi_out0.h"

/* I2C bit banging */
int hdmi_out0_i2c_started;
int hdmi_out0_debug_enabled = 0;

int hdmi_out0_i2c_init(void)
{
	unsigned int timeout;

	hdmi_out0_i2c_started = 0;
	hdmi_out0_i2c_w_write(I2C_SCL);
	/* Check the I2C bus is ready */
	timeout = 1000;
	while((timeout > 0) && (!(hdmi_out0_i2c_r_read() & I2C_SDAIN))) timeout--;
	return timeout;
}

static void hdmi_out0_i2c_delay(void)
{
	unsigned int i;

	for(i=0;i<1000;i++) __asm__("nop");
}

/* I2C bit-banging functions from http://en.wikipedia.org/wiki/I2c */
static unsigned int hdmi_out0_i2c_read_bit(void)
{
	unsigned int bit;

	/* Let the slave drive data */
	hdmi_out0_i2c_w_write(0);
	hdmi_out0_i2c_delay();
	hdmi_out0_i2c_w_write(I2C_SCL);
	hdmi_out0_i2c_delay();
	bit = hdmi_out0_i2c_r_read() & I2C_SDAIN;
	hdmi_out0_i2c_delay();
	hdmi_out0_i2c_w_write(0);
	return bit;
}

static void hdmi_out0_i2c_write_bit(unsigned int bit)
{
	if(bit) {
		hdmi_out0_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
	} else {
		hdmi_out0_i2c_w_write(I2C_SDAOE);
	}
	hdmi_out0_i2c_delay();
	/* Clock stretching */
	hdmi_out0_i2c_w_write(hdmi_out0_i2c_w_read() | I2C_SCL);
	hdmi_out0_i2c_delay();
	hdmi_out0_i2c_w_write(hdmi_out0_i2c_w_read() & ~I2C_SCL);
}

static void hdmi_out0_i2c_start_cond(void)
{
	if(hdmi_out0_i2c_started) {
		/* set SDA to 1 */
		hdmi_out0_i2c_w_write(I2C_SDAOE | I2C_SDAOUT);
		hdmi_out0_i2c_delay();
		hdmi_out0_i2c_w_write(hdmi_out0_i2c_w_read() | I2C_SCL);
		hdmi_out0_i2c_delay();
	}
	/* SCL is high, set SDA from 1 to 0 */
	hdmi_out0_i2c_w_write(I2C_SDAOE|I2C_SCL);
	hdmi_out0_i2c_delay();
	hdmi_out0_i2c_w_write(I2C_SDAOE);
	hdmi_out0_i2c_started = 1;
}

static void hdmi_out0_i2c_stop_cond(void)
{
	/* set SDA to 0 */
	hdmi_out0_i2c_w_write(I2C_SDAOE);
	hdmi_out0_i2c_delay();
	/* Clock stretching */
	hdmi_out0_i2c_w_write(I2C_SDAOE | I2C_SCL);
	/* SCL is high, set SDA from 0 to 1 */
	hdmi_out0_i2c_w_write(I2C_SCL);
	hdmi_out0_i2c_delay();
	hdmi_out0_i2c_started = 0;
}

static unsigned int hdmi_out0_i2c_write(unsigned char byte)
{
	unsigned int bit;
	unsigned int ack;

	for(bit = 0; bit < 8; bit++) {
		hdmi_out0_i2c_write_bit(byte & 0x80);
		byte <<= 1;
	}
	ack = !hdmi_out0_i2c_read_bit();
	return ack;
}

static unsigned char hdmi_out0_i2c_read(int ack)
{
	unsigned char byte = 0;
	unsigned int bit;

	for(bit = 0; bit < 8; bit++) {
		byte <<= 1;
		byte |= hdmi_out0_i2c_read_bit();
	}
	hdmi_out0_i2c_write_bit(!ack);
	return byte;
}

void hdmi_out0_print_edid(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    hdmi_out0_i2c_start_cond();
    b = hdmi_out0_i2c_write(0xa0);
    if (!b && hdmi_out0_debug_enabled)
        printf("hdmi_out0: NACK while writing slave address!\n");
    b = hdmi_out0_i2c_write(0x00);
    if (!b && hdmi_out0_debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    hdmi_out0_i2c_start_cond();
    b = hdmi_out0_i2c_write(0xa1);
    if (!b && hdmi_out0_debug_enabled)
        printf("hdmi_out0: NACK while writing slave address (2)!\n");
    for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
        b = hdmi_out0_i2c_read(eeprom_addr == 127 && extension_number == 0 ? 0 : 1);
        sum +=b;
        printf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            printf("\n");
        if(eeprom_addr == 126)
            extension_number = b;
        if(eeprom_addr == 127 && sum != 0)
        {
            printf("Checksum ERROR in EDID block 0\n");
            hdmi_out0_i2c_stop_cond();
            return;
        }
    }
    for(e = 0; e < extension_number; e++)
    {
        printf("\n");
        sum = 0;
        for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
            b = hdmi_out0_i2c_read(eeprom_addr == 127 && e == extension_number - 1 ? 0 : 1);
            sum += b;
            printf("%02X ", b);
            if(!((eeprom_addr+1) % 16))
                printf("\n");
            if(eeprom_addr == 127 && sum != 0)
            {
                printf("Checksum ERROR in EDID extension block %d\n", e);
                hdmi_out0_i2c_stop_cond();
                return;
            }
        }
    }
    hdmi_out0_i2c_stop_cond();
}

#endif