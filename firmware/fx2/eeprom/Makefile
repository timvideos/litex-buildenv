#
# Makefile for programming default USB VID/PID into FX2
#
#  https://github.com/timvideos/HDMI2USB/wiki/USB-IDs
#
# Joel Stanley <joel@jms.id.au>
#

FXCLI	= /usr/local/bin/fxcli

EEPROM	:= hdmi2usb_unconfigured.iic

CMD_LOAD_VIDPID := "\\xc0"
VID_MSB := \\x1d
VID_LSB := \\x50
PID_MSB := \\x60
PID_LSB := \\xb5

all: flash

flash: $(EEPROM)
	$(FXCLI) -v 1D50:60B5 -i 1443:0007 --eeprom=$<

$(EEPROM):
	echo -n -e $(CMD_LOAD_VIDPID) > $@
	echo -n -e $(VID_LSB)$(VID_MSB) >> $@
	echo -n -e $(PID_LSB)$(PID_MSB) >> $@
	echo -n -e \\x00\\x00\\x01 >> $@

dump: $(EEPROM)
	hexdump -C $<

clean:
	$(RM) $(EEPROM)
