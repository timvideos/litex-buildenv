// This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#include <generated/mem.h>

#ifdef ETHMAC_BASE

#include "etherbone.h"
#include "ethernet.h"

static unsigned char callback_buf[1512];
static unsigned int callback_buf_length;

void etherbone_init(void)
{
	callback_buf_length = 0;
	tcp_socket_register(&etherbone_socket, NULL,
		etherbone_rx_buf, ETHERBONE_BUFFER_SIZE_RX,
		etherbone_tx_buf, ETHERBONE_BUFFER_SIZE_TX,
		(tcp_socket_data_callback_t) etherbone_callback, NULL);
	tcp_socket_listen(&etherbone_socket, ETHERBONE_PORT);
	printf("Etherbone listening on port %d\n", ETHERBONE_PORT);
}

void etherbone_write(unsigned int addr, unsigned int value)
{
	unsigned int *addr_p = (unsigned int *)addr;
	*addr_p = value;
}

unsigned int etherbone_read(unsigned int addr)
{
	unsigned int value;
	unsigned int *addr_p = (unsigned int *)addr;
	value = *addr_p;
	return value;
}

int etherbone_callback(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen)
{
	struct etherbone_packet *packet;
	unsigned char * callback_buf_ptr;

	memcpy(callback_buf + callback_buf_length, rxbuf, rxlen);
	callback_buf_length += rxlen;
	callback_buf_ptr = callback_buf;

	while(callback_buf_length > 0) {
		packet = (struct etherbone_packet *)(callback_buf_ptr);
		/* seek header */
		if(packet->magic != 0x4e6f) {
			callback_buf_ptr++;
			callback_buf_length--;
		/* found header */
		} else {
			/* enough bytes for header? */
			if(callback_buf_length > ETHERBONE_HEADER_LENGTH) {
				unsigned int packet_length;
				packet_length = ETHERBONE_HEADER_LENGTH;
				if(packet->record_hdr.wcount)
					packet_length += (1 + packet->record_hdr.wcount)*4;
				if(packet->record_hdr.rcount)
					packet_length += (1 + packet->record_hdr.rcount)*4;
				/* enough bytes for packet? */
				if(callback_buf_length >= packet_length) {
					etherbone_process(s, callback_buf_ptr);
					callback_buf_ptr += packet_length;
					callback_buf_length -= packet_length;
				} else {
					memmove(callback_buf, callback_buf_ptr, callback_buf_length);
					return 0;
				}
			} else {
				memmove(callback_buf, callback_buf_ptr, callback_buf_length);
				return 0;
			}
		}
	}
	return 0;
}

void etherbone_process(struct tcp_socket *s, unsigned char *rxbuf)
{
	struct etherbone_packet *rx_packet = (struct etherbone_packet *)rxbuf;
	struct etherbone_packet *tx_packet = (struct etherbone_packet *)etherbone_tx_buf;
	unsigned int i;
	unsigned int addr;
	unsigned int data;
	unsigned int rcount, wcount;

	if(rx_packet->magic != 0x4e6f) return;   /* magic */
	if(rx_packet->addr_size != 4) return;    /* 32 bits address */
	if(rx_packet->port_size != 4) return;    /* 32 bits data */

	rcount = rx_packet->record_hdr.rcount;
	wcount = rx_packet->record_hdr.wcount;

	if(wcount > 0) {
		addr = rx_packet->record_hdr.base_write_addr;
		for(i=0;i<wcount;i++) {
			data = rx_packet->record[i].write_value;
			etherbone_write(addr, data);
			addr += 4;
		}
	}
	if(rcount > 0) {
		for(i=0;i<rcount;i++) {
			addr = rx_packet->record[i].read_addr;
			data = etherbone_read(addr);
			tx_packet->record[i].write_value = data;
		}
		tx_packet->magic = 0x4e6f;
		tx_packet->version = 1;
		tx_packet->nr = 1;
		tx_packet->pr = 0;
		tx_packet->pf = 0;
		tx_packet->addr_size = 4; // 32 bits
		tx_packet->port_size = 4; // 32 bits
		tx_packet->record_hdr.wcount = rcount;
		tx_packet->record_hdr.rcount = 0;
		tx_packet->record_hdr.base_write_addr = rx_packet->record_hdr.base_ret_addr;
		tcp_socket_send(&etherbone_socket,
						etherbone_tx_buf,
						sizeof(*tx_packet) + rcount*sizeof(struct etherbone_record));
	}

	return;
}

#endif