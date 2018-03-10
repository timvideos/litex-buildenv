ifneq ($(OS),Windows_NT)
ifeq ($(HDMI2USB_ENV),)
    $(error "Please enter environment. 'source scripts/enter-env.sh'")
endif

# Force colors despite running through tee.
COLORAMA=force
export COLORAMA

endif

PYTHON ?= python
export PYTHON

SPLIT_REGEX := ^\([^.]*\)\.\?\(.*\)$$

# The platform to run on. It is made up of FPGA_MAIN_BOARD.EXPANSION_BOARD
DEFAULT_PLATFORM = opsis
DEFAULT_PLATFORM_EXPANSION =

ifneq ($(FULL_PLATFORM),)
    PLATFORM_PART := $(shell echo $(FULL_PLATFORM) | sed -e's/$(SPLIT_REGEX)/\1/')
    PLATFORM_EXPANSION_PART := $(shell echo $(FULL_PLATFORM) | sed -e's/$(SPLIT_REGEX)/\2/')

    # Check PLATFORM value matches FULL_PLATFORM bits
    ifneq ($(PLATFORM),)
        ifneq ($(PLATFORM),$(PLATFORM_PART))
            $(error "FULL_PLATFORM was set to '$(FULL_PLATFORM)' ($(PLATFORM_PART)), but PLATFORM was set to '$(PLATFORM)'.")
        endif
    else
        PLATFORM=$(PLATFORM_PART)
    endif

    # Check PLATFORM_EXPANSION value matches FULL_PLATFORM bits
    ifneq ($(PLATFORM_EXPANSION),)
        ifneq ($(PLATFORM_EXPANSION),$(PLATFORM_EXPANSION_PART))
            $(error "FULL_PLATFORM was set to '$(FULL_PLATFORM)', but PLATFORM_EXPANSION was set to '$(PLATFORM_EXPANSION)'.")
        endif
    else
        PLATFORM_EXPANSION=$(PLATFORM_EXPANSION_PART)
    endif
endif
PLATFORM ?= $(DEFAULT_PLATFORM)
PLATFORM_EXPANSION ?= $(DEFAULT_PLATFORM_EXPANSION)

ifeq ($(PLATFORM),)
    $(error "Internal error: PLATFORM not set.")
endif
export PLATFORM
ifeq ($(PLATFORM_EXPANSION),)
FULL_PLATFORM = $(PLATFORM)
else
FULL_PLATFORM = $(PLATFORM).$(PLATFORM_EXPANSION)
MAKE_LITEX_EXTRA_CMDLINE += -Ot expansion $(PLATFORM_EXPANSION)
endif

# The soft CPU core to use inside the FPGA it is made up of CPU.VARIANT.
DEFAULT_CPU = lm32
DEFAULT_CPU_VARIANT =
ifneq ($(FULL_CPU),)
    CPU_PART := $(shell echo $(FULL_CPU) | sed -e's/$(SPLIT_REGEX)/\1/')
    CPU_VARIANT_PART := $(shell echo $(FULL_CPU) | sed -e's/$(SPLIT_REGEX)/\2/')

    # Check CPU value matches FULL_CPU bits
    ifneq ($(CPU),)
        ifneq ($(CPU),$(CPU_PART))
            $(error "FULL_CPU was set to '$(FULL_CPU)' ($(CPU_PART)), but CPU was set to '$(CPU)'.")
        endif
    else
        CPU=$(CPU_PART)
    endif

    # Check CPU_VARIANT value matches FULL_CPU bits
    ifneq ($(CPU_VARIANT),)
        ifneq ($(CPU_VARIANT),$(CPU_VARIANT_PART))
            $(error "FULL_CPU was set to '$(FULL_CPU)', but CPU_VARIANT was set to '$(CPU_VARIANT)'.")
        endif
    else
        CPU_VARIANT=$(CPU_VARIANT_PART)
    endif
endif

CPU ?= $(DEFAULT_CPU)
CPU_VARIANT ?= $(DEFAULT_CPU_VARIANT)

ifeq ($(CPU),)
    $(error "Internal error: CPU not set.")
endif
export CPU
ifeq ($(CPU_VARIANT),)
FULL_CPU = $(CPU)
else
FULL_CPU = $(CPU).$(CPU_VARIANT)
MAKE_LITEX_EXTRA_CMDLINE += -Ot cpu_variant $(CPU_VARIANT)
endif

# Include platform specific targets
include targets/$(PLATFORM)/Makefile.mk
TARGET ?= $(DEFAULT_TARGET)
ifeq ($(TARGET),)
    $(error "Internal error: TARGET not set.")
endif
export TARGET

FIRMWARE ?= firmware
ifeq ($(FIRMWARE),)
    FIRMWARE = firmware
endif
export FIRMWARE

# We don't use CLANG
CLANG = 0
export CLANG

JOBS ?= $(shell nproc)
JOBS ?= 2

ifeq ($(shell [ $(JOBS) -gt 1 ] && echo true),true)
    export MAKEFLAGS="-j $(JOBS) -l $(JOBS)"
endif

TARGET_BUILD_DIR = build/$(FULL_PLATFORM)_$(TARGET)_$(FULL_CPU)/

GATEWARE_FILEBASE = $(TARGET_BUILD_DIR)/gateware/top
BIOS_FILE = $(TARGET_BUILD_DIR)/software/bios/bios.bin
FIRMWARE_FILEBASE = $(TARGET_BUILD_DIR)/software/$(FIRMWARE)/firmware
IMAGE_FILE = $(TARGET_BUILD_DIR)/image-gateware+bios+$(FIRMWARE).bin

TFTP_IPRANGE ?= 192.168.100
export TFTP_IPRANGE
TFTPD_DIR ?= build/tftpd/

# Well known TFTP Server Port is UDP/69
# Default to high numbered port so we can run TFTP server as non-root
# (export into shell environment to use during building firmware BIOS)
#
TFTP_SERVER_PORT ?= 6069
export TFTP_SERVER_PORT

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
		$(MAKE_LITEX_EXTRA_CMDLINE) \

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
FIRMWARE_FBI=
else
OVERRIDE_FIRMWARE=--override-firmware=$(FIRMWARE_FILEBASE).fbi
FIRMWARE_FBI=$(FIRMWARE_FILEBASE).fbi
endif

$(IMAGE_FILE): $(GATEWARE_FILEBASE).bin $(BIOS_FILE) $(FIRMWARE_FBI)
	$(PYTHON) mkimage.py \
		$(MISOC_EXTRA_CMDLINE) $(LITEX_EXTRA_CMDLINE) $(MAKE_LITEX_EXTRA_CMDLINE) \
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

image-flash-py: image
	$(PYTHON) flash.py --mode=image

.PHONY: image image-load image-flash image-flash-py image-flash-$(PLATFORM) image-load-$(PLATFORM)
.NOTPARALLEL: image-load image-flash image-flash-py image-flash-$(PLATFORM) image-load-$(PLATFORM)

# Submodule checks
#
# Generate third_party/*/.git dependencies to force checkouts of submodules
#
# Also check for non-matching submodules, and warn that update might be
# needed (but do not force to match, as that makes development difficult)
# This is indicated by a "git submodule status" that does not start with
# a space (" ").
#
LITEX_SUBMODULES=litex litedram liteeth litepcie litesata litescope liteusb litevideo
litex-submodules: $(addsuffix /.git,$(addprefix third_party/,$(LITEX_SUBMODULES)))
	@if git submodule status --recursive | grep "^[^ ]" >/dev/null; then \
		echo ""; \
		echo "***************************************************************************"; \
		echo "WARNING: the following submodules do not match expected commit:"; \
		echo ""; \
		git submodule status --recursive | grep "^[^ ]"; \
		echo ""; \
		echo "If you are not developing in submodules you may need to run:"; \
		echo ""; \
		echo "git submodule update --init --recursive"; \
		echo ""; \
		echo "manually to bring everything back in sync with upstream"; \
		echo "***************************************************************************"; \
		echo ""; \
	fi

# Gateware - the stuff which configures the FPGA.
# --------------------------------------
gateware: litex-submodules
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

gateware-flash-py:
	$(PYTHON) flash.py --mode=gateware

gateware-clean:
	rm -rf $(TARGET_BUILD_DIR)/gateware

.PHONY: gateware gateware-load gateware-flash gateware-flash-py gateware-clean gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)
.NOTPARALLEL: gateware-load gateware-flash gateware-flash-py gateware-flash-$(PLATFORM) gateware-load-$(PLATFORM)

# Firmware - the stuff which runs in the soft CPU inside the FPGA.
# --------------------------------------
firmware-cmd: litex-submodules
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

firmware-flash-py: firmware
	$(PYTHON) flash.py --mode=firmware

firmware-connect: firmware-connect-$(PLATFORM)
	@true

firmware-clear: firmware-clear-$(PLATFORM)
	@true

firmware-clean:
	rm -rf $(TARGET_BUILD_DIR)/software

firmware-test:
	scripts/check-firmware-newlines.sh

.PHONY: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-flash-py firmware-connect-$(PLATFORM) firmware-clear-$(PLATFORM)
.NOTPARALLEL: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-flash-py firmware-connect-$(PLATFORM) firmware-clear-$(PLATFORM)
.PHONY: firmware-cmd $(FIRMWARE_FILEBASE).bin firmware firmware-load firmware-flash firmware-connect firmware-clean firmware-test
.NOTPARALLEL: firmware-cmd firmware-load firmware-flash firmware-connect

$(BIOS_FILE): firmware-cmd
	@true

bios: $(BIOS_FILE)
	@true

bios-flash: $(BIOS_FILE) bios-flash-$(PLATFORM)
	@true

.PHONY: $(FIRMWARE_FILE) bios bios-flash bios-flash-$(PLATFORM)
.NOTPARALLEL: bios-flash bios-flash-$(PLATFORM)


# TFTP booting stuff
# --------------------------------------
# TFTP server for minisoc to load firmware from
#
# We can run the TFTP server as the user if port >= 1024
# otherwise we need to run as root using sudo

ATFTPD:=$(shell which atftpd 2>/dev/null)
ifeq ($(ATFTPD),)
ATFTPD:=/usr/sbin/atftpd
endif

# Requires HPA in.tftpd not traditional BSD in.tftpd
# Unfortunately in.tftpd seems to require root always
# even if run as current user, otherwise it reports
# "cannot set groups for user $USER"
#
IN_TFTPD:=$(shell which in.tftpd 2>/dev/null)
ifeq ($(IN_TFTPD),)
IN_TFTPD:=/usr/sbin/in.tftpd
endif

tftp: $(FIRMWARE_FILEBASE).bin
	mkdir -p $(TFTPD_DIR)
	cp $(FIRMWARE_FILEBASE).bin $(TFTPD_DIR)/boot.bin

tftpd_stop:
	# FIXME: This is dangerous...
	@if [ $(TFTP_SERVER_PORT) -lt 1024 ]; then \
		sudo true; \
		sudo killall atftpd || sudo killall in.tftpd || true; \
	else \
		killall atftpd || \
		if ps axuwww | grep -v grep | \
			grep "[i]n.tftpd" >/dev/null 2>&1; then \
				sudo killall in.tftpd; \
		fi || true; \
	fi

tftpd_start:
	mkdir -p $(TFTPD_DIR)
	@if [ $(TFTP_SERVER_PORT) -lt 1024 ]; then \
		echo "Root required to run TFTP Server, will use sudo"; \
		sudo true; \
	fi
	@if [ -x "$(ATFTPD)" ]; then \
		echo "Starting atftpd"; \
		if [ $(TFTP_SERVER_PORT) -lt 1024 ]; then \
			sudo "$(ATFTPD)" --verbose --bind-address $(TFTP_IPRANGE).100 --port $(TFTP_SERVER_PORT) --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) --group $(shell id -gn) $(TFTPD_DIR) & \
		else \
			"$(ATFTPD)" --verbose --bind-address $(TFTP_IPRANGE).100 --port $(TFTP_SERVER_PORT) --daemon --logfile /dev/stdout --no-fork --user $(shell whoami) --group $(shell id -gn) $(TFTPD_DIR) & \
		fi \
	elif [ -x "$(IN_TFTPD)" ]; then \
		echo "Starting in.tftpd"; \
		if [ $(TFTP_SERVER_PORT) -lt 1024 ]; then \
			sudo "$(IN_TFTPD)" --verbose --listen --address $(TFTP_IPRANGE).100:$(TFTP_SERVER_PORT)  --user $(shell whoami) -s $(TFTPD_DIR) & \
		else \
			echo "Root required to run in.tftpd, will use sudo"; \
			sudo true; \
			sudo "$(IN_TFTPD)" --verbose --listen --address $(TFTP_IPRANGE).100:$(TFTP_SERVER_PORT) --user $(shell whoami) -s $(TFTPD_DIR) & \
		fi \
	else \
		echo "Cannot find an appropriate tftpd binary to launch the server."; \
		false; \
	fi

.PHONY: tftp tftpd_stop tftpd_start
.NOTPARALLEL: tftp tftpd_stop tftpd_start

# Extra targets
# --------------------------------------
flash: image-flash
	@true

env:
	@echo "export PLATFORM='$(PLATFORM)'"
	@echo "export PLATFORM_EXPANSION='$(PLATFORM_EXPANSION)'"
	@echo "export TARGET='$(TARGET)'"
	@echo "export DEFAULT_TARGET='$(DEFAULT_TARGET)'"
	@echo "export CPU='$(CPU)'"
	@echo "export CPU_VARIANT='$(CPU_VARIANT)'"
	@echo "export FIRMWARE='$(FIRMWARE)'"
	@echo "export OVERRIDE_FIRMWARE='$(OVERRIDE_FIRMWARE)'"
	@echo "export PROG='$(PROG)'"
	@echo "export TARGET_BUILD_DIR='$(TARGET_BUILD_DIR)'"
	@echo "export TFTP_DIR='$(TFTPD_DIR)'"
	@echo "export MISOC_EXTRA_CMDLINE='$(MISOC_EXTRA_CMDLINE)'"
	@echo "export LITEX_EXTRA_CMDLINE='$(LITEX_EXTRA_CMDLINE)'"
	@echo "export MAKE_LITEX_EXTRA_CMDLINE='$(MAKE_LITEX_EXTRA_CMDLINE)'"
	@# Hardcoded values
	@echo "export CLANG=$(CLANG)"
	@echo "export PYTHONHASHSEED=$(PYTHONHASHSEED)"
	@echo "export JOBS=$(JOBS)"
	@# Files
	@echo "export IMAGE_FILE='$(IMAGE_FILE)'"
	@echo "export GATEWARE_FILEBASE='$(GATEWARE_FILEBASE)'"
	@echo "export FIRMWARE_FILEBASE='$(FIRMWARE_FILEBASE)'"
	@echo "export BIOS_FILE='$(BIOS_FILE)'"
	@# Network settings
	@echo "export TFTP_IPRANGE='$(TFTP_IPRANGE)'"
	@echo "export TFTP_SERVER_PORT='$(TFTP_SERVER_PORT)'"
	@echo "export TFTPD_DIR='$(TFTPD_DIR)'"

info:
	@echo "              Platform: $(FULL_PLATFORM)"
	@echo "                Target: $(TARGET) (default: $(DEFAULT_TARGET))"
	@echo "                   CPU: $(FULL_CPU) (default: $(DEFAULT_CPU))"
	@if [ x"$(FIRMWARE)" != x"firmware" ]; then \
		echo "               Firmare: $(FIRMWARE) (default: firmware)"; \
	fi

prompt:
	@echo -n "P=$(FULL_PLATFORM)"
	@if [ x"$(TARGET)" != x"$(DEFAULT_TARGET)" ]; then echo -n " T=$(TARGET)"; fi
	@if [ x"$(CPU)" != x"$(DEFAULT_CPU)" ]; then echo -n " C=$(CPU)"; fi
	@if [ x"$(CPU_VARIANT)" != x"$(DEFAULT_CPU_VARIANT)" ]; then echo -n ".$(CPU_VARIANT)"; fi
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
	@echo " CPU_VARIANT describes which soft-CPU variant to use on the FPGA."
	@echo " CPU_VARIANT=<variant such as min OR full>"
	@echo "                        (current: $(CPU_VARIANT), default: $(DEFAULT_CPU_VARIANT))"
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
	@echo " make reset             - Reset the device."
	@echo ""
	@echo "Firmware make commands avaliable:"
	@echo " make firmware          - Build the firmware"
	@echo " make firmware-test     - Run firmware tests"
	@echo " make firmware-load     - *Temporarily* load the firmware onto a device"
	@echo " make firmware-flash    - *Permanently* flash the firmware onto a device"
	@echo " make firmware-connect  - *Connect* to the firmware running on a device"
	@echo " make firmware-clear    - *Permanently* erase the firmware on the device,"
	@echo "                          forcing TFTP/serial booting"
	@echo ""
	@echo "Image commands avaliable:"
	@echo " make image             - Make an image containing gateware+bios+firmware"
	@echo " make image-flash       - *Permanently* flash an image onto a device"
	@echo " make flash             - Alias for image-flash"
	@echo ""
	@echo "Other Make commands avaliable:"
	@make -s help-$(PLATFORM)
	@echo " make test              - Run all tests"
	@echo " make clean             - Clean all build artifacts."

reset: reset-$(PLATFORM)
	@true

clean:
	rm -f build/cache.mk
	rm -rf $(TARGET_BUILD_DIR)
	py3clean . 2>/dev/null || rm -rf $$(find -name __pycache__)

dist-clean:
	rm -rf build

.PHONY: flash env info prompt help clean dist-clean help-$(PLATFORM) reset reset-$(PLATFORM)
.NOTPARALLEL: flash env prompt info help help-$(PLATFORM) reset reset-$(PLATFORM)

# Tests
# --------------------------------------
TEST_MODULES=edid-decode
test-submodules: $(addsuffix /.git,$(addprefix third_party/,$(TEST_MODULES)))
	@true

test-edid: test-submodules
	$(MAKE) -C test/edid check

test: firmware-test
	@echo "Tests passed"

.PHONY: test test-edid
.NOTPARALLEL: test test-edid
