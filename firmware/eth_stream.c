#include <stdio.h>
#include <stdarg.h>

#include "eth_stream.h"
#include "ethernet.h"
#include "framebuffer.h"
#include "processor.h"

static struct tcp_socket eth_stream_socket_in;
static struct tcp_socket eth_stream_socket_out;

static int eth_stream_in_pos;
static int eth_stream_out_pos;
static int eth_stream_out_state;

int eth_stream_in_fb_index;

static unsigned int eth_stream_out_next_fb;
static unsigned int eth_stream_out_size;

#ifdef ETHMAC_BASE
static uint8_t eth_stream_in_rx_buffer[ETH_STREAM_DATA_BUFFER_SIZE];
static uint8_t eth_stream_in_tx_buffer[ETH_STREAM_CTL_BUFFER_SIZE];

static uint8_t eth_stream_out_rx_buffer[ETH_STREAM_CTL_BUFFER_SIZE];
static uint8_t eth_stream_out_tx_buffer[ETH_STREAM_DATA_BUFFER_SIZE];
#endif


void eth_stream_init(void)
{
#ifdef ETHMAC_BASE
	tcp_socket_register(&eth_stream_socket_in, NULL,
			eth_stream_in_rx_buffer, sizeof(eth_stream_in_rx_buffer),
			eth_stream_in_tx_buffer, sizeof(eth_stream_in_tx_buffer),
			(tcp_socket_data_callback_t) eth_stream_in_data_cb,
			(tcp_socket_event_callback_t) eth_stream_in_event_cb);
	tcp_socket_listen(&eth_stream_socket_in, ETH_STREAM_PORT_IN);

	tcp_socket_register(&eth_stream_socket_out, NULL,
			eth_stream_out_rx_buffer, sizeof(eth_stream_out_rx_buffer),
			eth_stream_out_tx_buffer, sizeof(eth_stream_out_tx_buffer),
			(tcp_socket_data_callback_t) eth_stream_out_data_cb,
			(tcp_socket_event_callback_t) eth_stream_out_event_cb);
	tcp_socket_listen(&eth_stream_socket_out, ETH_STREAM_PORT_OUT);

	eth_stream_in_fb_index = 0;

	printf("Ethernet streamer listening on ports %d(in) %d(out)\n", ETH_STREAM_PORT_IN, ETH_STREAM_PORT_OUT);
#endif
}

int eth_stream_in_event_cb(struct tcp_socket *s, void *ptr, tcp_socket_event_t event)
{
	switch(event)
	{
		case TCP_SOCKET_CONNECTED:
			eth_stream_in_pos = 0;
			break;
		case TCP_SOCKET_CLOSED:
			eth_stream_in_fb_index = (eth_stream_in_fb_index + 1) % 4;
			break;
		case TCP_SOCKET_TIMEDOUT:
		case TCP_SOCKET_ABORTED:
		default:
			break;
	}
	return 0;
}

int eth_stream_in_data_cb(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen)
{
	char idx = (eth_stream_in_fb_index + 1) % 4;
	uint8_t *fb_base = (uint8_t*)fb_ptrdiff_to_main_ram(eth_stream_in_framebuffer_base(idx));
	memcpy(fb_base + eth_stream_in_pos, rxbuf, rxlen);
	eth_stream_in_pos += rxlen;
	return 0;
}

unsigned int eth_stream_in_framebuffer_base(char n) {
	return FRAMEBUFFER_BASE_ETH_IN + n * FRAMEBUFFER_SIZE;
}

int eth_stream_out_event_cb(struct tcp_socket *s, void *ptr, tcp_socket_event_t event)
{
	switch(event)
	{
		case TCP_SOCKET_CONNECTED:
			eth_stream_out_state = ETH_STREAM_OUT_STATE_READY;
			break;
		case TCP_SOCKET_DATA_SENT:
			break;
		case TCP_SOCKET_CLOSED:
		case TCP_SOCKET_TIMEDOUT:
		case TCP_SOCKET_ABORTED:
		default:
			eth_stream_out_state = ETH_STREAM_OUT_STATE_OFF;
			break;
	}
	return 0;
}

int eth_stream_out_data_cb(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen)
{
	return 0;
}

void eth_stream_out_service(void)
{
	uint8_t *eth_fb = (uint8_t*)fb_ptrdiff_to_main_ram(FRAMEBUFFER_BASE_ETH_OUT);
	uint8_t *src_fb = (uint8_t*)fb_ptrdiff_to_main_ram(eth_stream_out_next_fb);
	int xfer_size = min(ETH_STREAM_DATA_BUFFER_SIZE, eth_stream_out_size - eth_stream_out_pos);

	switch(eth_stream_out_state)
	{
		case ETH_STREAM_OUT_STATE_OFF:
			return;
		case ETH_STREAM_OUT_STATE_READY:
			eth_stream_out_size = processor_h_active * processor_v_active * 2;
			eth_stream_out_pos = 0;
			memcpy(eth_fb, src_fb, eth_stream_out_size);
			eth_stream_out_state = ETH_STREAM_OUT_STATE_BUSY;
			tcp_socket_send(&eth_stream_socket_out, (uint8_t*)&eth_stream_out_size, 4);
			break;
		case ETH_STREAM_OUT_STATE_BUSY:
			xfer_size = tcp_socket_send(&eth_stream_socket_out, eth_fb + eth_stream_out_pos, xfer_size);
			eth_stream_out_pos += xfer_size;
			if (eth_stream_out_pos == eth_stream_out_size)
				eth_stream_out_state = ETH_STREAM_OUT_STATE_CLOSE;
			break;
		case ETH_STREAM_OUT_STATE_CLOSE:
			tcp_socket_close(&eth_stream_socket_out);
		default:
			eth_stream_out_state = ETH_STREAM_OUT_STATE_OFF;
			break;
	}
}

void eth_stream_out_base_write(unsigned int value)
{
	eth_stream_out_next_fb = value;
}
