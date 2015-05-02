import sys

sys.path.append("../")
from ftdi import FTDI_INTERFACE_B

from misoclib.tools.litescope.software.driver.usb import LiteScopeUSB2WishboneFTDIDriver

wb = LiteScopeUSB2WishboneFTDIDriver(FTDI_INTERFACE_B, "asynchronous", 2, debug=False)
wb.open()
for i in range(256):
    wb.write(0xe0003000, i)
for i in range(256):
    print("%08x" %wb.read(4*i))
wb.close()
