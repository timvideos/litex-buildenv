// This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#ifndef __TELNET_H
#define __TELNET_H

#include <stdarg.h>

#include "contiki.h"
#include "contiki-net.h"

//#define TELNET_DEBUG

#ifdef TELNET_DEBUG
	#define print_debug(...) printf(__VA_ARGS__)
#else
	#define print_debug(...) {}
#endif

#define TELNET_PORT 23
#define TELNET_BUFFER_SIZE_RX 4096
#define TELNET_BUFFER_SIZE_TX 4096

int telnet_active;

struct tcp_socket telnet_socket;
uint8_t telnet_rx_buffer[TELNET_BUFFER_SIZE_RX];
uint8_t telnet_tx_buffer[TELNET_BUFFER_SIZE_TX];

void telnet_init(void);
int telnet_event_callback(struct tcp_socket *s, void *ptr, tcp_socket_event_t event);
int telnet_data_callback(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen);

char telnet_readchar(void);
int telnet_readchar_nonblock(void);

int telnet_putchar(char c);
int telnet_puts(const char *s);
void telnet_putsnonl(const char *s);

int telnet_vprintf(const char *fmt, va_list argp);
int telnet_printf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

#endif
