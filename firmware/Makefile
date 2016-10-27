include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

BUILD_DIRECTORY=$(BUILDINC_DIRECTORY)/../../

OBJECTS=isr.o \
		ethernet.o \
		etherbone.o \
		telnet.o \
		mdio.o \
		config.o \
		processor.o \
		hdmi_in0.o \
		hdmi_in1.o \
		hdmi_out0.o \
		hdmi_out1.o \
		pattern.o \
		edid.o \
		pll.o \
		ci.o \
		encoder.o \
		i2c.o \
		main.o

CFLAGS += \
	-I. \
	-I$(LIBUIP_DIRECTORY)/../uip \
	-I$(LIBUIP_DIRECTORY)

all: firmware.bin

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@
	cp $@ $(BUILD_DIRECTORY)/software/boot.bin

firmware.elf: $(OBJECTS) libs
	$(LD) $(LDFLAGS) \
		-T $(FIRMWARE_DIRECTORY)/linker.ld \
		-N -o $@ \
                ../libbase/crt0-$(CPU).o \
                $(OBJECTS) \
                -L../libnet \
                -L../libbase \
                -L../libcompiler_rt \
		-L../libuip \
		-lbase-nofloat -luip -lcompiler_rt
	chmod -x $@

main.o: $(FIRMWARE_DIRECTORY)/main.c
	$(compile)

%.o: $(FIRMWARE_DIRECTORY)/%.c
	$(compile)

%.o: $(FIRMWARE_DIRECTORY)/%.S
	$(assemble)

load: firmware.bin
	litex_term --kernel firmware.bin COM8

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin .*~ *~

.PHONY: all main.o clean libs load
