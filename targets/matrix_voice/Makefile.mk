# matrix_voice targets

ifneq ($(PLATFORM),matrix_voice)
	$(error "Platform should be matrix_voice when using this file!?")
endif

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-$(PLATFORM):
	@echo "MATRIX Voice doesn't support just flashing firmware from PC, try xc3sprog running in the Raspberry instead."

# Gateware
gateware-load-$(PLATFORM):
	@echo "MATRIX Voice doesn't support just flashing firmware from PC, try xc3sprog running in the Raspberry instead."
	@false

gateware-flash-$(PLATFORM): $(GATEWARE_BIOS_FILE)
	@echo "MATRIX Voice doesn't support just flashing firmware from PC, try xc3sprog running in the Raspberry instead."
	@false

firmware-load-$(PLATFORM):
	@echo "MATRIX Voice doesn't support firmware load from PC, try flterm running in the Raspberry instead."
	@false

firmware-flash-$(PLATFORM):
	@echo "MATRIX Voice doesn't support flashing firmware from PC, try flterm running in the Raspberry instead."
	@false

firmware-connect-$(PLATFORM):
	@echo "MATRIX Voice doesn't support connect from PC, try flterm running in the Raspberry instead."

firmware-clear-$(PLATFORM):
	@echo "Unsupported."
	@false

bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

help-$(PLATFORM):
	@true

reset-$(PLATFORM):
	@echo "Unsupported."
	@false

