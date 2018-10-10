# Sim targets

ifneq ($(PLATFORM),sim)
	$(error "Platform should be sim when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

# Gateware
gateware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

gateware-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

# Firmware
firmware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

firmware-connect-$(PLATFORM):
	@echo "Unsupported."
	@false

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
