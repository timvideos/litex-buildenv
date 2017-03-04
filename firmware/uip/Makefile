include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

VPATH=$(UIP_DIRECTORY)

include $(UIP_DIRECTORY)/Makefile.mk

#See here for-fno-strict-aliasing -fpack-struct:
#http://sourceforge.net/p/contiki/mailman/message/28002063/

CCDEP=$(CC)

UIPCOREOBJS=$(LIBUIPDIR)/net/ip/dhcpc.o \
	$(LIBUIPDIR)/net/ip/psock.o \
	$(LIBUIPDIR)/net/ip/resolv.o \
	$(LIBUIPDIR)/net/ip/simple-udp.o \
	$(LIBUIPDIR)/net/ip/slipdev.o \
	$(LIBUIPDIR)/net/ip/tcpip.o \
	$(LIBUIPDIR)/net/ip/tcp-socket.o \
	$(LIBUIPDIR)/net/ip/udp-socket.o \
	$(LIBUIPDIR)/net/ip/uip-debug.o \
	$(LIBUIPDIR)/net/ip/uiplib.o \
	$(LIBUIPDIR)/net/ip/uip-packetqueue.o \
	$(LIBUIPDIR)/net/ip/uip-split.o \
	$(LIBUIPDIR)/net/ip/uip-udp-packet.o \
	$(LIBUIPDIR)/net/ipv4/uaodv.o \
	$(LIBUIPDIR)/net/ipv4/uaodv-rt.o \
	$(LIBUIPDIR)/net/ipv4/uip.o \
	$(LIBUIPDIR)/net/ipv4/uip_arp.o \
	$(LIBUIPDIR)/net/ipv4/uip-fw.o \
	$(LIBUIPDIR)/net/ipv4/uip-fw-drv.o \
	$(LIBUIPDIR)/net/ipv4/uip-neighbor.o \
	$(LIBUIPDIR)/net/ipv4/uip-over-mesh.o \
	$(LIBUIPDIR)/net/linkaddr.o \
	$(LIBUIPDIR)/net/nbr-table.o \
	$(LIBUIPDIR)/net/netstack.o \
	$(LIBUIPDIR)/net/packetbuf.o \
	$(LIBUIPDIR)/net/queuebuf.o \
	$(LIBUIPDIR)/sys/process.o \
	$(LIBUIPDIR)/sys/etimer.o \
	$(LIBUIPDIR)/sys/timer.o \
	$(LIBUIPDIR)/lib/list.o

UIPARCHOBJS=\
	$(UIPDIR)/clock-arch.o \
	$(UIPDIR)/rtimer-arch.o \
	$(UIPDIR)/liteethmac-drv.o

UIPOBJS=$(UIPCOREOBJS) $(UIPARCHOBJS)
OBJS_LIB+=$(UIPOBJS)

UIPLIB=libuip.a

all: $(UIPLIB)

.PHONY: all compile clean

# pull in dependency info for *existing* .o files
-include $(UIPOBJS:.o=.d)

%.o: %.c
	@mkdir -p $(@D)
	$(compile)

%.o: %.S
	@mkdir -p $(@D)
	$(assemble)

clean:
	rm -f $(UIPOBJS) $(UIPOBJS:.o=.d) libuip.a

libuip.a: $(UIPOBJS)
	$(AR) clr libuip.a $(UIPOBJS)
