include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

OBJECTS=\
	main.o \
	isr.o \
	boot-helper-$(CPU).o

CFLAGS += -I$(STUB_DIRECTORY) \
	-I$(FIRMWARE_DIRECTORY)

CFLAGS += \
	-Wall \
	-Werror \
	-Wno-error=unused-function \
	-Wno-error=unused-variable

LDFLAGS += \

LINKER_LD=linker.ld


all: firmware.bin firmware.fbi

%.fbi: %.bin
	$(PYTHON) -m litex.soc.tools.mkmscimg -f $< -o $@

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@

firmware.elf: $(STUB_DIRECTORY)/$(LINKER_LD) $(OBJECTS)

%.elf: ../libbase/crt0-$(CPU)-xip.o ../libbase/libbase-nofloat.a ../libcompiler_rt/libcompiler_rt.a
	$(LD) $(LDFLAGS) \
		-T $(STUB_DIRECTORY)/$(LINKER_LD) \
		-N -o $@ \
        ../libbase/crt0-$(CPU)-xip.o \
        $(OBJECTS) \
        -L../libbase \
		-lbase-nofloat \
        -L../libcompiler_rt \
		-lcompiler_rt
	chmod -x $@


# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

boot-helper-$(CPU).S: $(BIOS_DIRECTORY)/boot-helper-$(CPU).S
	cp $< $@

boot-helper-$(CPU).o: boot-helper-$(CPU).S
	$(assemble)

%.o: $(STUB_DIRECTORY)/%.c
	$(compile)

%.o: $(STUB_DIRECTORY)/%.S
	$(assemble)

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin .*~ *~
