NEXYS_DIR=../build

include $(NEXYS_DIR)/software/include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

UIPDIR=uip
LIBUIPDIR=libuip

OBJECTS=isr.o \
		ethernet.o \
		etherbone.o \
		telnet.o \
		mdio.o \
		ci.o \
		i2c.o \
		main.o

CFLAGS += -I. -I$(UIPDIR) -I$(LIBUIPDIR)

all: firmware.bin

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
	chmod -x $@
	cp $@ boot.bin

firmware.elf: $(OBJECTS) libs
	$(LD) $(LDFLAGS) \
		-T linker.ld \
		-N -o $@ \
		 $(NEXYS_DIR)/software/libbase/crt0-$(CPU).o \
		$(OBJECTS) \
		-L$(NEXYS_DIR)/software/libbase \
		-L$(NEXYS_DIR)/software/libcompiler_rt \
		-L$(LIBUIPDIR) \
		-lbase-nofloat -luip -lcompiler_rt
	chmod -x $@

main.o: main.c
	$(compile)

%.o: %.c
	$(compile)

%.o: %.S
	$(assemble)

libs:
	$(MAKE) -C $(LIBUIPDIR)

clean:
	cd libuip && make clean
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin .*~ *~

.PHONY: all main.o clean libs load
