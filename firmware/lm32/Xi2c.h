#ifndef __XI2C_H
#define __XI2C_H

#define XI2C_SCL 0x01
#define XI2C_SDAOE	0x02
#define XI2C_SDAOUT	0x04

#define XI2C_SDAIN	0x01

int Xi2c_init(void);
void Xi2c_delay(void);
unsigned int Xi2c_read_bit(void);
void Xi2c_write_bit(unsigned int bit);
void Xi2c_start_cond(void);
void Xi2c_stop_cond(void);
unsigned int Xi2c_write(unsigned char byte);
unsigned char Xi2c_read(int ack);

#endif /* __XI2C_H */
