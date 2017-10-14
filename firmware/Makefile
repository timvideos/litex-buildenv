include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

ifeq ($(PLATFORM),)
$(error PLATFORM not defined.)
endif
UPLATFORM = $(shell echo $(PLATFORM) | tr a-z A-Z)

ifeq ($(TARGET),)
$(error TARGET not defined.)
endif
UTARGET = $(shell echo $(TARGET) | tr a-z A-Z)

CFLAGS += -DPLATFORM_$(UPLATFORM) -DTARGET_$(UTARGET)

BUILD_DIRECTORY=$(BUILDINC_DIRECTORY)/../../
FIRMBUILD_DIRECTORY=$(BUILD_DIRECTORY)/software/firmware

OBJECTS=\
	bist.o \
	ci.o \
	config.o \
	edid.o \
	encoder.o \
	etherbone.o \
	ethernet.o \
	fx2.o \
	hdmi_in0.o \
	hdmi_out0.o \
	hdmi_out1.o \
	heartbeat.o \
	i2c.o \
	isr.o \
	main.o \
	mdio.o \
	mmcm.o \
	oled.o \
	opsis_eeprom.o \
	pattern.o \
	pll.o \
	processor.o \
	reboot.o \
	stdio_wrap.o \
	telnet.o \
	tofe_eeprom.o \
	uptime.o \
	version.o \
	$(FIRMBUILD_DIRECTORY)/version_data.o \
	$(FIRMBUILD_DIRECTORY)/hdmi_in1.o \
	boot-helper-$(CPU).o


CFLAGS += \
	-I$(FIRMWARE_DIRECTORY) \
	-I$(BUILD_DIRECTORY)/software/firmware

CFLAGS += \
	-Wall \
	-Werror \
	-Wno-error=unused-function \
	-Wno-error=unused-variable \


include $(UIP_DIRECTORY)/Makefile.mk

LDFLAGS += \

all: firmware.bin firmware.fbi

%.fbi: %.bin
	$(PYTHON) -m litex.soc.tools.mkmscimg -f $< -o $@

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@

firmware.elf: $(FIRMWARE_DIRECTORY)/linker.ld $(OBJECTS)

%.elf: ../libbase/crt0-$(CPU).o ../libbase/libbase-nofloat.a ../libcompiler_rt/libcompiler_rt.a ../uip/libuip.a
	$(LD) $(LDFLAGS) \
		-T $(FIRMWARE_DIRECTORY)/linker.ld \
		-N -o $@ \
                ../libbase/crt0-$(CPU).o \
                $(OBJECTS) \
                -L../libbase \
		-lbase-nofloat \
                -L../libcompiler_rt \
		-lcompiler_rt \
		-L../uip \
		-luip
	chmod -x $@

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

boot-helper-$(CPU).S: $(BIOS_DIRECTORY)/boot-helper-$(CPU).S
	cp $< $@

%.o: $(FIRMWARE_DIRECTORY)/%.c
	$(compile)

%.o: $(FIRMWARE_DIRECTORY)/%.S
	$(assemble)

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin .*~ *~

# Dependencies on generated files
ci.o: $(FIRMBUILD_DIRECTORY)/hdmi_in1.h
hdmi_in1.o: $(FIRMBUILD_DIRECTORY)/hdmi_in1.h $(FIRMBUILD_DIRECTORY)/hdmi_in1.c
pattern.o: $(FIRMBUILD_DIRECTORY)/version_data.h $(FIRMBUILD_DIRECTORY)/version_data.c
version.o: $(FIRMBUILD_DIRECTORY)/version_data.h $(FIRMBUILD_DIRECTORY)/version_data.c
version_data.o: $(FIRMBUILD_DIRECTORY)/version_data.h $(FIRMBUILD_DIRECTORY)/version_data.c

# Generated version info
$(FIRMBUILD_DIRECTORY)/version_data.h: version_data
$(FIRMBUILD_DIRECTORY)/version_data.c: version_data
version_data:
	bash $(FIRMWARE_DIRECTORY)/version_data.sh
	# Check the version files exist
	[ -e $(FIRMBUILD_DIRECTORY)/version_data.h ]
	[ -e $(FIRMBUILD_DIRECTORY)/version_data.c ]

# Generated hdmi_in1 from hdmi_in0
$(FIRMBUILD_DIRECTORY)/hdmi_in1.h: $(FIRMWARE_DIRECTORY)/hdmi_in0.h $(FIRMWARE_DIRECTORY)/hdmi_in.sh
	bash $(FIRMWARE_DIRECTORY)/hdmi_in.sh 1
	# Check the files exist
	[ -e $(FIRMBUILD_DIRECTORY)/hdmi_in1.h ]

$(FIRMBUILD_DIRECTORY)/hdmi_in1.c: $(FIRMWARE_DIRECTORY)/hdmi_in0.c $(FIRMWARE_DIRECTORY)/hdmi_in.sh
	bash $(FIRMWARE_DIRECTORY)/hdmi_in.sh 1
	# Check the files exist
	[ -e $(FIRMBUILD_DIRECTORY)/hdmi_in1.c ]

.PHONY: all clean libs version_data
