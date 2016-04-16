
ifneq ($(OS),Windows_NT)
ifneq "$(HDMI2USB_ENV)" "1"
$(error "Please 'source scripts/setup-env.sh'")
endif
endif

# Turn off Python's hash randomization
PYTHONHASHSEED := 0
export PYTHONHASHSEED

# Default board
BOARD ?= atlys
export BOARD
# Default targets for a given board
ifeq ($(BOARD),pipistrello)
    TARGET ?= base
else ifeq ($(BOARD),minispartan6)
    TARGET ?= video
else
    TARGET ?= hdmi2usb
endif
export TARGET
# Default programmer
PROG ?= openocd
ifneq ($(PROG),)
    PROGRAMMER_OPTION ?= --platform-option programmer $(PROG)
endif

FILTER ?= tee

MSCDIR ?= third_party/misoc
HDMI2USBDIR = $(realpath .)
PYTHON = python3
DATE = `date +%Y_%m_%d`

# We use the special PIPESTATUS which is bash only below.
SHELL := /bin/bash

FLASH_PROXIES=$(HDMI2USBDIR)/third_party/flash_proxies

MAKEPY_CMD = \
  cd $(MSCDIR) && \
  $(PYTHON) \
  make.py \
    --external $(HDMI2USBDIR) \
    --flash-proxy-dir $(FLASH_PROXIES) \
    --target $(BOARD)_$(TARGET) \
    --target-option firmware_filename $(HDMI2USBDIR)/firmware/lm32/firmware.bin \
    --csr_csv $(HDMI2USBDIR)/test/csr.csv \
    $(PROGRAMMER_OPTION) \
    $(MISOC_EXTRA_CMDLINE)

MAKEIMAGE_CMD = \
  cd $(MSCDIR) && \
  $(PYTHON) \
  mkmscimg.py

FLASHEXTRA_CMD = \
  cd $(MSCDIR) && \
  $(PYTHON) \
  flash_extra.py \
    --external $(HDMI2USBDIR) \
    --flash-proxy-dir $(FLASH_PROXIES) \
    $(PROGRAMMER_OPTION) \
    $(BOARD)


ifeq ($(OS),Windows_NT)
	FLTERM = $(PYTHON) $(MSCDIR)/tools/flterm.py
else
	FLTERM = $(MSCDIR)/tools/flterm
endif

# Every target has a lm32 softcore
include Makefile.lm32

# The edid_debug and hdmi2usb also use the Cypress FX2
ifneq ($(filter $(TARGET),edid_debug hdmi2usb),)
include Makefile.fx2
endif

help:
	@echo "Environment:"
	@echo "  BOARD=atlys OR opsis OR pipistrello  (current: $(BOARD))"
	@echo " TARGET=base OR hdmi2usb OR hdmi2eth"
	@echo "                        (current: $(TARGET))"
	@echo "   PROG=programmer      (current: $(PROG))"
	@echo ""
	@if [ ! -z "$(TARGETS)" ]; then echo " Extra firmware needed for: $(TARGETS)"; echo ""; fi
	@echo "Targets avaliable:"
	@echo " make help"
	@echo " make all"
	@echo " make gateware"
	@echo " make firmware"
	@echo " make download-prebuilt"
	@echo " make load"
	@echo " make flash"
	@for T in $(TARGETS); do make -s help-$$T; done
	@echo " make clean"

# All target
all: clean gateware firmware
	echo "Run 'make load' to load the firmware."

# Initialize submodules automatically
third_party/%/.git: .gitmodules
	git submodule sync --recursive -- $$(dirname $@)
	git submodule update --recursive --init $$(dirname $@)
	touch $@ -r .gitmodules

# Gateware
MODULES=migen misoc liteeth litescope
gateware-submodules: $(addsuffix /.git,$(addprefix third_party/,$(MODULES)))
	@true

gateware-generate: gateware-submodules $(addprefix gateware-generate-,$(TARGETS))
	@echo 'Building target: $@. First dep: $<'
ifneq ($(OS),Windows_NT)
	$(MAKEPY_CMD) --build-option run False build-csr-csv build-bitstream \
	| $(FILTER) $(PWD)/build/output.$(DATE).log; (exit $${PIPESTATUS[0]})
else
	$(MAKEPY_CMD) --build-option run False build-csr-csv build-bitstream
endif

gateware-build: gateware-submodules $(addprefix gateware-build-,$(TARGETS))
ifneq ($(OS),Windows_NT)
	$(MAKEPY_CMD) build-csr-csv build-bitstream \
	| $(FILTER) $(PWD)/build/output.$(DATE).log; (exit $${PIPESTATUS[0]})
else
	$(MAKEPY_CMD) build-csr-csv build-bitstream
endif

gateware: gateware-generate gateware-build
	@true

# Firmware
firmware: $(addprefix firmware-,$(TARGETS))
	@true

# Download pre-built firmware
download-prebuilt:
	scripts/download-prebuilt.sh
	
# Load
load-gateware:
	$(MAKEPY_CMD) load-bitstream

load: load-gateware $(addprefix load-,$(TARGETS))
	@true

# Flash
flash-gateware:
	$(MAKEPY_CMD) flash-bitstream

flash: flash-gateware  $(addprefix flash-,$(TARGETS))
	@echo ""
	@echo ""
	@echo "Power cycle your board to boot newly flashed stuff."

# Clean
clean:
	@for T in $(TARGETS); do make clean-$$T; done
	if [ -f $(MSCDIR)/software/include/generated/cpu.mak ]; then \
		($(MAKEPY_CMD) clean) \
	fi
	# FIXME - This is a temporarily hack until misoc clean works better.
	rm -rf $(MSCDIR)/software/include/generated && ( \
		mkdir $(MSCDIR)/software/include/generated && \
		touch $(MSCDIR)/software/include/generated/.keep_me)
	# Cleanup Python3's __pycache__ directories
	find . -name __pycache__ -type d -exec rm -r {} +
	# Delete any previously downloaded pre-built firmware
	rm -rf build/prebuilt
	rm -f third_party/misoc/build/*.bit
	rm -f firmware/fx2/hdmi2usb.hex


.DEFAULT_GOAL := help
.NOTPARALLEL: *
.PHONY: help all third_party/* gateware-submodules gateware-generate gateware-build gateware firmware download-prebuilt test
