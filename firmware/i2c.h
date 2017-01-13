#ifndef __I2C_H
#define __I2C_H

#define I2C_SCL 0x01
#define I2C_SDAOE	0x02
#define I2C_SDAOUT	0x04

#define I2C_SDAIN	0x01

#define I2C_READ	0x01
#define I2C_WRITE	0x00

typedef unsigned char (*i2c_w_read_t)(void);
typedef void (*i2c_w_write_t)(unsigned char value);
typedef unsigned char (*i2c_r_read_t)(void);

typedef struct {
	i2c_w_read_t w_read;
	i2c_w_write_t w_write;
	i2c_r_read_t r_read;
	int started;
} I2C;

int i2c_init(I2C *i2c);
void i2c_delay(void);
unsigned int i2c_read_bit(I2C *i2c);
void i2c_write_bit(I2C *i2c, unsigned int bit);
void i2c_start_cond(I2C *i2c);
void i2c_stop_cond(I2C *i2c);
unsigned int i2c_write(I2C *i2c, unsigned char byte);
unsigned char i2c_read(I2C *i2c, int ack);

#endif /* __I2C_H */
