#include <generated/csr.h>
#ifdef CSR_HDMI_OUT1_I2C_W_ADDR
#include <stdio.h>
#include "i2c.h"
#include "hdmi_out1.h"

I2C hdmi_out1_i2c;
int hdmi_out1_debug_enabled = 0;

void hdmi_out1_i2c_init(void) {
    hdmi_out1_i2c.w_read = hdmi_out1_i2c_w_read;
    hdmi_out1_i2c.w_write = hdmi_out1_i2c_w_write;
    hdmi_out1_i2c.r_read = hdmi_out1_i2c_r_read;
    i2c_init(&hdmi_out1_i2c);
}

void hdmi_out1_print_edid(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    i2c_start_cond(&hdmi_out1_i2c);
    b = i2c_write(&hdmi_out1_i2c, 0xa0);
    if (!b && hdmi_out1_debug_enabled)
        printf("hdmi_out1: NACK while writing slave address!\r\n");
    b = i2c_write(&hdmi_out1_i2c, 0x00);
    if (!b && hdmi_out1_debug_enabled)
        printf("hdmi_out1: NACK while writing eeprom address!\r\n");
    i2c_start_cond(&hdmi_out1_i2c);
    b = i2c_write(&hdmi_out1_i2c, 0xa1);
    if (!b && hdmi_out1_debug_enabled)
        printf("hdmi_out1: NACK while writing slave address (2)!\r\n");
    for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
        b = i2c_read(&hdmi_out1_i2c, eeprom_addr == 127 && extension_number == 0 ? 0 : 1);
        sum +=b;
        printf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            printf("\r\n");
        if(eeprom_addr == 126)
            extension_number = b;
        if(eeprom_addr == 127 && sum != 0)
        {
            printf("Checksum ERROR in EDID block 0\r\n");
            i2c_stop_cond(&hdmi_out1_i2c);
            return;
        }
    }
    for(e = 0; e < extension_number; e++)
    {
        printf("\r\n");
        sum = 0;
        for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
            b = i2c_read(&hdmi_out1_i2c, eeprom_addr == 127 && e == extension_number - 1 ? 0 : 1);
            sum += b;
            printf("%02X ", b);
            if(!((eeprom_addr+1) % 16))
                printf("\r\n");
            if(eeprom_addr == 127 && sum != 0)
            {
                printf("Checksum ERROR in EDID extension block %d\r\n", e);
                i2c_stop_cond(&hdmi_out1_i2c);
                return;
            }
        }
    }
    i2c_stop_cond(&hdmi_out1_i2c);
}

#endif
