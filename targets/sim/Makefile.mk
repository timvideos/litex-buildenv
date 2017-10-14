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

.PHONY: image-flash-$(PLATFORM)

# Gateware
gateware-load-$(PLATFORM):
	@echo "Unsupported."
	@false

gateware-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: gateware-load-$(PLATFORM) gateware-flash-$(PLATFORM)

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

.PHONY: firmware-load-$(PLATFORM) firmware-flash-$(PLATFORM) firmware-connect-$(PLATFORM)

# Bios
bios-flash-$(PLATFORM):
	@echo "Unsupported."
	@false

.PHONY: bios-flash-$(PLATFORM)

# Extra Commands
help-$(PLATFORM):
	@echo " make $(PLATFORM)-setup"
	@echo " make $(PLATFORM)-teardown"

$(PLATFORM)-setup:
	sudo true
	sudo openvpn --mktun --dev tap0
	sudo ifconfig tap0 $(IPRANGE).100 up
	sudo mknod /dev/net/tap0 c 10 200
	sudo chown $(shell whoami) /dev/net/tap0
	make tftpd_start

$(PLATFORM)-teardown:
	sudo true
	make tftpd_stop
	sudo rm -f /dev/net/tap0
	sudo ifconfig tap0 down
	sudo openvpn --rmtun --dev tap0

.PHONY: help-$(PLATFORM)
.PHONY: $(PLATFORM)-setup $(PLATFORM)-teardown
