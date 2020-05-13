# Pano Logic Zero Client G2 targets

ifneq ($(PLATFORM),pano_logic_g2)
	$(error "Platform should be pano_logic_g2 when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

COMM_PORT ?= /dev/ttyUSB0
BAUD ?= 115200

ifeq ($(FIRMWARE),linux)


OVERRIDE_FIRMWARE=--override-firmware=none
define fbi_rule
$(1): $(subst .fbi,,$(1))
endef

TARGET_BUILD_DIR = build/$(FULL_PLATFORM)_$(TARGET)_$(FULL_CPU)
FIRMWARE_DIR = $(TARGET_BUILD_DIR)/software/$(FIRMWARE)

BUILDROOT_IMAGES = third_party/buildroot/output/images
KERNEL_FBI   = $(BUILDROOT_IMAGES)/Image.fbi
ROOTFS_FBI   = $(BUILDROOT_IMAGES)/rootfs.cpio.fbi
EMULATOR_FBI = $(TARGET_BUILD_DIR)/emulator/emulator.bin.fbi
DTB_FBI      = $(FIRMWARE_DIR)/rv32.dtb.fbi
FIRMWARE_FBI = $(KERNEL_FBI) $(ROOTFS_FBI) $(EMULATOR_FBI) $(DTB_FBI)

$(foreach file,$(FIRMWARE_FBI),$(eval $(call fbi_rule,$(file))))
endif

# Image
image-flash-$(PLATFORM): gateware-flash-$(PLATFORM) firmware-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	./load.py ise

ifeq ($(FIRMWARE),linux)
GATEWARE_BIN = $(TARGET_BUILD_DIR)/gateware+emulator+dtb.bin

$(GATEWARE_BIN): $(GATEWARE_FILEBASE).bin $(DTB_FBI) $(EMULATOR_FBI)
	# note: emulator and DTB are flashed with gateware to save flash space
	dd if=$(GATEWARE_FILEBASE).bin of=$@ bs=4259840 conv=sync
	dd if=$(DTB_FBI) bs=16K conv=sync >> $@
	cat $(EMULATOR_FBI) >> $@

# note: emulator and DTB are flashed with gateware to save flash space
gateware-flash-$(PLATFORM): $(GATEWARE_BIN)
ifeq ($(DUMMY_FLASH),)
	@echo "Flashing $(notdir( $(GATEWARE_BIN))) @ 0"
	$(PYTHON) flash.py --mode=other --other-file $(GATEWARE_BIN) --address 0
endif
	@true
else
gateware-flash-$(PLATFORM): gateware-flash-py
endif

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)


rootfs-flash-$(PLATFORM):
ifeq ($(DUMMY_FLASH),)
	@echo "Flashing roots @ 0x9c0000"
	$(PYTHON) flash.py --mode=other --other-file $(ROOTFS_FBI) --address 10223616
endif

kernel-flash-$(PLATFORM):
ifeq ($(DUMMY_FLASH),)
	@echo "Flashing kernel @ 0x440000"
	$(PYTHON) flash.py --mode=other --other-file $(KERNEL_FBI) --address 4456448
endif

ifeq ($(FIRMWARE),linux)
firmware-flash-$(PLATFORM): $(FIRMWARE_FBI) kernel-flash-$(PLATFORM) rootfs-flash-$(PLATFORM)
else
ifeq ($(FIRMWARE),micropython)
MICROPYTHON_FBI = $(TARGET_BUILD_DIR)/software/micropython/firmware.fbi

firmware-flash-$(PLATFORM):
	@echo "Flashing micropython @ 0x440000"
	$(PYTHON) flash.py --mode=other --other-file $(MICROPYTHON_FBI) --address 4456448
else
firmware-flash-$(PLATFORM): firmware-flash-py
endif
endif

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported"
	@false

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported"
	@false

