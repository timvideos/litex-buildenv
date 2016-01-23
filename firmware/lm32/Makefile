# XXX remove this
MSCDIR=../../third_party/misoc
include $(MSCDIR)/software/common.mak

OBJECTS=isr.o \
        processor.o \
        hdmi_in0.o \
        hdmi_in1.o \
        pattern.o \
        edid.o \
        pll.o \
        ci.o \
        config.o \
        encoder.o \
        fx2.o \
        i2c.o \
        main.o \
        hdmi_out0.o \
        hdmi_out1.o \
        opsis_eeprom_i2c.o \
        opsis_eeprom.o \
        tofe_eeprom_i2c.o \
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

%.o: %.c
	$(compile-dep)

%.o: %.S
	$(assemble)

define gen_i2c
@echo " GEN " $@
@sed -e "s/XI2C/I2C/g;s/Xi2c/i2c/g" $< > $@
endef

i2c.c: Xi2c.c
	$(gen_i2c)

i2c.h: Xi2c.h
	$(gen_i2c)

i2c.o: i2c.h

define gen_opsis_eeprom_i2c
@echo " GEN " $@
@sed -e "s/XI2C/OPSIS_EEPROM_I2C/g;s/Xi2c/opsis_eeprom_i2c/g" $< > $@
endef

opsis_eeprom_i2c.c: Xi2c.c
	$(gen_opsis_eeprom_i2c)

opsis_eeprom_i2c.h: Xi2c.h
	$(gen_opsis_eeprom_i2c)

opsis_eeprom_i2c.o: opsis_eeprom_i2c.h

define gen_tofe_eeprom_i2c
@echo " GEN " $@
@sed -e "s/XI2C/TOFE_EEPROM_I2C/g;s/Xi2c/tofe_eeprom_i2c/g" $< > $@
endef

tofe_eeprom_i2c.c: Xi2c.c
	$(gen_tofe_eeprom_i2c)

tofe_eeprom_i2c.h: Xi2c.h
	$(gen_tofe_eeprom_i2c)

tofe_eeprom_i2c.o: tofe_eeprom_i2c.h

libs:
	$(MAKE) -C $(MSCDIR)/software/libcompiler-rt
	$(MAKE) -C $(MSCDIR)/software/libbase

clean:
	$(RM) $(OBJECTS) $(OBJECTS:.o=.d) firmware.elf firmware.bin
	$(RM) .*~ *~

.PHONY: all main.o clean libs load
