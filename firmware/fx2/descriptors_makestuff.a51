;
; Copyright (C) 2009 Ubixum, Inc.
;
; Copyright (C) 2009-2012 Chris McClelland
;
; This program is free software: you can redistribute it and/or modify
; it under the terms of the GNU Lesser General Public License as published by
; the Free Software Foundation, either version 3 of the License, or
; (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU Lesser General Public License for more details.
;
; You should have received a copy of the GNU Lesser General Public License
; along with this program.  If not, see <http://www.gnu.org/licenses/>.
;
; this is a the default 
; full speed and high speed 
; descriptors found in the TRM
; change however you want but leave 
; the descriptor pointers so the setupdat.c file works right 

.module DEV_DSCR
.include "date.inc"

        DSCR_DEVICE_TYPE   =    1        ;; Descriptor type: Device
        DSCR_CONFIG_TYPE   =    2        ;; Descriptor type: Configuration
        DSCR_STRING_TYPE   =    3        ;; Descriptor type: String
        DSCR_INTERFACE_TYPE =   4        ;; Descriptor type: Interface
        DSCR_ENDPOINT_TYPE =    5        ;; Descriptor type: Endpoint
        DSCR_DEVQUAL_TYPE  =    6        ;; Descriptor type: Device Qualifier

; for the repeating interfaces
        DSCR_INTERFACE_LEN =    9
        DSCR_ENDPOINT_LEN  =    7

; endpoint types
        ENDPOINT_TYPE_CONTROL = 0        ;; Endpoint type: Control
        ENDPOINT_TYPE_ISO  =    1        ;; Endpoint type: Isochronous
        ENDPOINT_TYPE_BULK =    2        ;; Endpoint type: Bulk
        ENDPOINT_TYPE_INT  =    3        ;; Endpoint type: Interrupt

LEN=(highspd_dscr_realend-_highspd_dscr)
LEN_LE=((LEN&0x00FF)<<8)+(LEN>>8)
VID_LE=((VID&0x00FF)<<8)+(VID>>8)
PID_LE=((PID&0x00FF)<<8)+(PID>>8)
DID_LE=((DID&0x00FF)<<8)+(DID>>8)

	.globl _dev_dscr, _dev_qual_dscr, _highspd_dscr, _fullspd_dscr, _dev_strings, _dev_strings_end

; These need to be in code memory. If they aren't you'll have to
; manully copy them somewhere in code memory otherwise SUDPTRH:L
; don't work right

	.area DSCR_AREA (CODE)

; DEVICE DESCRIPTOR
_dev_dscr:
	.db    dev_dscr_end-_dev_dscr         ; 0 bLength 1 Descriptor size in bytes (12h)
	.db    DSCR_DEVICE_TYPE               ; 1 bDescriptorType 1 The constant DEVICE (01h)
	.dw    0x0002                         ; 2 bcdUSB 2 USB specification release number (BCD)
	.db    0x00                           ; 4 bDeviceClass 1 Class code (Defined at Interface level)
	.db    0x00                           ; 5 bDeviceSubclass 1 Subclass code (Defined at Interface level)
	.db    0x00                           ; 6 bDeviceProtocol 1 Protocol Code (Defined at Interface level)
	.db    64                             ; 7 bMaxPacketSize0 1 Maximum packet size for endpoint zero
	.dw    VID_LE                         ; 8 idVendor 2 Vendor ID
	.dw    PID_LE                         ; 10 idProduct 2 Product ID
	.dw    DID_LE                         ; 12 bcdDevice 2 Device release number (BCD)
	.db    1                              ; 14 iManufacturer 1 Index of string descriptor for the manufacturer
	.db    2                              ; 15 iProduct 1 Index of string descriptor for the product
	.db    0                              ; 16 iSerialNumber 1 Index of string descriptor for the serial number
	.db    1                              ; 17 bNumConfigurations 1 Number of possible configurations
dev_dscr_end:

; CONFIGURATION DESCRIPTOR
_highspd_dscr:
	.db    highspd_dscr_end-_highspd_dscr ; bLength
	.db    DSCR_CONFIG_TYPE               ; bDescriptorType
	.dw    LEN_LE                         ; wTotalLength
	.db    1                              ; bNumInterfaces
	.db    1                              ; bConfigurationValue
	.db    0                              ; iConfiguration (string index)
	.db    0x80                           ; bmAttributes (bus powered, no wakeup)
	.db    250                            ; MaxPower 500mA
highspd_dscr_end:

; INTERFACE DESCRIPTOR
	.db    DSCR_INTERFACE_LEN             ; bLength
	.db    DSCR_INTERFACE_TYPE            ; bDescriptorType
	.db    0                              ; bInterfaceNumber
	.db    0                              ; bAlternateSetting
	.db    4                              ; bNumEndpoints
	.db    0xff                           ; bInterfaceClass
	.db    0x00                           ; bInterfaceSubClass
	.db    0x00                           ; bInterfaceProtocol
	.db    0                              ; iInterface (string index)

; EP1OUT
	.db    DSCR_ENDPOINT_LEN              ; bLength
	.db    DSCR_ENDPOINT_TYPE             ; bDescriptorType
	.db    0x01                           ; bEndpointAddress (0x01 = EP1OUT)
	.db    ENDPOINT_TYPE_BULK             ; bmAttributes
	.db    0x00                           ; wMaxPacketSize LSB
	.db    0x02                           ; wMaxPacketSize MSB (0x0200 = 512 bytes, but buffer is only 64 bytes)
	.db    0x00                           ; bInterval

; EP1IN
	.db    DSCR_ENDPOINT_LEN              ; bLength
	.db    DSCR_ENDPOINT_TYPE             ; bDescriptorType
	.db    0x81                           ; bEndpointAddress (0x81 = EP1IN)
	.db    ENDPOINT_TYPE_BULK             ; bmAttributes
	.db    0x00                           ; wMaxPacketSize LSB
	.db    0x02                           ; wMaxPacketSize MSB (0x0200 = 512 bytes, but buffer is only 64 bytes)
	.db    0x00                           ; bInterval

; EP2OUT
	.db    DSCR_ENDPOINT_LEN              ; bLength
	.db    DSCR_ENDPOINT_TYPE             ; bDescriptorType
	.db    0x02                           ; bEndpointAddress
	.db    ENDPOINT_TYPE_BULK             ; bmAttributes
	.db    0x00                           ; wMaxPacketSize LSB
	.db    0x02                           ; wMaxPacketSize MSB (0x0200 = 512 bytes)
	.db    0x00                           ; bInterval

; EP4OUT
;	.db    DSCR_ENDPOINT_LEN              ; bLength
;	.db    DSCR_ENDPOINT_TYPE             ; bDescriptorType
;	.db    0x04                           ; bEndpointAddress
;	.db    ENDPOINT_TYPE_BULK             ; bmAttributes
;	.db    0x00                           ; wMaxPacketSize LSB
;	.db    0x02                           ; wMaxPacketSize MSB (0x0200 = 512 bytes)
;	.db    0x00                           ; bInterval

; EP6IN
	.db    DSCR_ENDPOINT_LEN              ; bLength
	.db    DSCR_ENDPOINT_TYPE             ; bDescriptorType
	.db    0x86                           ; bEndpointAddress
	.db    ENDPOINT_TYPE_BULK             ; bmAttributes
	.db    0x00                           ; wMaxPacketSize LSB
	.db    0x02                           ; wMaxPacketSize MSB (0x0200 = 512 bytes)
	.db    0x00                           ; bInterval

; EP8IN
;	.db    DSCR_ENDPOINT_LEN              ; bLength
;	.db    DSCR_ENDPOINT_TYPE             ; bDescriptorType
;	.db    0x88                           ; bEndpointAddress
;	.db    ENDPOINT_TYPE_BULK             ; bmAttributes
;	.db    0x00                           ; wMaxPacketSize LSB
;	.db    0x02                           ; wMaxPacketSize MSB (0x0200 = 512 bytes)
;	.db    0x00                           ; bInterval

highspd_dscr_realend:

_dev_qual_dscr:
	.db    dev_qualdscr_end-_dev_qual_dscr  ; 0 bLength 1 Descriptor size in bytes (0Ah)
	.db    DSCR_DEVQUAL_TYPE                ; 1 bDescriptorType 1 The constant DEVICE_QUALIFIER (06h)
	.dw    0x0002                           ; 2 bcdUSB 2 USB specification release number (BCD)
	.db    0x00                             ; 4 bDeviceClass 1 Class code (Defined at Interface level)
	.db    0x00                             ; 5 bDeviceSubclass 1 Subclass code (Defined at Interface level)
	.db    0x00                             ; 6 bDeviceProtocol 1 Protocol Code (Defined at Interface level)
	.db    64                               ; 7 bMaxPacketSize0 1 Maximum packet size for endpoint zero
	.db    1                                ; 8 bNumConfigurations 1 Number of possible configurations
	.db    0                                ; 9 Reserved 1 For future use
dev_qualdscr_end:

.even
_fullspd_dscr:
	.db    fullspd_dscr_end-_fullspd_dscr      ; Descriptor length
	.db    DSCR_CONFIG_TYPE
	; can't use .dw because byte order is different
	.db    (fullspd_dscr_realend-_fullspd_dscr) % 256 ; total length of config lsb
	.db    (fullspd_dscr_realend-_fullspd_dscr) / 256 ; total length of config msb
	.db    1                         ; n interfaces
	.db    1                         ; config number
	.db    0                         ; config string
	.db    0x80                      ; attrs = bus powered, no wakeup
	.db    0x32                      ; max power = 100ma
fullspd_dscr_end:

; all the interfaces next 
; NOTE the default TRM actually has more alt interfaces
; but you can add them back in if you need them.
; here, we just use the default alt setting 1 from the trm
	.db    DSCR_INTERFACE_LEN
	.db    DSCR_INTERFACE_TYPE
	.db    0                         ; index
	.db    0                         ; alt setting idx
	.db    1                         ; n endpoints    
	.db    0xff                      ; class
	.db    0xff
	.db    0xff
	.db    0                         ; string index    

; The sole endpoint:
	.db    DSCR_ENDPOINT_LEN
	.db    DSCR_ENDPOINT_TYPE
	.db    0x06                      ; 0x82 = EP2IN, 0x02 = EP2OUT
	.db    ENDPOINT_TYPE_BULK        ; type
	.db    0x00                      ; max packet LSB
	.db    0x02                      ; max packet size=512 bytes
	.db    0x00                      ; polling interval
fullspd_dscr_realend:

	.even
_dev_strings:
string0:
	.db    string0end-string0        ; String descriptor length
	.db    DSCR_STRING_TYPE
	.db    0x09, 0x04                ; 0x0409 is the language code for English.
string0end:

; Manufacture
string1:
       	.db    string1end-string1        ; String descriptor length
	.db    DSCR_STRING_TYPE
	.ascii 'M'
	.db    0
	.ascii 'a'
	.db    0
	.ascii 'k'
	.db    0
	.ascii 'e'
	.db    0
	.ascii 'S'
	.db    0
	.ascii 't'
	.db    0
	.ascii 'u'
	.db    0
	.ascii 'f'
	.db    0
	.ascii 'f'
	.db    0
string1end:

; Product
string2:
	.db    string2end-string2
	.db    DSCR_STRING_TYPE
	.ascii 'F'
	.db    0
	.ascii 'P'
	.db    0
	.ascii 'G'
	.db    0
	.ascii 'A'
	.db    0
	.ascii 'L'
	.db    0
	.ascii 'i'
	.db    0
	.ascii 'n'
	.db    0
	.ascii 'k'
	.db    0
	.ascii '/'
	.db    0
	.ascii 'F'
	.db    0
	.ascii 'X'
	.db    0
	.ascii '2'
	.db    0
	.ascii ' '
	.db    0
	.db    ((DATE>>(7*4))&0xF) + 48
	.db    0
	.db    ((DATE>>(6*4))&0xF) + 48
	.db    0
	.db    ((DATE>>(5*4))&0xF) + 48
	.db    0
	.db    ((DATE>>(4*4))&0xF) + 48
	.db    0
	.db    ((DATE>>(3*4))&0xF) + 48
	.db    0
	.db    ((DATE>>(2*4))&0xF) + 48
	.db    0
	.db    ((DATE>>(1*4))&0xF) + 48
	.db    0
	.db    (DATE&0xF) + 48
	.db    0
string2end:

_dev_strings_end:
	.dw 0x0000                       ; in case you wanted to look at memory between _dev_strings and _dev_strings_end
