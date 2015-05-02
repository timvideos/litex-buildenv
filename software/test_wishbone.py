from misoclib.com.liteusb.software.wishbone import LiteUSBWishboneDriver

FTDI_INTERFACE_A = 1
FTDI_INTERFACE_B = 2

wb = LiteUSBWishboneDriver("ft2232h", FTDI_INTERFACE_B, "asynchronous", 2, debug=False)
wb.open()
for i in range(64):
    wb.write(0xe0003000, i)
data = wb.read(0x00000000, 128)
for value in data:
	print("{:08x}".format(value))
wb.close()
