# XXX remove this
MSCDIR=../../third_party/misoc
include $(MSCDIR)/software/common.mak

ifeq ($(BOARD),)
$(error BOARD not defined.)
endif
UBOARD = $(shell echo $(BOARD) | tr a-z A-Z)

ifeq ($(TARGET),)
$(error TARGET not defined.)
endif
UTARGET = $(shell echo $(TARGET) | tr a-z A-Z)

CFLAGS += -Wno-unused-function -DBOARD_$(UBOARD) -DTARGET_$(UTARGET)

OBJECTS=isr.o \
        processor.o \
        hdmi_in0.o \
        hdmi_in1.o \
        hdmi_out0.o \
        hdmi_out1.o \
        heartbeat.o \
        pattern.o \
        edid.o \
        pll.o \
        ci.o \
        config.o \
        encoder.o \
        fx2.o \
        i2c.o \
        main.o \
        opsis_eeprom.o \
        tofe_eeprom.o \
	version.o \
	version_data.o \

all: version_data libs firmware.bin

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@
	cp $@ boot.bin

firmware.elf: $(OBJECTS)

%.elf: linker.ld $(MSCDIR)/software/libbase/crt0-$(CPU).o $(MSCDIR)/software/libbase/libbase-nofloat.a $(MSCDIR)/software/libcompiler-rt/libcompiler-rt.a
	$(LD) $(LDFLAGS) \
		-T linker.ld \
		-N -o $@ \
		$(MSCDIR)/software/libbase/crt0-$(CPU).o \
		$(OBJECTS) \
		-L$(MSCDIR)/software/libbase \
		-L$(MSCDIR)/software/libcompiler-rt \
		-lbase-nofloat -lcompiler-rt
	chmod -x $@

%.o: %.c
	$(compile-dep)

%.o: %.S
	$(assemble)

libs:
	$(MAKE) -C $(MSCDIR)/software/libcompiler-rt
	$(MAKE) -C $(MSCDIR)/software/libbase

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin
	$(RM) .*~ *~
	$(RM) version_data.h version_data.c

version_data.h: version_data
version_data.c: version_data
version_data:
	bash version_data.sh

.PHONY: all clean libs load version_data
