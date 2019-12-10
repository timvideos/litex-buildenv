#ifndef __ETH_STREAM_H
#define __ETH_STREAM_H

#include <stdarg.h>

#include "contiki.h"
#include "contiki-net.h"

#define ETH_STREAM_PORT_IN 6000
#define ETH_STREAM_PORT_OUT 6001

#define ETH_STREAM_DATA_BUFFER_SIZE 4096
#define ETH_STREAM_CTL_BUFFER_SIZE 64

#define max(a,b) ((a>b)?a:b)
#define min(a,b) ((a<b)?a:b)

enum {
	ETH_STREAM_OUT_STATE_OFF,
	ETH_STREAM_OUT_STATE_READY,
	ETH_STREAM_OUT_STATE_BUSY,
	ETH_STREAM_OUT_STATE_CLOSE,
};

void eth_stream_init(void);

int eth_stream_in_event_cb(struct tcp_socket *s, void *ptr, tcp_socket_event_t event);
int eth_stream_in_data_cb(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen);

int eth_stream_out_event_cb(struct tcp_socket *s, void *ptr, tcp_socket_event_t event);
int eth_stream_out_data_cb(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen);

unsigned int eth_stream_in_framebuffer_base(void);

void eth_stream_out_service(void);
void eth_stream_out_base_write(unsigned int value);

#endif
