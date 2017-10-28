
OPENOCD_CMD="openocd -f board/$(OPENOCD_BOARD)"

GATEWARE="$(TARGET_BUILD_DIR)/gateware/top."
IMAGE="$(TARGET_BUILD_DIR)/image."

define OPENOCD_LOAD
	init
	pld load 0 $(FILE).bit
	exit
endef

define OPENOCD_FLASH
	init
	jtagspi_init 0 $(PROXY)
	flash banks
	flash list
	flash info 0
	jtagspi_program $(FILE).bin 0x$()
endef

gateware-load-openocd:
	openocd -f board/$(OPENOCD_BOARD) \
		-c "init; pld load 0 $(TARGET_BUILD_DIR)/gateware/top.bit; exit"

