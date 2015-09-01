# XXX remove this
MSCDIR=../../build/misoc
include $(MSCDIR)/software/common.mak

OBJECTS=isr.o processor.o hdmi_in0.o hdmi_in1.o pattern.o edid.o pll.o ci.o config.o encoder.o i2c.o main.o

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

.PHONY: all main.o clean libs load
