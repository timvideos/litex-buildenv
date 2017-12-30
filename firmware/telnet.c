// This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#include <stdio.h>
#include <stdarg.h>

#include "telnet.h"
#include "ethernet.h"

#define TELNET_RINGBUFFER_SIZE_RX 128
#define TELNET_RINGBUFFER_MASK_RX (TELNET_RINGBUFFER_SIZE_RX-1)

static char telnet_rx_buf[TELNET_RINGBUFFER_SIZE_RX];
static volatile unsigned int telnet_rx_produce;
static unsigned int telnet_rx_consume;

void telnet_init(void)
{
	telnet_active = 0;
	tcp_socket_register(&telnet_socket, NULL,
		telnet_rx_buffer, TELNET_BUFFER_SIZE_RX,
		telnet_tx_buffer, TELNET_BUFFER_SIZE_TX,
		(tcp_socket_data_callback_t) telnet_data_callback,
		(tcp_socket_event_callback_t) telnet_event_callback);
	tcp_socket_listen(&telnet_socket, TELNET_PORT);
	printf("Telnet listening on port %d\r\n", TELNET_PORT);
}

int telnet_event_callback(struct tcp_socket *s, void *ptr, tcp_socket_event_t event)
{
	switch(event)
	{
		case TCP_SOCKET_CONNECTED:
			printf("\r\nTelnet connected.\r\n");
			telnet_active = 1;
			break;
		case TCP_SOCKET_CLOSED:
		case TCP_SOCKET_TIMEDOUT:
		case TCP_SOCKET_ABORTED:
			printf("\r\nTelnet disconnected.\r\n");
			telnet_active = 0;
		default:
			break;
	}
	return 0;
}


int telnet_data_callback(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen)
{
	int i;
	unsigned int telnet_rx_produce_next;

	for(i=0; i<rxlen; i++) {
		telnet_rx_produce_next = (telnet_rx_produce + 1) & TELNET_RINGBUFFER_MASK_RX;
		if(telnet_rx_produce_next != telnet_rx_consume) {
				telnet_rx_buf[telnet_rx_produce] = rxbuf[i];
				telnet_rx_produce = telnet_rx_produce_next;
		}
	}
	return 0;
}

char telnet_readchar(void)
{
	char c;

	if(telnet_readchar_nonblock() == 0)
		return 0;

	c = telnet_rx_buf[telnet_rx_consume];
	telnet_rx_consume = (telnet_rx_consume + 1) & TELNET_RINGBUFFER_MASK_RX;
	return c;
}

int telnet_readchar_nonblock(void)
{
	return (telnet_rx_consume != telnet_rx_produce);
}

int telnet_putchar(char c)
{
	tcp_socket_send(&telnet_socket, (unsigned char *)&c, 1);
	return c;
}

int telnet_puts(const char *s)
{
	while(*s) {
		telnet_putchar(*s);
		s++;
	}
	telnet_putchar('\n');
	return 1;
}

void telnet_putsnonl(const char *s)
{
	while(*s) {
		telnet_putchar(*s);
		s++;
	}
}

#define TELNET_PRINTF_BUFFER_SIZE 256

int telnet_printf(const char *fmt, ...)
{
	int len = 0;
	va_list args;
	va_start(args, fmt);
	len = telnet_vprintf(fmt, args);
	va_end(args);
	return len;
}

int telnet_vprintf(const char *fmt, va_list args)
{
	int len;
	char outbuf[TELNET_PRINTF_BUFFER_SIZE];

	len = vscnprintf(outbuf, sizeof(outbuf), fmt, args);
	outbuf[len] = 0;
	telnet_putsnonl(outbuf);

	return len;
}
