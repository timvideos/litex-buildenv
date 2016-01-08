#include <generated/csr.h>
#ifdef CSR_FX2_RESET_OUT_ADDR

#include <stdbool.h>

enum fx2_fw_version {
	FX2FW_USBJTAG,
#ifdef ENCODER_BASE
	FX2FW_HDMI2USB,
#endif
};

void fx2_init(void);
bool fx2_service(bool verbose);
void fx2_reboot(enum fx2_fw_version fw);

#endif
