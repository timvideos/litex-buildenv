#include <stdint.h>

#include <generated/csr.h>
#ifdef CSR_OPSIS_I2C_MASTER_W_ADDR
#include "i2c.h"
#include "opsis_eeprom.h"
#include "stdio_wrap.h"

I2C opsis_eeprom_i2c;
int opsis_eeprom_debug_enabled = 0;

void opsis_eeprom_i2c_init(void) {
    wprintf("opsis_eeprom: Init...");
    opsis_eeprom_i2c.w_read = opsis_i2c_master_w_read;
    opsis_eeprom_i2c.w_write = opsis_i2c_master_w_write;
    opsis_eeprom_i2c.r_read = opsis_i2c_master_r_read;
    OPSIS_I2C_ACTIVE(OPSIS_I2C_GPIO);
    i2c_init(&opsis_eeprom_i2c);
    wprintf("finished.\n");
}

static void opsis_eeprom_read(uint8_t addr) {
    unsigned char b;

    OPSIS_I2C_ACTIVE(OPSIS_I2C_GPIO);
    i2c_init(&opsis_eeprom_i2c);

    // Write address to I2C EEPROM
    i2c_start_cond(&opsis_eeprom_i2c);
    b = i2c_write(&opsis_eeprom_i2c, OPSIS_EEPROM_SLAVE_ADDRESS | I2C_WRITE);
    if (!b && opsis_eeprom_debug_enabled)
        wprintf("opsis_eeprom: NACK while writing slave address!\n");
    b = i2c_write(&opsis_eeprom_i2c, addr);
    if (!b && opsis_eeprom_debug_enabled)
        wprintf("opsis_eeprom: NACK while writing opsis_eeprom address!\n");

    // Read data from I2C EEPROM
    i2c_start_cond(&opsis_eeprom_i2c);
    b = i2c_write(&opsis_eeprom_i2c, OPSIS_EEPROM_SLAVE_ADDRESS | I2C_READ);
    if (!b && opsis_eeprom_debug_enabled)
        wprintf("opsis_eeprom: NACK while writing slave address (2)!\n");
}

void opsis_eeprom_dump(void) {
    opsis_eeprom_read(0);
    for (int i = 0 ; i < 256 ; i++) {
        unsigned char b = i2c_read(&opsis_eeprom_i2c, 1);
        wprintf("%02X ", b);
        if(!((i+1) % 16))
            wputchar('\n');
    }
    i2c_stop_cond(&opsis_eeprom_i2c);
}

void opsis_eeprom_mac(unsigned char mac[6]) {
    opsis_eeprom_read(OPSIS_EEPROM_MAC);
    for (int i = 0 ; i < 6; i++) {
	unsigned char b = i2c_read(&opsis_eeprom_i2c, 1);
        mac[i] = b;
    }
    i2c_stop_cond(&opsis_eeprom_i2c);
}

#endif
