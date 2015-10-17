// The endpoint which data is sent **from** the host down to the CDC serial
// port.

#define CDC_H2D_RESET(x) \
  RESET ## x(0x02);

#define CDC_H2D_EP(x) \
  EP2 ## x

#define bmCDC_H2D_EP(x) \
  bmEP2 ## x

// The endpoint which data is sent **to** the host from the CDC serial port.
#define CDC_D2H_RESET(x) \
  RESET ## x(0x80|0x04);

#define CDC_D2H_EP(x) \
  EP4 ## x

#define bmCDC_D2H_EP(x) \
  bmEP4 ## x

// The endpoint which is used to notify the host about the CDC state changes.
#define CDC_INT_EP(x) \
  EP1OUT ## x

#define bmCDC_INT_EP(x) \
  bmEP1OUT ## x
