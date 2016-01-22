#include <generated/csr.h>
#ifdef CSR_OPSIS_EEPROM_I2C_BASE
#include <stdio.h>
#include "opsis_eeprom_i2c.h"
#include "opsis_eeprom.h"

int opsis_eeprom_debug_enabled = 0;

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
