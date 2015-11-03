
#ifndef CDC_H
#define CDC_H

#include <fx2types.h>

#include "cdc-config.h"

void cdcuser_receive_data(BYTE* data, WORD length);
BOOL cdcuser_set_line_rate(DWORD baud_rate);

// Handles the "vendor commands" for a CDC device.
BOOL cdc_handle_command(BYTE cmd);

//void cdc_setup();

// Send the CDC interrupt poll thingy.
void cdc_receive_poll();

// You are able to send data.
//BOOL cdc_can_send();
#define cdc_can_send() \
	!(EP2468STAT & bmCDC_D2H_EP(FULL))

extern volatile WORD cdc_queued_bytes;
// Queue a byte in the output CDC data queue.
//void cdc_queue_data(BYTE data);
#define cdc_queue_data(data) \
	CDC_D2H_EP(FIFOBUF)[cdc_queued_bytes++] = data;
// Send all queue bytes from the output CDC data queue to the host.
//void cdc_send_queued_data();
#define cdc_send_queued_data() \
	CDC_D2H_EP(BCH)=MSB(cdc_queued_bytes); \
	SYNCDELAY; \
	CDC_D2H_EP(BCL)=LSB(cdc_queued_bytes); \
	SYNCDELAY; \
	cdc_queued_bytes = 0;


/* ------------------------------------------------------------------------ */

/**
 * The defines and structures found below comes from the Linux kernel and are
 * found in include/uapi/linux/usb/cdc.h
 */

/* The 8051 is an 8bit processor, so doesn't actually have any endian
 * naturally, instead the endian comes from the compiler. sdcc choses to be
 * little endian, as does the USB specification.
 */
#define __u8    BYTE
#define __le16  WORD
#define __le32  DWORD

// #define USB_CDC_SUBCLASS_ACM                    0x02
// #define USB_CDC_PROTO_NONE                      0
// #define USB_CDC_ACM_PROTO_AT_V25TER             1
// #define USB_CDC_ACM_PROTO_AT_PCCA101            2
// #define USB_CDC_ACM_PROTO_AT_PCCA101_WAKE       3
// #define USB_CDC_ACM_PROTO_AT_GSM                4
// #define USB_CDC_ACM_PROTO_AT_3G                 5
// #define USB_CDC_ACM_PROTO_AT_CDMA               6
// #define USB_CDC_ACM_PROTO_VENDOR                0xff
// 
// /* "Abstract Control Management Descriptor" from CDC spec  5.2.3.3 */
// struct usb_cdc_acm_descriptor {
//         __u8    bLength;
//         __u8    bDescriptorType;
//         __u8    bDescriptorSubType;
// 
//         __u8    bmCapabilities;
// /* capabilities from 5.2.3.3 */
// #define USB_CDC_COMM_FEATURE    0x01
// #define USB_CDC_CAP_LINE        0x02
// #define USB_CDC_CAP_BRK         0x04
// #define USB_CDC_CAP_NOTIFY      0x08
// };

/*
 * Class-Specific Control Requests (6.2)
 *
 * section 3.6.2.1 table 4 has the ACM profile, for modems.
 * section 3.8.2 table 10 has the ethernet profile.
 *
 * Microsoft's RNDIS stack for Ethernet is a vendor-specific CDC ACM variant,
 * heavily dependent on the encapsulated (proprietary) command mechanism.
 */

//#define USB_CDC_SEND_ENCAPSULATED_COMMAND       0x00
//#define USB_CDC_GET_ENCAPSULATED_RESPONSE       0x01
#define USB_CDC_REQ_SET_LINE_CODING             0x20
#define USB_CDC_REQ_GET_LINE_CODING             0x21
#define USB_CDC_REQ_SET_CONTROL_LINE_STATE      0x22
//#define USB_CDC_REQ_SEND_BREAK                  0x23

/* Line Coding Structure from CDC spec 6.2.13 */
struct usb_cdc_line_coding {
        // __le32  dwDTERate;
        __u8  bDTERate0;
        __u8  bDTERate1;
        __u8  bDTERate2;
        __u8  bDTERate3;

        __u8    bCharFormat;
#define USB_CDC_1_STOP_BITS                     0
#define USB_CDC_1_5_STOP_BITS                   1
#define USB_CDC_2_STOP_BITS                     2

        __u8    bParityType;
#define USB_CDC_NO_PARITY                       0
#define USB_CDC_ODD_PARITY                      1
#define USB_CDC_EVEN_PARITY                     2
#define USB_CDC_MARK_PARITY                     3
#define USB_CDC_SPACE_PARITY                    4

        __u8    bDataBits;
};

// /*
//  * Class-Specific Notifications (6.3) sent by interrupt transfers
//  *
//  * section 3.8.2 table 11 of the CDC spec lists Ethernet notifications
//  * section 3.6.2.1 table 5 specifies ACM notifications, accepted by RNDIS
//  * RNDIS also defines its own bit-incompatible notifications
//  */
// 
// #define USB_CDC_NOTIFY_NETWORK_CONNECTION       0x00
// #define USB_CDC_NOTIFY_RESPONSE_AVAILABLE       0x01
// #define USB_CDC_NOTIFY_SERIAL_STATE             0x20
// #define USB_CDC_NOTIFY_SPEED_CHANGE             0x2a
// 
// struct usb_cdc_notification {
//         __u8    bmRequestType;
//         __u8    bNotificationType;
//         __le16  wValue;
//         __le16  wIndex;
//         __le16  wLength;
// };
// 
// struct usb_cdc_speed_change {
//         __le32  DLBitRRate;     /* contains the downlink bit rate (IN pipe) */
//         __le32  ULBitRate;      /* contains the uplink bit rate (OUT pipe) */
// };


#endif // CDC_H
