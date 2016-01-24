#include <generated/csr.h>
#ifdef CSR_TOFE_EEPROM_I2C_BASE
#include <stdio.h>
#include "i2c.h"
#include "tofe_eeprom.h"

I2C tofe_eeprom_i2c;
int tofe_eeprom_debug_enabled = 0;

void tofe_eeprom_i2c_init(void) {
    tofe_eeprom_i2c.w_read = tofe_eeprom_i2c_w_read;
    tofe_eeprom_i2c.w_write = tofe_eeprom_i2c_w_write;
    tofe_eeprom_i2c.r_read = tofe_eeprom_i2c_r_read;
    i2c_init(&tofe_eeprom_i2c);
}

void tofe_eeprom_dump(void) {
    int tofe_eeprom_addr = 0;
    unsigned char b;

    i2c_start_cond(&tofe_eeprom_i2c);
    b = i2c_write(&tofe_eeprom_i2c, 0xa0);
    if (!b && tofe_eeprom_debug_enabled)
        printf("tofe_eeprom: NACK while writing slave address!\r\n");
    b = i2c_write(&tofe_eeprom_i2c, 0x00);
    if (!b && tofe_eeprom_debug_enabled)
        printf("tofe_eeprom: NACK while writing tofe_eeprom address!\r\n");

    i2c_start_cond(&tofe_eeprom_i2c);
    b = i2c_write(&tofe_eeprom_i2c, 0xa1);
    if (!b && tofe_eeprom_debug_enabled)
        printf("tofe_eeprom: NACK while writing slave address (2)!\r\n");

    for (tofe_eeprom_addr = 0 ; tofe_eeprom_addr < 256 ; tofe_eeprom_addr++) {
        b = i2c_read(&tofe_eeprom_i2c, 1);
        printf("%02X ", b);
        if(!((tofe_eeprom_addr+1) % 16))
            printf("\r\n");
    }
    i2c_stop_cond(&tofe_eeprom_i2c);
}

#endif
