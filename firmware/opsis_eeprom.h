#include <generated/csr.h>
#ifdef CSR_OPSIS_I2C_MASTER_W_ADDR

#include "opsis_i2c.h"

#define OPSIS_EEPROM_SLAVE_ADDRESS 0xA0

#define OPSIS_EEPROM_MAC 0xFA

void opsis_eeprom_i2c_init(void);
void opsis_eeprom_dump(void);
void opsis_eeprom_mac(unsigned char mac[6]);

#endif
