// This file is Copyright (c) 2015 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#ifndef __ETHERBONE_H
#define __ETHERBONE_H

#include "contiki.h"
#include "contiki-net.h"

//#define ETHERBONE_DEBUG

#ifdef ETHERBONE_DEBUG
	#define print_debug(...) printf(__VA_ARGS__)
#else
	#define print_debug(...) {}
#endif

#define ETHERBONE_PORT 1234
#define ETHERBONE_BUFFER_SIZE_RX 1512
#define ETHERBONE_BUFFER_SIZE_TX 1512

#define ETHERBONE_HEADER_LENGTH 12

struct tcp_socket etherbone_socket;
uint8_t etherbone_rx_buf[ETHERBONE_BUFFER_SIZE_RX];
uint8_t etherbone_tx_buf[ETHERBONE_BUFFER_SIZE_TX];

struct etherbone_record {
    union {
        uint32_t write_value;
        uint32_t read_addr;
    };
} __attribute__((packed));

struct etherbone_record_header {
    unsigned int bca: 1;
    unsigned int rca: 1;
    unsigned int rff: 1;
    unsigned int reserved: 1;
    unsigned int cyc: 1;
    unsigned int wca: 1;
    unsigned int wff: 1;
    unsigned int reserved2: 1;
    unsigned char byte_enable;
    unsigned char wcount;
    unsigned char rcount;
    union {
        uint32_t base_write_addr;
        uint32_t base_ret_addr;
    };
} __attribute__((packed));

struct etherbone_packet {
    uint16_t magic;
    unsigned int version: 4;
    unsigned int reserved: 1;
    unsigned int nr: 1;
    unsigned int pr: 1;
    unsigned int pf: 1;
    unsigned int addr_size: 4;
    unsigned int port_size: 4;
    uint32_t padding;

    struct etherbone_record_header record_hdr;
    struct etherbone_record record[];
} __attribute__((packed, aligned(8)));

void etherbone_init(void);
void etherbone_write(unsigned int addr, unsigned int value);
unsigned int etherbone_read(unsigned int addr);
int etherbone_callback(struct tcp_socket *s, void *ptr, const char *rxbuf, int rxlen);
void etherbone_process(struct tcp_socket *s, unsigned char *rxbuf);


#endif
