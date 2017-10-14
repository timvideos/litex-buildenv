# Sim targets

# Settings
DEFAULT_TARGET = base
TARGET ?= $(DEFAULT_TARGET)

# Image
image-flash-sim:
	@echo "Unsupported."
	@false

.PHONY: image-flash-sim

# Gateware
gateware-load-sim:
	@echo "Unsupported."
	@false

gateware-flash-sim:
	@echo "Unsupported."
	@false

.PHONY: gateware-load-sim gateware-flash-sim

# Firmware
firmware-load-sim:
	@echo "Unsupported."
	@false

firmware-flash-sim:
	@echo "Unsupported."
	@false

firmware-connect-sim:
	@echo "Unsupported."
	@false

.PHONY: firmware-load-sim firmware-flash-sim firmware-connect-sim

# Bios
bios-flash-sim:
	@echo "Unsupported."
	@false

.PHONY: bios-flash-sim

# Extra Commands
help-sim:
	@echo " make sim-setup"
	@echo " make sim-teardown"

sim-setup:
	sudo true
	sudo openvpn --mktun --dev tap0
	sudo ifconfig tap0 $(IPRANGE).100 up
	sudo mknod /dev/net/tap0 c 10 200
	sudo chown $(shell whoami) /dev/net/tap0
	make tftpd_start

sim-teardown:
	sudo true
	make tftpd_stop
	sudo rm -f /dev/net/tap0
	sudo ifconfig tap0 down
	sudo openvpn --rmtun --dev tap0

.PHONY: help-sim
.PHONY: sim-setup sim-teardown
