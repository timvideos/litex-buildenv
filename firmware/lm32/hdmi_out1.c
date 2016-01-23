#include <generated/csr.h>
#ifdef CSR_HDMI_OUT1_BASE
#include <stdio.h>
#include "hdmi_out1.h"

int hdmi_out1_debug_enabled = 0;

void hdmi_out1_print_edid(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    hdmi_out1_i2c_start_cond();
    b = hdmi_out1_i2c_write(0xa0);
    if (!b && hdmi_out1_debug_enabled)
        printf("hdmi_out1: NACK while writing slave address!\n");
    b = hdmi_out1_i2c_write(0x00);
    if (!b && hdmi_out1_debug_enabled)
        printf("hdmi_out1: NACK while writing eeprom address!\n");
    hdmi_out1_i2c_start_cond();
    b = hdmi_out1_i2c_write(0xa1);
    if (!b && hdmi_out1_debug_enabled)
        printf("hdmi_out1: NACK while writing slave address (2)!\n");
    for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
        b = hdmi_out1_i2c_read(eeprom_addr == 127 && extension_number == 0 ? 0 : 1);
        sum +=b;
        printf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            printf("\n");
        if(eeprom_addr == 126)
            extension_number = b;
        if(eeprom_addr == 127 && sum != 0)
        {
            printf("Checksum ERROR in EDID block 0\n");
            hdmi_out1_i2c_stop_cond();
            return;
        }
    }
    for(e = 0; e < extension_number; e++)
    {
        printf("\n");
        sum = 0;
        for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
            b = hdmi_out1_i2c_read(eeprom_addr == 127 && e == extension_number - 1 ? 0 : 1);
            sum += b;
            printf("%02X ", b);
            if(!((eeprom_addr+1) % 16))
                printf("\n");
            if(eeprom_addr == 127 && sum != 0)
            {
                printf("Checksum ERROR in EDID extension block %d\n", e);
                hdmi_out1_i2c_stop_cond();
                return;
            }
        }
    }
    hdmi_out1_i2c_stop_cond();
}

#endif
