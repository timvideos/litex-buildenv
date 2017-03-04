#include <generated/csr.h>
#ifdef CSR_OPSIS_I2C_MUX_SEL_ADDR

#define OPSIS_I2C_GPIO 0
#define OPSIS_I2C_FX2HACK 1

#define OPSIS_I2C_ACTIVE(x) \
	opsis_i2c_mux_sel_write(x);

#endif
