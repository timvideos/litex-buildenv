# XXX remove this
MSCDIR=../../third_party/misoc
include $(MSCDIR)/software/common.mak

CFLAGS += -Wno-unused-function

OBJECTS=isr.o \
        processor.o \
        hdmi_in0.o \
        hdmi_in1.o \
        hdmi_out0.o \
        hdmi_out1.o \
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

all: firmware.bin

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@
	cp $@ boot.bin

firmware.elf: $(OBJECTS) libs

%.elf:
	$(LD) $(LDFLAGS) \
		-T linker.ld \
		-N -o $@ \
		$(MSCDIR)/software/libbase/crt0-$(CPU).o \
		$(OBJECTS) \
		-L$(MSCDIR)/software/libbase \
		-L$(MSCDIR)/software/libcompiler-rt \
		-lbase-nofloat -lcompiler-rt
	chmod -x $@

main.o: main.c
	$(compile-dep)

%.o: %.c version.h
	$(compile-dep)

%.o: %.S
	$(assemble)

libs:
	$(MAKE) -C $(MSCDIR)/software/libcompiler-rt
	$(MAKE) -C $(MSCDIR)/software/libbase

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin
	$(RM) .*~ *~

version.h: version.sh
	bash version.sh

.PHONY: all main.o clean libs load version.h
