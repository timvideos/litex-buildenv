# Makefile for kernel module

KERNEL_VERSION:=$(shell uname -r)
KERNEL_PATH:=/lib/modules/$(KERNEL_VERSION)/build

obj-m = hdmi2pcie.o
hdmi2pcie-objs = main.o

all: hdmi2pcie.ko

hdmi2pcie.ko: main.c
	make -C $(KERNEL_PATH) M=$(shell pwd) modules

clean:
	make -C $(KERNEL_PATH) M=$(shell pwd) clean
	rm -f *~
