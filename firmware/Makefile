OPSIS_DIR=../gateware/soc_basesoc_opsis_platform

include $(OPSIS_DIR)/software/include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

OBJECTS=isr.o main.o

all: firmware.bin

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@

firmware.elf: $(OBJECTS)
	$(LD) $(LDFLAGS) \
		-T linker.ld \
		-N -o $@ \
		 $(OPSIS_DIR)/software/libbase/crt0-$(CPU).o \
		$(OBJECTS) \
		-L$(OPSIS_DIR)/software/libbase \
		-L$(OPSIS_DIR)/software/libcompiler_rt \
		-lbase -lcompiler_rt
	chmod -x $@

main.o: main.c
	$(compile)

%.o: %.c
	$(compile)

%.o: %.S
	$(assemble)

load:
	litex_term --kernel firmware.bin COM8

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin .*~ *~

.PHONY: all main.o clean load
