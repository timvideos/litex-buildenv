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
endif

# Image
image-flash-$(PLATFORM): gateware-flash-$(PLATFORM) firmware-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	./load.py ise

ifeq ($(FIRMWARE),linux)
GATEWARE_BIN = $(TARGET_BUILD_DIR)/gateware+emulator+dtb.bin

$(GATEWARE_BIN): $(GATEWARE_FILEBASE).bin $(DTB_FBI) $(EMULATOR_FBI)
	# note: emulator and DTB are flash with gateware to save flash space
	dd if=$(GATEWARE_FILEBASE).bin of=$@ bs=4259840 conv=sync
	dd if=$(DTB_FBI) bs=16K conv=sync >> $@
	cat $(EMULATOR_FBI) >> $@

gateware-flash-$(PLATFORM): $(GATEWARE_BIN)
	# note: emulator and DTB are flash with gateware to save flash space
	@echo "Flashing $(GATEWARE_BIN) @ 0x9c0000"
	$(PYTHON) flash.py --mode=other --other-file $(GATEWARE_BIN) --address 0
	@true
else
gateware-flash-$(PLATFORM): gateware-flash-py
endif

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)


rootfs-flash-$(PLATFORM):
	@echo "Flashing roots @ 0x9c0000"
	$(PYTHON) flash.py --mode=other --other-file $(ROOTFS_FBI) --address 10223616

kernel-flash-$(PLATFORM):
	@echo "Flashing kernel @ 0x440000"
	$(PYTHON) flash.py --mode=other --other-file $(KERNEL_FBI) --address 4456448

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
