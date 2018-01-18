# elbertv2 targets
#
# NOTE: elbertconfig.py will run only with python3, so we explicitly run python3

ifneq ($(PLATFORM),elbertv2)
	$(error "Platform should be elbertv2 when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

# Elbert V2 has programming port built in, but needs separate USB UART
# for communications (eg, interaction with Python REPL), currently assumed
# to be Digilent PMOD USBUART on P4, which has FTDI FT232RL and appears
# as /dev/ttyUSB0 or similar on modern Linux
#
# Serial Baud rate is assumed to be 19200bps on both links for simplicity /
# compatibilty with Numato Mimas v2
#
PORT ?= /dev/ttyACM0
PROG_PORT ?= $(PORT)
COMM_PORT ?= /dev/ttyUSB0
BAUD ?= 19200

# Image
image-flash-$(PLATFORM):
	python3 $$(which elbertconfig.py) $(PROG_PORT) $(IMAGE_FILE)

# Gateware
gateware-load-$(PLATFORM):
	@echo "ElbertV2 doesn't support loading, use the flash target instead."
	@echo "make gateware-flash"
	@false

gateware-flash-$(PLATFORM):
	python3 $$(which elbertconfig.py) $(PROG_PORT) $(GATEWARE_FILEBASE).bin

# Firmware
firmware-load-$(PLATFORM):
	flterm --port=$(COMM_PORT) --kernel=$(FIRMWARE_FILEBASE).bin --speed=$(BAUD)

firmware-flash-$(PLATFORM):
	@echo "ElbertV2 doesn't support just flashing firmware, use image target instead."
	@echo "make image-flash"
	@false

firmware-connect-$(PLATFORM):
	flterm --port=$(COMM_PORT) --speed=$(BAUD)

firmware-clear-$(PLATFORM):
	@echo "FIXME: Unsupported?."
	@false

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

# Extra commands
help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported."
	@false
