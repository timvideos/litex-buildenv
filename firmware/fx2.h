#include <generated/csr.h>
#include <generated/mem.h>
#ifdef CSR_OPSIS_I2C_FX2_RESET_OUT_ADDR

#include <stdbool.h>

#include "opsis_i2c.h"

enum fx2_fw_version {
	FX2FW_USBJTAG,
#ifdef ENCODER_BASE
	FX2FW_HDMI2USB,
#endif
};

void fx2_init(void);
bool fx2_service(bool verbose);
void fx2_reboot(enum fx2_fw_version fw);
void fx2_debug(void);

#endif
