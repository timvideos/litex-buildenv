ifneq ($(OS),Windows_NT)
ifeq ($(HDMI2USB_ENV),)
    $(error "Please enter environment. 'source scripts/enter-env.sh'")
endif
endif

PYTHON ?= python
export PYTHON

PLATFORM ?= opsis
export PLATFORM
# Default board
ifeq ($(PLATFORM),)
    $(error "PLATFORM not set, please set it.")
endif

# Include platform specific targets
include targets/$(PLATFORM)/Makefile.mk
TARGET ?= $(DEFAULT_TARGET)
ifeq ($(TARGET),)
    $(error "Internal error: TARGET not set.")
endif
export TARGET

DEFAULT_CPU = lm32
CPU ?= $(DEFAULT_CPU)
ifeq ($(CPU),)
    $(error "Internal error: CPU not set.")
endif
export CPU

FIRMWARE ?= firmware

# We don't use CLANG
CLANG = 0
export CLANG

ifeq ($(PLATFORM_EXPANSION),)
FULL_PLATFORM = $(PLATFORM)
else
FULL_PLATFORM = $(PLATFORM).$(PLATFORM_EXPANSION)
LITEX_EXTRA_CMDLINE += -Ot expansion $(PLATFORM_EXPANSION)
endif
TARGET_BUILD_DIR = build/$(FULL_PLATFORM)_$(TARGET)_$(CPU)/

GATEWARE_FILEBASE = $(TARGET_BUILD_DIR)/gateware/top
BIOS_FILE = $(TARGET_BUILD_DIR)/software/bios/bios.bin
FIRMWARE_FILEBASE = $(TARGET_BUILD_DIR)/software/$(FIRMWARE)/firmware
IMAGE_FILE = $(TARGET_BUILD_DIR)/image-gateware+bios+$(FIRMWARE).bin

TFTP_IPRANGE ?= 192.168.100
export TFTP_IPRANGE
TFTPD_DIR ?= build/tftpd/

# Couple of Python settings.
# ---------------------------------
# Turn off Python's hash randomization
PYTHONHASHSEED := 0
export PYTHONHASHSEED
# ---------------------------------

MAKE_CMD=\
	time $(PYTHON) -u ./make.py \
		--platform=$(PLATFORM) \
		--target=$(TARGET) \
		--cpu-type=$(CPU) \
		--iprange=$(TFTP_IPRANGE) \
		$(MISOC_EXTRA_CMDLINE) \
		$(LITEX_EXTRA_CMDLINE) \

# We use the special PIPESTATUS which is bash only below.
SHELL := /bin/bash

FILTER ?= tee -a
LOGFILE ?= $(PWD)/$(TARGET_BUILD_DIR)/output.$(shell date +%Y%m%d-%H%M%S).log

build/cache.mk: targets/*/*.py scripts/makefile-cache.sh
	@mkdir -p build
	@./scripts/makefile-cache.sh

-include build/cache.mk

TARGETS=$(TARGETS_$(PLATFORM))


# Initialize submodules automatically
third_party/%/.git: .gitmodules
	git submodule sync --recursive -- $$(dirname $@)
	git submodule update --recursive --init $$(dirname $@)
	touch $@ -r .gitmodules

# Image - a combination of multiple parts (gateware+bios+firmware+more?)
# --------------------------------------
ifeq ($(FIRMWARE),none)
OVERRIDE_FIRMWARE=--override-firmware=none
else
OVERRIDE_FIRMWARE=--override-firmware=$(FIRMWARE_FILEBASE).fbi
endif

$(IMAGE_FILE): $(GATEWARE_FILEBASE).bin $(BIOS_FILE) $(FIRMWARE_FILEBASE).fbi
	$(PYTHON) mkimage.py \
		$(MISOC_EXTRA_CMDLINE) $(LITEX_EXTRA_CMDLINE) \
		--override-gateware=$(GATEWARE_FILEBASE).bin \
		--override-bios=$(BIOS_FILE) \
		$(OVERRIDE_FIRMWARE) \
		--output-file=$(IMAGE_FILE)

$(TARGET_BUILD_DIR)/image.bin: $(IMAGE_FILE)
	cp $< $@

image: $(IMAGE_FILE)
	@true

image-load: image image-load-$(PLATFORM)
	@true

image-flash: image image-flash-$(PLATFORM)
	@true

.PHONY: image image-load image-flash

# Gateware - the stuff which configures the FPGA.
# --------------------------------------
GATEWARE_MODULES=litex litedram liteeth litepcie litesata litescope liteusb litevideo litex
gateware-submodules: $(addsuffix /.git,$(addprefix third_party/,$(GATEWARE_MODULES)))
	@true

gateware: gateware-submodules
	mkdir -p $(TARGET_BUILD_DIR)
ifneq ($(OS),Windows_NT)
	$(MAKE_CMD) \
		2>&1 | $(FILTER) $(LOGFILE); (exit $${PIPESTATUS[0]})
else
	$(MAKE_CMD)
endif

gateware-fake:
	touch $(GATEWARE_FILEBASE).bit
	touch $(GATEWARE_FILEBASE).bin

$(GATEWARE_FILEBASE).bit:
	make gateware

$(GATEWARE_FILEBASE).bin:
	make gateware

gateware-load: $(GATEWARE_FILEBASE).bit gateware-load-$(PLATFORM)
	@true

gateware-flash: $(GATEWARE_FILEBASE).bin gateware-flash-$(PLATFORM)
	@true

gateware-clean:
	rm -rf $(TARGET_BUILD_DIR)/gateware

.PHONY: gateware gateware-load gateware-flash gateware-clean

# Firmware - the stuff which runs in the soft CPU inside the FPGA.
# --------------------------------------
firmware-cmd:
	mkdir -p $(TARGET_BUILD_DIR)
ifneq ($(OS),Windows_NT)
	$(MAKE_CMD) --no-compile-gateware \
		2>&1 | $(FILTER) $(LOGFILE); (exit $${PIPESTATUS[0]})
else
	$(MAKE_CMD) --no-compile-gateware
endif

$(FIRMWARE_FILEBASE).bin: firmware-cmd
	@true

$(FIRMWARE_FILEBASE).fbi: $(FIRMWARE_FILEBASE).bin
	$(PYTHON) -m litex.soc.tools.mkmscimg -f $< -o $@

firmware: $(FIRMWARE_FILEBASE).bin
	@true

firmware-load: firmware firmware-load-$(PLATFORM)
	@true

firmware-flash: firmware firmware-flash-$(PLATFORM)
	@true

firmware-connect: firmware-connect-$(PLATFORM)
	@true

firmware-clean:
	rm -rf $(TARGET_BUILD_DIR)/software

.PHONY: firmware-cmd $(FIRMWARE_FILEBASE).bin firmware firmware-load firmware-flash firmware-connect firmware-clean

$(BIOS_FILE): firmware-cmd
	@true

bios: $(BIOS_FILE)
	@true

bios-flash: $(BIOS_FILE) bios-flash-$(PLATFORM)
	@true

.PHONY: $(FIRMWARE_FILE) bios bios-flash

# TFTP booting stuff
# --------------------------------------
# TFTP server for minisoc to load firmware from
tftp: firmware
	mkdir -p $(TFTPD_DIR)
	cp $(TARGET_BUILD_DIR)/software/firmware/firmware.bin $(TFTPD_DIR)/boot.bin

tftpd_stop:
	sudo true
	sudo killall atftpd || true	# FIXME: This is dangerous...

tftpd_start:
	mkdir -p $(TFTPD_DIR)
	sudo true
	sudo atftpd --verbose --bind-address $(TFTP_IPRANGE).100 --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) $(TFTPD_DIR) &

.PHONY: tftp tftpd_stop tftpd_start

# Extra targets
# --------------------------------------
flash: image-flash
	@true

env:
	@echo "PLATFORM='$(PLATFORM)'"
	@echo "PLATFORM_EXPANSION='$(PLATFORM_EXPANSION)'"
	@echo "FULL_PLATFORM='$(FULL_PLATFORM)'"
	@echo "TARGET='$(TARGET)'"
	@echo "DEFAULT_TARGET='$(DEFAULT_TARGET)'"
	@echo "CPU='$(CPU)'"
	@echo "FIRMWARE='$(FIRMWARE)'"
	@echo "PROG='$(PROG)'"
	@echo "TARGET_BUILD_DIR='$(TARGET_BUILD_DIR)'"
	@echo "MISOC_EXTRA_CMDLINE='$(MISOC_EXTRA_CMDLINE)'"
	@echo "LITEX_EXTRA_CMDLINE='$(LITEX_EXTRA_CMDLINE)'"
	# Hardcoded values
	@echo "CLANG=$(CLANG)"
	@echo "PYTHONHASHSEED=$(PYTHONHASHSEED)"

info:
	@echo "              Platform: $(FULL_PLATFORM)"
	@echo "                Target: $(TARGET)"
	@echo "                   CPU: $(CPU)"
	@if [ x"$(FIRMWARE)" != x"firmware" ]; then \
		echo "               Firmare: $(FIRMWARE)"; \
	fi

prompt:
	@echo -n "P=$(PLATFORM)"
	@if [ x"$(TARGET)" != x"$(DEFAULT_TARGET)" ]; then echo -n " T=$(TARGET)"; fi
	@if [ x"$(CPU)" != x"$(DEFAULT_CPU)" ]; then echo -n " C=$(CPU)"; fi
	@if [ x"$(FIRMWARE)" != x"firmware" ]; then \
		echo -n " F=$(FIRMWARE)"; \
	fi
	@if [ x"$(JIMMO)" != x"" ]; then \
		echo -n " JIMMO"; \
	fi
	@if [ x"$(PROG)" != x"" ]; then echo -n " P=$(PROG)"; fi
	@BRANCH="$(shell git symbolic-ref --short HEAD 2> /dev/null)"; \
		if [ "$$BRANCH" != "master" ]; then \
			if [ x"$$BRANCH" = x"" ]; then \
				BRANCH="???"; \
			fi; \
			echo " R=$$BRANCH"; \
		fi

# @if [ ! -z "$(TARGETS)" ]; then echo " Extra firmware needed for: $(TARGETS)"; echo ""; fi
# FIXME: Add something about the TFTP stuff
# FIXME: Add something about TFTP_IPRANGE for platforms which have NET targets.
help:
	@echo "Environment:"
	@echo " PLATFORM describes which device you are targetting."
	@echo " PLATFORM=$(shell echo $(PLATFORMS) | sed -e's/ / OR /g')" | sed -e's/ OR $$//'
	@echo "                        (current: $(PLATFORM))"
	@echo ""
	@echo " PLATFORM_EXPANSION describes any expansion board you have plugged into your device."
	@echo " PLATFORM_EXPANSION=<expansion board>"
	@echo "                        (current: $(PLATFORM_EXPANSION))"
	@echo ""
	@echo " TARGET describes a set of functionality to use (see doc/targets.md for more info)."
	@echo " TARGET=$(shell echo $(TARGETS) | sed -e's/ / OR /g')" | sed -e's/ OR $$//'
	@echo "                        (current: $(TARGET), default: $(DEFAULT_TARGET))"
	@echo ""
	@echo " CPU describes which soft-CPU to use on the FPGA."
	@echo " CPU=lm32 OR or1k"
	@echo "                        (current: $(CPU), default: $(DEFAULT_CPU))"
	@echo ""
	@echo " FIRMWARE describes the code running on the soft-CPU inside the FPGA."
	@echo " FIRMWARE=firmware OR micropython"
	@echo "                        (current: $(FIRMWARE))"
	@echo ""
	@echo "Gateware make commands avaliable:"
	@echo " make gateware          - Build the gateware"
	@echo " make gateware-load     - *Temporarily* load the gateware onto a device"
	@echo " make gateware-flash    - *Permanently* flash gateware onto a device"
	@echo " make bios              - Build the bios"
	@echo " make bios-flash        - *Permanently* flash the bios onto a device"
	@echo "                          (Only needed on low resource boards.)"
	@echo ""
	@echo "Firmware make commands avaliable:"
	@echo " make firmware          - Build the firmware"
	@echo " make firmware-load     - *Temporarily* load the firmware onto a device"
	@echo " make firmware-flash    - *Permanently* flash the firmware onto a device"
	@echo " make firmware-connect  - *Connect* to the firmware running on a device"
	@echo ""
	@echo "Image commands avaliable:"
	@echo " make image             - Make an image containing gateware+bios+firmware"
	@echo " make image-flash       - *Permanently* flash an image onto a device"
	@echo " make flash             - Alias for image-flash"
	@echo ""
	@echo "Other Make commands avaliable:"
	@make -s help-$(PLATFORM)
	@echo " make clean             - Clean all build artifacts."

clean:
	rm build/cache.mk
	rm -rf $(TARGET_BUILD_DIR)
	py3clean . || rm -rf $$(find -name __pycache__)

dist-clean:
	rm -rf build

.PHONY: flash help clean dist-clean

# Tests
# --------------------------------------
TEST_MODULES=edid-decode
test-submodules: $(addsuffix /.git,$(addprefix third_party/,$(TEST_MODULES)))
	@true

test-edid: test-submodules
	$(MAKE) -C test/edid check

test:
	true

.PHONY: test test-edid
