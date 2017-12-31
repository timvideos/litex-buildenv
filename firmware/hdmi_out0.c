#include <generated/csr.h>

#include "stdio_wrap.h"

#include "hdmi_out0.h"

#ifdef CSR_HDMI_OUT0_I2C_W_ADDR
#include "i2c.h"

I2C hdmi_out0_i2c;
int hdmi_out0_debug_enabled = 0;

void hdmi_out0_i2c_init(void) {
    wprintf("hdmi_out0: Init I2C...");
    hdmi_out0_i2c.w_read = hdmi_out0_i2c_w_read;
    hdmi_out0_i2c.w_write = hdmi_out0_i2c_w_write;
    hdmi_out0_i2c.r_read = hdmi_out0_i2c_r_read;
    i2c_init(&hdmi_out0_i2c);
    wprintf("finished.\n");
}

void hdmi_out0_print_edid(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    i2c_start_cond(&hdmi_out0_i2c);
    b = i2c_write(&hdmi_out0_i2c, 0xa0);
    if (!b && hdmi_out0_debug_enabled)
        wprintf("hdmi_out0: NACK while writing slave address!\n");
    b = i2c_write(&hdmi_out0_i2c, 0x00);
    if (!b && hdmi_out0_debug_enabled)
        wprintf("hdmi_out0: NACK while writing eeprom address!\n");
    i2c_start_cond(&hdmi_out0_i2c);
    b = i2c_write(&hdmi_out0_i2c, 0xa1);
    if (!b && hdmi_out0_debug_enabled)
        wprintf("hdmi_out0: NACK while writing slave address (2)!\n");
    for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
        b = i2c_read(&hdmi_out0_i2c, eeprom_addr == 127 && extension_number == 0 ? 0 : 1);
        sum +=b;
        wprintf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            wprintf("\n");
        if(eeprom_addr == 126)
            extension_number = b;
        if(eeprom_addr == 127 && sum != 0)
        {
            wprintf("Checksum ERROR in EDID block 0\n");
            i2c_stop_cond(&hdmi_out0_i2c);
            return;
        }
    }
    for(e = 0; e < extension_number; e++)
    {
        wprintf("\n");
        sum = 0;
        for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
            b = i2c_read(&hdmi_out0_i2c, eeprom_addr == 127 && e == extension_number - 1 ? 0 : 1);
            sum += b;
            wprintf("%02X ", b);
            if(!((eeprom_addr+1) % 16))
                wprintf("\n");
            if(eeprom_addr == 127 && sum != 0)
            {
                wprintf("Checksum ERROR in EDID extension block %d\n", e);
                i2c_stop_cond(&hdmi_out0_i2c);
                return;
            }
        }
    }
    i2c_stop_cond(&hdmi_out0_i2c);
}

#endif
