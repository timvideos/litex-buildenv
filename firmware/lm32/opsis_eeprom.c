#include <generated/csr.h>
#ifdef CSR_OPSIS_EEPROM_I2C_BASE
#include <stdio.h>
#include "i2c.h"
#include "opsis_eeprom.h"

I2C opsis_eeprom_i2c;
int opsis_eeprom_debug_enabled = 0;

void opsis_eeprom_i2c_init(void) {
    opsis_eeprom_i2c.w_read = opsis_eeprom_i2c_w_read;
    opsis_eeprom_i2c.w_write = opsis_eeprom_i2c_w_write;
    opsis_eeprom_i2c.r_read = opsis_eeprom_i2c_r_read;
    i2c_init(&opsis_eeprom_i2c);
}

void opsis_eeprom_dump(void) {
    int opsis_eeprom_addr = 0;
    unsigned char b;

    i2c_start_cond(&opsis_eeprom_i2c);
    b = i2c_write(&opsis_eeprom_i2c, 0xa0);
    if (!b && opsis_eeprom_debug_enabled)
        printf("opsis_eeprom: NACK while writing slave address!\r\n");
    b = i2c_write(&opsis_eeprom_i2c, 0x00);
    if (!b && opsis_eeprom_debug_enabled)
        printf("opsis_eeprom: NACK while writing opsis_eeprom address!\r\n");

    i2c_start_cond(&opsis_eeprom_i2c);
    b = i2c_write(&opsis_eeprom_i2c, 0xa1);
    if (!b && opsis_eeprom_debug_enabled)
        printf("opsis_eeprom: NACK while writing slave address (2)!\r\n");

    for (opsis_eeprom_addr = 0 ; opsis_eeprom_addr < 256 ; opsis_eeprom_addr++) {
        b = i2c_read(&opsis_eeprom_i2c, 1);
        printf("%02X ", b);
        if(!((opsis_eeprom_addr+1) % 16))
            printf("\r\n");
    }
    i2c_stop_cond(&opsis_eeprom_i2c);
}

#endif
