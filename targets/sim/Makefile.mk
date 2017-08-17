# Sim targets

DEFAULT_TARGET = base

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

help-sim:
	@echo " make sim-setup"
	@echo " make sim-teardown"

.PHONY: sim-setup sim-teardown help-sim
